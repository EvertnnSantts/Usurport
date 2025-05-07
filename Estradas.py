import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import os

# Título da aplicação
st.title("Usuport - Estradas na Bahia")

# Diretório onde os arquivos CSV das BRs estão armazenados
CAMINHO_PLANILHAS = "planilhas_por_br"

# Obter a lista de BRs disponíveis
brs_disponiveis = [arquivo.replace(".csv", "") for arquivo in os.listdir(CAMINHO_PLANILHAS) if arquivo.endswith(".csv")]

# Barra lateral para seleção da BR
br_selecionada = st.sidebar.selectbox("Selecione a BR", brs_disponiveis)

# Carregar dados da BR selecionada
df = pd.read_csv(f"{CAMINHO_PLANILHAS}/{br_selecionada}.csv", sep=';', encoding='utf-8')

# Garantir que latitude e longitude sejam numéricos
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
df = df.dropna(subset=['latitude', 'longitude'])

# Agrupamento dos pontos para o mapa de calor
heat_data = df[['latitude', 'longitude']].values.tolist()

# Criação do mapa com estilo escuro
mapa = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=7, tiles=None)
folium.TileLayer().add_to(mapa)
HeatMap(heat_data).add_to(mapa)

# Exibir mapa
st_folium(mapa, width=700, height=500)

# Estatísticas na barra lateral
st.sidebar.markdown("---")
st.sidebar.subheader("Estatísticas da BR")

# Número de acidentes únicos
num_acidentes = df['id'].nunique()
st.sidebar.write(f"**Acidentes totais:** {num_acidentes}")

# Número de fatalidades
num_fatalidades = df['mortos'].sum()
st.sidebar.write(f"**Fatalidades:** {num_fatalidades}")

# Acidentes de ultrapassagem em pista simples
ultrapassagem_pista_simples = df[(df['causa_acidente'].str.contains("Ultrapassagem Indevida", case=False, na=False)) & (df['tipo_pista'].str.contains("Simples", case=False, na=False))].shape[0]
st.sidebar.write(f"**Ultrapassagens em pista simples:** {ultrapassagem_pista_simples}")

# Acidentes em dias chuvosos
chuva = df[df['condicao_metereologica'].str.contains("Chuva", case=False, na=False)].shape[0]
st.sidebar.write(f"**Acidentes com chuva:** {chuva}")

# Acidentes noturnos
noturno = df[df['fase_dia'].str.contains("Plena Noite", case=False, na=False)].shape[0]
st.sidebar.write(f"**Acidentes à noite:** {noturno}")
