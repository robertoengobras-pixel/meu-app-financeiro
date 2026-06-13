import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.express as px

st.set_page_config(layout="wide", page_title="Finanças Meire e Junior")

# Configuração de Acesso (Usando a conta de serviço que criaste)
# NOTA: Garante que o ficheiro JSON está no GitHub como 'google_key.json'
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
KEYFILE = "google_key.json" 

def get_gsheet_client():
    creds = Credentials.from_service_account_file(KEYFILE, scopes=SCOPES)
    return gspread.authorize(creds)

# Carregar dados
try:
    client = get_gsheet_client()
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1dusMDuXQC4a2xiotVm5Gm4vKrc22VcBudsgeupB55OY/edit#gid=0").sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    st.session_state.banco_dados = df
except Exception as e:
    st.error(f"Erro ao carregar do Sheets: {e}")
    if 'banco_dados' not in st.session_state:
        st.session_state.banco_dados = pd.DataFrame(columns=["Data", "Descrição", "Tipo", "Valor", "Método", "Categoria", "Status"])

# ... (O resto do código permanece igual, só alteramos a função de salvar abaixo)

def salvar_no_sheets(df):
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

# No teu botão de salvar, em vez de conn.update, usas:
# salvar_no_sheets(st.session_state.banco_dados)
