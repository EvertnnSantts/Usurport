import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import numpy as np
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuração da página Streamlit
st.set_page_config(
    page_title="Usuport - Estradas na Bahia",
    page_icon="🚗",
    layout="wide"
)

# Título da aplicação
st.title("Usuport - Estradas na Bahia")

# Diretório onde os arquivos CSV das BRs estão armazenados
CAMINHO_PLANILHAS = "planilhas_por_br"

try:
    # Verificar se o diretório existe
    if not os.path.exists(CAMINHO_PLANILHAS):
        st.error(f"O diretório {CAMINHO_PLANILHAS} não foi encontrado.")
        st.stop()

    # Obter a lista de BRs disponíveis
    brs_disponiveis = [arquivo.replace(".csv", "") for arquivo in os.listdir(CAMINHO_PLANILHAS) if arquivo.endswith(".csv")]

    if not brs_disponiveis:
        st.error("Nenhuma BR encontrada no diretório de planilhas.")
        st.stop()

    # Barra lateral para seleção da BR
    with st.sidebar:
        br_selecionada = st.selectbox("Selecione a BR", sorted(brs_disponiveis))
        st.info("Visualização da cobertura da BR")

    def calcular_distancia(lat1, lon1, lat2, lon2):
        R = 6371  # Raio da Terra em km
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

    def contar_acidentes_no_raio(centro_lat, centro_lon, todos_pontos, raio_km):
        contador = 0
        for ponto in todos_pontos:
            dist = calcular_distancia(centro_lat, centro_lon, ponto[0], ponto[1])
            if dist <= raio_km:
                contador += 1
        return contador

    def definir_cor_circulo(num_acidentes):
        if num_acidentes < 50:
            return 'blue'
        elif num_acidentes < 80:
            return 'yellow'
        elif num_acidentes < 120:
            return 'orange'
        else:
            return 'red'

    @st.cache_data
    def carregar_dados(br):
        try:
            caminho_arquivo = os.path.join(CAMINHO_PLANILHAS, f"{br}.csv")
            if not os.path.exists(caminho_arquivo):
                st.error(f"Arquivo não encontrado: {caminho_arquivo}")
                return None

            df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8')
            df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
            df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

            # Validar coordenadas
            df = df[
                (df['latitude'].between(-33.75, 5.27)) &  # Limites do Brasil
                (df['longitude'].between(-73.99, -34.73))
            ]
            df = df.dropna(subset=['latitude', 'longitude'])

            if df.empty:
                st.warning("Não foram encontradas coordenadas válidas no arquivo.")
                return None

            return df

        except Exception as e:
            st.error(f"Erro ao carregar os dados: {str(e)}")
            return None

    df = carregar_dados(br_selecionada)

    if df is not None and not df.empty:
        # Criar o mapa
        mapa = folium.Map(
            location=[df['latitude'].mean(), df['longitude'].mean()],
            zoom_start=8,
            tiles='OpenStreetMap'
        )

        # Ordenar pontos por latitude/longitude
        pontos = df[['latitude', 'longitude']].values
        distancia_minima = 20  # Distância mínima entre centros dos círculos (20km)
        pontos_selecionados = []

        # Selecionar o primeiro ponto
        pontos_selecionados.append(pontos[0])

        # Encontrar pontos adequadamente espaçados
        for ponto in pontos:
            # Verificar se o ponto está longe o suficiente de todos os pontos já selecionados
            pode_adicionar = True
            for ponto_selecionado in pontos_selecionados:
                dist = calcular_distancia(
                    ponto[0], ponto[1],
                    ponto_selecionado[0], ponto_selecionado[1]
                )
                if dist < distancia_minima:
                    pode_adicionar = False
                    break

            if pode_adicionar:
                pontos_selecionados.append(ponto)

        # Adicionar círculos de cobertura
        estatisticas_areas = []
        for i, ponto in enumerate(pontos_selecionados):
            # Contar acidentes no raio de 10km
            num_acidentes = contar_acidentes_no_raio(ponto[0], ponto[1], pontos, 10)
            cor = definir_cor_circulo(num_acidentes)

            # Armazenar estatísticas
            estatisticas_areas.append({
                'area': i+1,
                'acidentes': num_acidentes,
                'cor': cor
            })

            folium.Circle(
                location=[ponto[0], ponto[1]],
                radius=10000,  # 10km em metros
                color=cor,
                fill=True,
                fillColor=cor,
                fillOpacity=0.2,
                weight=2,
                popup=f"Área de cobertura {i+1}<br>"
                      f"Raio: 10km<br>"
                      f"BR: {br_selecionada}<br>"
                      f"Acidentes na área: {num_acidentes}"
            ).add_to(mapa)

        # Exibir o mapa e informações
        col1, col2 = st.columns([3, 1])

        with col1:
            st_folium(mapa, width=800, height=600)

        with col2:
            st.write("### Informações")
            st.write(f"BR selecionada: {br_selecionada}")
            st.write(f"Quantidade de áreas de cobertura: {len(pontos_selecionados)}")
            st.write("Distância entre centros: 20km")
            st.write("Raio de cada área: 10km")
            st.write("---")
            st.write("### Legenda")
            st.markdown("🟣 Rosa: Menos de 50 acidentes")
            st.markdown("🟡 Amarelo: 80 acidentes")
            st.markdown("🟠 Laranja: 120 acidentes")
            st.markdown("🔴 Vermelho: mais de 120 acidentes")
            st.write("---")
            st.write(f"Última atualização: "
                    f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    else:
        st.warning("Não há dados disponíveis para esta BR.")

except Exception as e:
    st.error(f"Ocorreu um erro inesperado: {str(e)}")
    st.error("Por favor, verifique se o diretório e os arquivos estão corretos.")

# Botão para limpar cache
if st.button("Limpar Cache"):
    st.cache_data.clear()
    st.rerun()
def coletar_detalhes_acidentes(centro_lat, centro_lon, df, raio_km):
    detalhes = []
    for _, acidente in df.iterrows():
        dist = calcular_distancia(centro_lat, centro_lon,
                                acidente['latitude'], acidente['longitude'])
        if dist <= raio_km:
            detalhes.append({
                'vitimas': acidente['vitimas'] if 'vitimas' in acidente else 'N/A',
                'veiculos': acidente['veiculos'] if 'veiculos' in acidente else 'N/A',
                'horario': acidente['horario'] if 'horario' in acidente else 'N/A',
                'clima': acidente['clima'] if 'clima' in acidente else 'N/A',
                'data': acidente['data'] if 'data' in acidente else 'N/A'
            })
    return detalhes

# Modificar a parte onde criamos os círculos
for i, ponto in enumerate(pontos_selecionados):
    # Contar acidentes no raio de 10km
    num_acidentes = contar_acidentes_no_raio(ponto[0], ponto[1], pontos, 10)
    cor = definir_cor_circulo(num_acidentes)

    # Coletar detalhes dos acidentes nesta área
    detalhes_acidentes = coletar_detalhes_acidentes(ponto[0], ponto[1], df, 10)

    # Criar HTML para o popup com os detalhes
    html_content = f"""
    <div style='width: 300px; max-height: 400px; overflow-y: auto;'>
        <h4>Área de cobertura {i+1}</h4>
        <p><strong>Total de acidentes:</strong> {num_acidentes}</p>
        <p><strong>Raio:</strong> 10km</p>
        <p><strong>BR:</strong> {br_selecionada}</p>
        
        <hr>
        <h5>Detalhes dos Acidentes:</h5>
        <div style='max-height: 300px; overflow-y: auto;'>
    """

    for idx, acidente in enumerate(detalhes_acidentes, 1):
        html_content += f"""
        <div style='margin-bottom: 10px; padding: 5px; background-color: #f8f9fa; border-radius: 5px;'>
            <strong>Acidente {idx}</strong><br>
            Data: {acidente['data']}<br>
            Horário: {acidente['horario']}<br>
            Número de Vítimas: {acidente['vitimas']}<br>
            Veículos Envolvidos: {acidente['veiculos']}<br>
            Condição Climática: {acidente['clima']}
        </div>
        """

    html_content += "</div></div>"

    # Criar popup com iframe para permitir scrolling
    popup = folium.Popup(folium.Html(html_content, script=True), max_width=350)

    # Criar círculo ao mapa (removido o parâmetro tooltip)
    folium.vector_layers.Circle(
        location=[ponto[0], ponto[1]],
        radius=10000,  # 10km em metros
        color=cor,
        fill=True,
        fillColor=cor,
        fillOpacity=0.3,
        weight=2,
        popup=popup
    ).add_to(mapa)