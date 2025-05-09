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
        for i, ponto in enumerate(pontos_selecionados):
            folium.Circle(
                location=[ponto[0], ponto[1]],
                radius=10000,  # 10km em metros
                color='blue',
                fill=True,
                fillColor='blue',
                fillOpacity=0.2,
                weight=2,
                popup=f"Área de cobertura {i+1}<br>Raio: 10km<br>BR: {br_selecionada}"
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
            st.write("Cobertura total aproximada: "
                     f"{len(pontos_selecionados) * 20}km")
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