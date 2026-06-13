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
    "Cartão Auchan Junior", "Cartão Auchan Meire", "Subs. Férias Meire", 
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
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Lê a planilha atual do Google Sheets
    df_sheets = conn.read(ttl="0d")
    
    # Se a planilha estiver vazia ou sem colunas corretas, reconstrói a estrutura
    if df_sheets.empty or "Data" not in df_sheets.columns:
        st.session_state.banco_dados = pd.DataFrame(columns=["Data", "Descrição", "Tipo", "Valor", "Método", "Categoria", "Status"])
    else:
        # Garante a formatação correta dos dados vindos do Sheets
        df_sheets["Valor"] = pd.to_numeric(df_sheets["Valor"], errors="coerce").fillna(0.0)
        df_sheets["Data"] = df_sheets["Data"].astype(str)
        st.session_state.banco_dados = df_sheets.copy()
except Exception as e:
    st.error(f"⚠️ Erro ao conectar ao Google Sheets. Verifique a Etapa 3. Detalhes: {e}")
    if 'banco_dados' not in st.session_state:
        st.session_state.banco_dados = pd.DataFrame(columns=["Data", "Descrição", "Tipo", "Valor", "Método", "Categoria", "Status"])

# ==============================================================================
# 🧠 REGRAS DE NEGÓCIO (Trava Exata do Cartão Auchan Meire)
# ==============================================================================
def validar_teto_cartao_auchan(novo_valor, subdespesa, mes_alvo):
    df = st.session_state.banco_dados
    
    texto_formatado = str(subdespesa).strip().lower()
    eh_auchan_oficial = (texto_formatado == "supermercado auchan") or (texto_formatado == "gasolineira auchan")
    
    if df.empty:
        gastos_atuais_fora = 0.0
        gastos_atuais_total = 0.0
    else:
        df['Ano_Mes_Tmp'] = pd.to_datetime(df['Data']).dt.strftime('%Y-%m')
        df_cartao_mes = df[(df['Tipo'] == 'Despesa') &
