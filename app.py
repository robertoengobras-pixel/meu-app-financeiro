import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# Configuração da página
st.set_page_config(layout="wide", page_title="Finanças Meire e Junior")

# Link da tua planilha
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1dusMDuXQC4a2xiotVm5Gm4vKrc22VcBudsgeupB55OY/edit?gid=0#gid=0"

# Listas de apoio
RECEITAS_PERMITIDAS = ["Ordenado Meire", "Ordenado Junior", "VR Meire", "VR Junior", "Cartão Auchan Meire", "Cartão Auchan Junior", "Subs. Férias Meire", "Subs. Férias Junior", "Gasóleo DDN", "Prêmio Junior", "Prêmio Meire", "Empréstimo Aline", "Empréstimo Gabriel"]
METODOS_PAGAMENTO = ["Dinheiro", "Cartão Auchan Meire", "Cartão Auchan Junior", "Vale Refeição Junior", "Vale Refeição Meire"]
CATEGORIAS_DESPESA = ["Habitação/Casa (Renda, EDP, Água, Internet)", "Transportes (Gasóleo, Via Verde, Carro)", "Supermercado/Alimentação", "Família/Filhos (Creche, Explicações, ATL)", "Saúde & Seguros", "Créditos/Financiamentos", "Outros/Diversos"]
CATEGORIAS_RECEITA = ["Salário/Ordenado", "Subsídios & Prémios", "Ajudas de Custo / Gasóleo", "Empréstimos Recebidos", "Cartão de Crédito", "Outras Entradas"]

# Conexão
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)

# Inicialização do estado
if 'banco_dados' not in st.session_state:
    st.session_state.banco_dados = df

# Interface (O resto do código segue a lógica de cálculos que tínhamos)
st.title("💰 Finanças Meire e Junior")

# ... [Aqui entrava o restante da lógica de Interface e botões que tínhamos] ...
