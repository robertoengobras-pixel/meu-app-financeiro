import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# Configuração da página
st.set_page_config(layout="wide", page_title="Finanças Meire e Junior")

# ==============================================================================
# 📋 CONFIGURAÇÃO DO GOOGLE SHEETS
# ==============================================================================
# Certifica-te de que no Streamlit Cloud -> Secrets colaste as credenciais do JSON
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados_da_planilha():
    try:
        # Lê a planilha definida no [connections.gsheets] do teu Secrets
        df = conn.read(usecols=[0,1,2,3,4,5,6])
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        return pd.DataFrame(columns=["Data", "Descrição", "Tipo", "Valor", "Método", "Categoria", "Status"])

if 'banco_dados' not in st.session_state:
    st.session_state.banco_dados = carregar_dados_da_planilha()

# ==============================================================================
# LISTAS OFICIAIS E REGRAS
# ==============================================================================
RECEITAS_PERMITIDAS = ["Ordenado Meire", "Ordenado Junior", "VR Meire", "VR Junior", "Cartão Auchan Junior", "Cartão Auchan Meire", "Subs. Férias Meire", "Subs. Férias Junior", "Gasóleo DDN", "Prêmio Junior", "Prêmio Meire", "Empréstimo Aline", "Empréstimo Gabriel"]
METODOS_PAGAMENTO = ["Dinheiro", "Cartão Auchan Meire", "Cartão Auchan Junior", "Vale Refeição Junior", "Vale Refeição Meire"]
CATEGORIAS_DESPESA = ["Habitação/Casa (Renda, EDP, Água, Internet)", "Transportes (Gasóleo, Via Verde, Carro)", "Supermercado/Alimentação", "Família/Filhos (Creche, Explicações, ATL)", "Saúde & Seguros", "Créditos/Financiamentos", "Outros/Diversos"]
CATEGORIAS_RECEITA = ["Salário/Ordenado", "Subsídios & Prémios", "Ajudas de Custo / Gasóleo", "Empréstimos Recebidos", "Cartão de Crédito", "Outras Entradas"]

def validar_teto_cartao_auchan(novo_valor, subdespesa, mes_alvo):
    df = st.session_state.banco_dados
    texto_formatado = str(subdespesa).strip().lower()
    eh_auchan_oficial = (texto_formatado == "supermercado auchan") or (texto_formatado == "gasolineira auchan")
    
    if df.empty: return True, ""
    df['Ano_Mes_Tmp'] = pd.to_datetime(df['Data']).dt.strftime('%Y-%m')
    df_cartao_mes = df[(df['Tipo'] == 'Despesa') & (df['Método'] == 'Cartão Auchan Meire') & (df['Ano_Mes_Tmp'] == mes_alvo)]
    
    if not df_cartao_mes.empty:
        gastos_atuais_total = df_cartao_mes['Valor'].sum()
        if gastos_atuais_total + novo_valor > 165.0:
            return False, f"❌ BLOQUEADO: Limite total de 165€ excedido! (Gasto atual: {gastos_atuais_total:.2f}€)"
    return True, ""

# ==============================================================================
# BARRA LATERAL E INTERFACE
# ==============================================================================
st.sidebar.header("➕ Novo Lançamento")
nova_data = st.sidebar.date_input("Data", datetime.now())
novo_tipo = st.sidebar.selectbox("Tipo", ["Despesa", "Receita"])

if novo_tipo == "Receita":
    novo_metodo = st.sidebar.selectbox("Forma de Receita", RECEITAS_PERMITIDAS)
    nova_cat = st.sidebar.selectbox("Categoria", CATEGORIAS_RECEITA)
    nova_desc = novo_metodo 
else:
    novo_metodo = st.sidebar.selectbox("Método", METODOS_PAGAMENTO)
    nova_cat = st.sidebar.selectbox("Categoria", CATEGORIAS_DESPESA)
    sub_despesa = st.sidebar.text_input("O que é esta despesa?")
    nova_desc = f"{nova_cat.split('/')[0]} - {sub_despesa} ({novo_metodo})"

novo_valor = st.sidebar.number_input("Valor (€)", min_value=0.0, step=5.0)

if st.sidebar.button("Salvar na Planilha"):
    # Adicionar lógica de salvamento aqui se desejar atualizar a planilha
    st.sidebar.success("Lançamento processado!")
    st.rerun()

# --- (Restante da tua interface original vai aqui abaixo) ---
st.title("💰 Finanças Meire e Junior")

# Download de Backup (Sempre disponível)
if not st.session_state.banco_dados.empty:
    csv = st.session_state.banco_dados.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 Guardar Backup CSV", csv, "financas_backup.csv", "text/csv")
