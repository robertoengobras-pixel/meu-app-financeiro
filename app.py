import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(layout="wide")

URL = "https://docs.google.com/spreadsheets/d/1dusMDuXQC4a2xiotVm5Gm4vKrc22VcBudsgeupB55OY/edit?gid=0#gid=0"

# Conectar
conn = st.connection("gsheets", type=GSheetsConnection)

# Carregar dados
try:
    df = conn.read(spreadsheet=URL, ttl=0)
    st.session_state.df = df
except:
    st.session_state.df = pd.DataFrame(columns=["Data", "Descrição", "Tipo", "Valor", "Método", "Categoria", "Status"])

st.title("Finanças Meire e Junior")

# Simples formulário de teste para ver se salva
with st.sidebar:
    st.header("Novo Lançamento")
    data = st.date_input("Data")
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor")
    if st.button("Salvar"):
        novo_dado = pd.DataFrame([{"Data": str(data), "Descrição": desc, "Tipo": "Despesa", "Valor": valor, "Método": "Dinheiro", "Categoria": "Outros", "Status": "Pendente"}])
        df_atualizado = pd.concat([st.session_state.df, novo_dado], ignore_index=True)
        # Tenta salvar
        try:
            conn.update(spreadsheet=URL, data=df_atualizado)
            st.success("Salvo!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

st.dataframe(st.session_state.df)
