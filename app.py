import os
import subprocess
import sys

# Força a instalação caso o Streamlit Cloud ignore o requirements.txt
try:
    import streamlit_gsheets
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit-gsheets"])

import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# Configuração da página para o modo estendido (visual moderno)
st.set_page_config(layout="wide", page_title="Finanças Meire e Junior")

# ==============================================================================
# 📋 LISTAS OFICIAIS CONFIGURADAS PELO ROBERTO
# ==============================================================================
RECEITAS_PERMITIDAS = [
    "Ordenado Meire", "Ordenado Junior", "VR Meire", "VR Junior", 
    "Cartão Auchan Meire", "Cartão Auchan Junior", "Subs. Férias Meire", 
    "Subs. Férias Junior", "Gasóleo DDN", "Prêmio Junior", "Prêmio Meire", 
    "Empréstimo Aline", "Empréstimo Gabriel"
]

METODOS_PAGAMENTO = [
    "Dinheiro", "Cartão Auchan Meire", "Cartão Auchan Junior", 
    "Vale Refeição Junior", "Vale Refeição Meire"
]

CATEGORIAS_DESPESA = [
    "Habitação/Casa (Renda, EDP, Água, Internet)",
    "Transportes (Gasóleo, Via Verde, Carro)",
    "Supermercado/Alimentação",
    "Família/Filhos (Creche, Explicações, ATL)",
    "Saúde & Seguros",
    "Créditos/Financiamentos",
    "Outros/Diversos"
]

CATEGORIAS_RECEITA = [
    "Salário/Ordenado",
    "Subsídios & Prémios",
    "Ajudas de Custo / Gasóleo",
    "Empréstimos Recebidos",
    "Cartão de Crédito",
    "Outras Entradas"
]

# ==============================================================================
# 📋 CONEXÃO REAL COM O GOOGLE SHEETS
# ==============================================================================
if 'banco_dados' not in st.session_state:
    st.session_state.banco_dados = pd.DataFrame(columns=["Data", "Descrição", "Tipo", "Valor", "Método", "Categoria", "Status"])

try:
    conn = st.connection("gsheets", connection_class=GSheetsConnection)
    df_sheets = conn.read(ttl="0d")
    
    if df_sheets.empty or df_sheets.columns.size < 3 or "Data" not in df_sheets.columns:
        st.session_state.banco_dados = pd.DataFrame(columns=["Data", "Descrição", "Tipo", "Valor", "Método", "Categoria", "Status"])
    else:
        df_sheets["Valor"] = pd.to_numeric(df_sheets["Valor"], errors="coerce").fillna(0.0)
        df_sheets["Data"] = df_sheets["Data"].astype(str)
        st.session_state.banco_dados = df_sheets.copy()
except Exception as e:
    pass

# ==============================================================================
# 🧠 REGRAS DE NEGÓCIO (Trava do Cartão Auchan Meire)
# ==============================================================================
def validar_teto_cartao_auchan(novo_valor, subdespesa, mes_alvo):
    df = st.session_state.banco_dados
    
    texto_formatado = str(subdespesa).strip().lower()
    eh_auchan_oficial = (texto_formatado == "supermercado auchan") or (texto_formatado == "gasolineira auchan")
    
    if df.empty:
        gastos_atuais_fora = 0.0
        gastos_atuais_total = 0.0
    else:
        df['Ano_Mes_Tmp'] = pd.to_datetime(df['Data'], errors='coerce').dt.strftime('%Y-%m')
        df_cartao_mes = df[(df['Tipo'] == 'Despesa') & (df['Método'] == 'Cartão Auchan Meire') & (df['Ano_Mes_Tmp'] == mes_alvo)]
        
        if df_cartao_mes.empty:
            gastos_atuais_fora = 0.0
            gastos_atuais_total = 0.0
        else:
            gastos_fora = df_cartao_mes[
                ~(df_cartao_mes['Descrição'].str.lower().str.contains("supermercado auchan")) & 
                ~(df_cartao_mes['Descrição'].str.lower().str.contains("gasolineira auchan"))
            ]
            gastos_atuais_fora = gastos_fora['Valor'].sum()
            gastos_atuais_total = df_cartao_mes['Valor'].sum()

    if gastos_atuais_total + novo_valor > 165.0:
        return False, f"❌ BLOQUEADO: Este lançamento ultrapassa o limite total de 165,00€ do cartão! (Gasto atual: {gastos_atuais_total:.2f}€)"

    if not eh_auchan_oficial:
        if gastos_atuais_fora + float(novo_valor) > 50.0:
            return False, f"❌ BLOQUEADO: Limite de 50,00€ excedido para gastos comuns! Para liberar valores maiores, escreva exatamente 'Supermercado Auchan' ou 'Gasolineira Auchan'. (Gasto fora atual: {gastos_atuais_fora:.2f}€)"

    return True, ""

# ==============================================================================
# ➕ INTERFACE: BARRA LATERAL
# ==============================================================================
st.sidebar.header("➕ Novo Lançamento")

nova_data = st.sidebar.date_input("Data de Vencimento / Entrada", datetime.now())
novo_tipo = st.sidebar.selectbox("Tipo de Fluxo", ["Despesa", "Receita"], key="sb_tipo")

sub_despesa = ""

if novo_tipo == "Receita":
    novo_metodo = st.sidebar.selectbox("Forma de
