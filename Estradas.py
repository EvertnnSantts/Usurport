import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np
import os

# --- Configuração da página ---
st.set_page_config(page_title="Usuport - BRs da Bahia", layout="wide")

# --- Título ---
st.title("Usuport - BRs da Bahia")

# --- Carregar os dados ---
df = pd.read_csv('estradas_filtradas_ba.csv', sep=';')

# --- Corrigir o KM para número ---
df['km'] = pd.to_numeric(df['km'], errors='coerce')

# --- Sidebar para selecionar a BR ---
brs_disponiveis = df['br'].dropna().unique()
br_selecionada = st.sidebar.selectbox('Selecione uma BR:', sorted(brs_disponiveis))

# --- Filtrar dados pela BR selecionada ---
df_filtrado = df[df['br'] == br_selecionada].dropna(subset=['km', 'latitude', 'longitude'])

# --- Ordenar por KM ---
df_filtrado = df_filtrado.sort_values(by='km')

# --- Mostrar informações na sidebar ---
st.sidebar.markdown("### Informações da BR selecionada:")

# Contar acidentes (ID únicos)
qtd_acidentes = df_filtrado['id'].nunique()
st.sidebar.write(f"🛑 Acidentes registrados: {qtd_acidentes}")

# Contar mortos
total_mortos = df_filtrado['mortos'].sum()
st.sidebar.write(f"☠️ Número de mortos: {total_mortos}")

# --- Criar o mapa ---
lat_mean = df_filtrado['latitude'].mean()
lon_mean = df_filtrado['longitude'].mean()
m = folium.Map(location=[lat_mean, lon_mean], zoom_start=7)

# --- Definir os intervalos a cada 10km ---
km_min = int(df_filtrado['km'].min())
km_max = int(df_filtrado['km'].max())
intervalos = np.arange(km_min, km_max + 10, 10)

# --- Criar coluna de grupo 10km ---
df_filtrado['grupo_10km'] = pd.cut(df_filtrado['km'], bins=intervalos, labels=False, include_lowest=True)

# --- Contagem de acidentes por grupo ---
contagem_por_grupo = df_filtrado['grupo_10km'].value_counts().sort_index()
total_acidentes = contagem_por_grupo.sum()
porcentagem_por_grupo = contagem_por_grupo / total_acidentes

# --- Função para definir cor baseado na porcentagem ---
def cor_por_percentual(pct):
    if pct < 0.02:
        return 'green'
    elif pct < 0.05:
        return 'orange'
    else:
        return 'red'

# --- Construir linha da estrada completa ---
for i in range(len(intervalos) - 1):
    km_inicio = intervalos[i]
    km_fim = intervalos[i + 1]

    dados_trecho = df_filtrado[(df_filtrado['km'] >= km_inicio) & (df_filtrado['km'] < km_fim)]

    if not dados_trecho.empty:
        grupo_id = dados_trecho['grupo_10km'].iloc[0]
        cor = cor_por_percentual(porcentagem_por_grupo.get(grupo_id, 0))
        pontos = dados_trecho[['latitude', 'longitude']].values.tolist()
    else:
        pontos = []
        if i > 0:
            antes = df_filtrado[df_filtrado['km'] < km_inicio]
            if not antes.empty:
                ponto_antes = antes.iloc[-1][['latitude', 'longitude']].tolist()
                pontos.append(ponto_antes)

        if i < len(intervalos) - 2:
            depois = df_filtrado[df_filtrado['km'] >= km_fim]
            if not depois.empty:
                ponto_depois = depois.iloc[0][['latitude', 'longitude']].tolist()
                pontos.append(ponto_depois)

        cor = 'gray'

    if len(pontos) >= 2:
        folium.PolyLine(
            pontos,
            color=cor,
            weight=6,
            opacity=0.8
        ).add_to(m)

# --- Adicionar legenda manual ---
legend_html = """
<div style="position: fixed; 
     bottom: 50px; left: 50px; width: 200px; height: 140px; 
     background-color: white; z-index:9999; font-size:14px;
     border:2px solid grey; padding:10px;">
<b>Legenda:</b><br>
<span style='color:green;'>🟢 Poucos acidentes</span><br>
<span style='color:orange;'>🟠 Acidentes moderados</span><br>
<span style='color:red;'>🔴 Muitos acidentes</span><br>
<span style='color:gray;'>⚪ Sem acidentes</span>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# --- Exibir o mapa ---
st_folium(m, width=900, height=600)

# --- Relações abaixo do mapa ---
st.subheader(f"Análises da {br_selecionada}")

# Quantidade de acidentes de ultrapassagem por tipo de pista
acidentes_ultrapassagem = df_filtrado[df_filtrado['tipo_acidente'].str.contains('Ultrapassagem', na=False, case=False)]
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
