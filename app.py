import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(layout="wide", page_title="Finanças Meire e Junior")

# Link da tua planilha publicada como CSV (Aquele que termina em ...pub?output=csv)
# Se não tiveres o link, vai a Ficheiro > Partilhar > Publicar na Web > CSV > Publicar
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTpKTYdsvVBipR0UG10hJtnSy2Q-aZDG2EWfoip-jWFZuGt9mQOj8amDhPRLh0Tht0NYkKX7ysSX_Bc/pub?output=csv"

st.title("💰 Finanças Meire e Junior")

try:
    # Lê a planilha como um ficheiro CSV simples (o Google não bloqueia isto)
    df = pd.read_csv(URL)
    
    # Mostra os dados
    st.dataframe(df, use_container_width=True)
    
    # Métricas rápidas
    total_receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
    total_despesas = df[df['Tipo'] == 'Despesa']['Valor'].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("Receitas Totais", f"{total_receitas:.2f}€")
    col2.metric("Despesas Totais", f"{total_despesas:.2f}€")
    
except Exception as e:
    st.error("Erro ao carregar dados. Verifica se publicaste a planilha como CSV.")
    st.write(e)
