import streamlit as st
import pandas as pd
import unicodedata
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

# Título
st.title("🚦 Mapa de Acidentes nas BRs da Bahia")
st.markdown("Este mapa interativo mostra os acidentes ocorridos nas rodovias federais da Bahia com base nos dados fornecidos pelo Detran-BA.")

# Sidebar
st.sidebar.header("Filtros")

@st.cache_data
def carregar_dados(path):
    df = pd.read_csv(path, encoding="latin1", sep=";", on_bad_lines="skip")
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .map(lambda x: unicodedata.normalize('NFKD', x).encode('ASCII', 'ignore').decode('utf-8'))
    )
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["data_inversa"] = pd.to_datetime(df["data_inversa"], errors="coerce")
    df["ano"] = df["data_inversa"].dt.year
    df["mes"] = df["data_inversa"].dt.month_name()
    df["uid"] = df.index.astype(str)
    return df.dropna(subset=["latitude", "longitude"]).sample(frac=1).reset_index(drop=True)

# Carrega o CSV
df = carregar_dados("estradas_filtradas_ba.csv")

# Filtros
anos = sorted(df["ano"].dropna().unique())
ano_selecionado = st.sidebar.multiselect("Ano", anos, default=anos)

municipios = sorted(df["municipio"].dropna().unique())
municipios_selecionados = st.sidebar.multiselect("Município", municipios)

filtros = (df["ano"].isin(ano_selecionado)) if ano_selecionado else (df["ano"] > 0)
if municipios_selecionados:
    filtros &= df["municipio"].isin(municipios_selecionados)

df_filtrado = df[filtros].copy()

# Limitar para performance
if len(df_filtrado) > 5000:
    df_filtrado = df_filtrado.sample(5000)

# Tipo de visualização
tipo_visualizacao = st.sidebar.radio(
    "Tipo de visualização no mapa",
    ["Marcadores", "Cluster", "Densidade (HeatMap)"]
)

# Estilo do mapa
tile_selecionado = st.sidebar.selectbox(
    "Tipo de Mapa Base",
    options=["OpenStreetMap", "Stamen Terrain", "Stamen Toner", "CartoDB Positron", "CartoDB Dark_Matter"],
    index=0
)

tiles = {
    "OpenStreetMap": "OpenStreetMap",
    "Stamen Terrain": "Stamen Terrain",
    "Stamen Toner": "Stamen Toner",
    "CartoDB Positron": "CartoDB Positron",
    "CartoDB Dark_Matter": "CartoDB Dark_Matter"
}

# Cria o mapa base
mapa = folium.Map(
    location=[-12.97, -38.50],
    zoom_start=6,
    control_scale=True,
    tiles=tiles[tile_selecionado]
)

# Só adiciona se tiver dados filtrados
if not df_filtrado.empty:
    if tipo_visualizacao == "Marcadores":
        for _, row in df_filtrado.iterrows():
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=f"{row['data_inversa'].date()} - {row['municipio']} - {row['tipo_acidente']}",
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(mapa)

    elif tipo_visualizacao == "Cluster":
        marker_cluster = MarkerCluster()
        for _, row in df_filtrado.iterrows():
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=f"{row['data_inversa'].date()} - {row['municipio']} - {row['tipo_acidente']}",
            ).add_to(marker_cluster)
        marker_cluster.add_to(mapa)

    elif tipo_visualizacao == "Densidade (HeatMap)":
        heat_data = df_filtrado[["latitude", "longitude"]].dropna().values.tolist()
        HeatMap(heat_data, radius=8, blur=15).add_to(mapa)

# Mostra o mapa sempre
st_data = st_folium(mapa, use_container_width=True, height=600)

# Expande para ver dados brutos
with st.expander("🔎 Ver dados brutos"):
    st.dataframe(df_filtrado)
