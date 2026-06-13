import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.express as px

# Configuração da página
st.set_page_config(layout="wide", page_title="Finanças Meire e Junior")

# Inicialização de um estado de dados vazio (para o app arrancar sem erros de conexão)
if 'banco_dados' not in st.session_state:
    st.session_state.banco_dados = pd.DataFrame(columns=["Data", "Descrição", "Tipo", "Valor", "Método", "Categoria", "Status"])

st.title("💰 Finanças Meire e Junior")

# Interface Base
st.info("Sistema a correr na versão local. Podes usar este ambiente para gerir os teus lançamentos.")

# Exemplo de entrada
with st.sidebar:
    st.header("➕ Novo Lançamento")
    data = st.date_input("Data")
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor", min_value=0.0)
    if st.button("Adicionar (Local)"):
        novo_dado = pd.DataFrame([{"Data": str(data), "Descrição": desc, "Tipo": "Despesa", "Valor": valor, "Status": "Pendente"}])
        st.session_state.banco_dados = pd.concat([st.session_state.banco_dados, novo_dado], ignore_index=True)
        st.rerun()

st.dataframe(st.session_state.banco_dados, use_container_width=True)
