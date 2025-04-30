import streamlit as st
import pandas as pd
import folium
from folium import PolyLine
from streamlit_folium import st_folium
import os

# --- Configuração da página ---
st.set_page_config(page_title="Usuport - BRs da Bahia", layout="wide")

# --- Título ---
st.title("Usuport - BRs da Bahia")

# --- Listar BRs disponíveis ---
planilhas_dir = 'planilhas_por_br'
arquivos = os.listdir(planilhas_dir)
brs_disponiveis = [arquivo.replace('.csv', '') for arquivo in arquivos]

# --- Sidebar para selecionar a BR ---
br_selecionada = st.sidebar.selectbox('Selecione uma BR:', sorted(brs_disponiveis))

# --- Carregar dados da BR selecionada ---
caminho_arquivo = os.path.join(planilhas_dir, f"{br_selecionada}.csv")
df = pd.read_csv(caminho_arquivo, sep=';')

# --- Corrigir KM para número ---
df['km'] = pd.to_numeric(df['km'], errors='coerce')

# --- Limpar dados nulos de coordenadas ---
df = df.dropna(subset=['latitude', 'longitude'])

# --- Mostrar informações na sidebar ---
st.sidebar.markdown("### Informações da BR selecionada:")
qtd_acidentes = df['id'].nunique()
total_mortos = df['mortos'].sum()
st.sidebar.write(f"🛑 Acidentes registrados: {qtd_acidentes}")
st.sidebar.write(f"☠️ Número de fatalidades: {total_mortos}")

# --- Criar o mapa ---
lat_mean = df['latitude'].mean()
lon_mean = df['longitude'].mean()
m = folium.Map(location=[lat_mean, lon_mean], zoom_start=7)

# --- Construir linha organizada ---

# Preparar pontos únicos
pontos = df[['latitude', 'longitude']].drop_duplicates().copy()

# Determinar se ordena por latitude (norte-sul) ou longitude (leste-oeste)
lat_range = pontos['latitude'].max() - pontos['latitude'].min()
lon_range = pontos['longitude'].max() - pontos['longitude'].min()

if lon_range > lat_range:
    # Estrada mais leste-oeste (ordena pela longitude)
    pontos = pontos.sort_values(by='longitude')
else:
    # Estrada mais norte-sul (ordena pela latitude)
    pontos = pontos.sort_values(by='latitude')

# Pegar as coordenadas ordenadas
caminho = pontos[['latitude', 'longitude']].values.tolist()

# Desenhar a linha
PolyLine(locations=caminho, color='blue', weight=3).add_to(m)

# --- Exibir mapa ---
st_data = st_folium(m, width=900, height=600)

# --- Relações abaixo ---
st.subheader(f"Análises da {br_selecionada}")

# Acidentes de ultrapassagem
acidentes_ultrapassagem = df[df['tipo_acidente'].str.contains('Ultrapassagem', na=False, case=False)]
contagem_pista = acidentes_ultrapassagem['tipo_pista'].value_counts()

st.write("### Quantidade de acidentes de ultrapassagem por tipo de pista:")
st.bar_chart(contagem_pista)


"""
import pandas as pd
import os

# Lê o CSV original (usando separador ';', porque parece que é ponto e vírgula)
df = pd.read_csv('estradas_filtradas_ba.csv', sep=';')

# Cria uma pasta para salvar os novos arquivos (opcional)
os.makedirs('planilhas_por_br', exist_ok=True)

# Garante que a coluna da estrada é 'br'
coluna_br = 'br'

# Faz a separação
for br, dados_br in df.groupby(coluna_br):
    if pd.notna(br):  # Só separa se o valor de BR não for vazio
        nome_arquivo = f"BR_{str(br).replace('/', '_').replace(' ', '_')}.csv"
        dados_br.to_csv(os.path.join('planilhas_por_br', nome_arquivo), sep=';', index=False)

print('Separação concluída!')
"""
