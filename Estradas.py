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

st.title("Usuport - Estradas na Bahia")

CAMINHO_PLANILHAS = "planilhas_por_br"

try:
    if not os.path.exists(CAMINHO_PLANILHAS):
        st.error(f"O diretório {CAMINHO_PLANILHAS} não foi encontrado.")
        st.stop()

    brs_disponiveis = [arquivo.replace(".csv", "") for arquivo in os.listdir(CAMINHO_PLANILHAS) if arquivo.endswith(".csv")]

    if not brs_disponiveis:
        st.error("Nenhuma BR encontrada no diretório de planilhas.")
        st.stop()

    with st.sidebar:
        br_selecionada = st.selectbox("Selecione a BR", sorted(brs_disponiveis))
        st.info("Visualização da cobertura da BR")

    def calcular_distancia(lat1, lon1, lat2, lon2):
        R = 6371
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

            df = df[
                (df['latitude'].between(-33.75, 5.27)) &
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

        mapa = folium.Map(
            location=[df['latitude'].mean(), df['longitude'].mean()],
            zoom_start=8,
            tiles='OpenStreetMap'
        )

        pontos = df[['latitude', 'longitude']].values
        distancia_minima = 20
        pontos_selecionados = [pontos[0]]

        for ponto in pontos:
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

        for i, ponto in enumerate(pontos_selecionados):
            num_acidentes = contar_acidentes_no_raio(ponto[0], ponto[1], pontos, 10)
            cor = definir_cor_circulo(num_acidentes)

            acidentes_no_raio = df[df.apply(
                lambda row: calcular_distancia(ponto[0], ponto[1], row['latitude'], row['longitude']) <= 10, axis=1
            )]

            if 'id' in acidentes_no_raio.columns:
                acidentes_unicos = acidentes_no_raio.drop_duplicates(subset='id', keep='first')
            else:
                acidentes_unicos = acidentes_no_raio.copy()

            # Métricas resumidas
            total_fatalidades = acidentes_no_raio['mortos'].sum() if 'mortos' in acidentes_no_raio.columns else 'N/A'

            clima_predominante = acidentes_unicos['condicao_metereologica'].mode().iloc[0] if 'condicao_metereologica' in acidentes_unicos.columns and not acidentes_unicos['condicao_metereologica'].mode().empty else 'N/A'
            causa_predominante = acidentes_unicos['tipo_acidente'].mode().iloc[0] if 'tipo_acidente' in acidentes_unicos.columns and not acidentes_unicos['tipo_acidente'].mode().empty else 'N/A'

            html_content = f"""
            <div style='width: 300px; max-height: 400px; overflow-y: auto;'>
                <h4>Área de cobertura {i+1}</h4>
                <p><strong>Total de acidentes:</strong> {num_acidentes}</p>
                <p><strong>Fatalidades:</strong> {total_fatalidades}</p>
                <p><strong>Clima predominante:</strong> {clima_predominante}</p>
                <p><strong>Principal causa:</strong> {causa_predominante}</p>
            </div>
            """
            popup = folium.Popup(folium.Html(html_content, script=True), max_width=350)
            folium.vector_layers.Circle(
                location=[ponto[0], ponto[1]],
                radius=10000,
                color=cor,
                fill=True,
                fillColor=cor,
                fillOpacity=0.3,
                weight=2,
                popup=popup
            ).add_to(mapa)

        col1, col2 = st.columns([3, 1])
        with col1:
            st_folium(mapa, width=800, height=600)

        with st.sidebar:
            st.markdown("---")
            st.subheader("Legenda")
            st.markdown("🔵 Azul: Menos de 50 acidentes")
            st.markdown("🟡 Amarelo: 50 a 79 acidentes")
            st.markdown("🟠 Laranja: 80 a 119 acidentes")
            st.markdown("🔴 Vermelho: 120 ou mais acidentes")
            st.markdown("---")
            st.write(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    else:
        st.warning("Não há dados disponíveis para esta BR.")

except Exception as e:
    st.error(f"Ocorreu um erro inesperado: {str(e)}")
    st.error("Por favor, verifique se o diretório e os arquivos estão corretos.")

if st.button("Limpar Cache"):
    st.cache_data.clear()
    st.rerun()
