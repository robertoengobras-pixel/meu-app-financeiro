import streamlit as st
import pandas as pd

st.set_page_config(page_title="Finanças", layout="wide")
st.title("💰 Finanças Meire e Junior")

# Link que publicaste na web
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTpKTYdsvVBipR0UG10hJtnSy2Q-aZDG2EWfoip-jWFZuGt9mQOj8amDhPRLh0Tht0NYkKX7ysSX_Bc/pub?output=csv"

try:
    df = pd.read_csv(CSV_URL)
    st.success("Dados carregados com sucesso!")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"Erro ao carregar: {e}")
    st.write("Verifica se a planilha foi publicada como CSV na Web.")
