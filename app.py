import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.express as px
import requests
import io

# Configuração da página
st.set_page_config(layout="wide", page_title="Finanças Meire e Junior")

# Link público da Planilha (Formato CSV)
# NOTA: O ID abaixo é o da tua planilha, configurado para exportar como CSV
URL_CSV = "https://docs.google.com/spreadsheets/d/1dusMDuXQC4a2xiotVm5Gm4vKrc22VcBudsgeupB55OY/gviz/tq?tqx=out:csv&sheet=Folha1"

# ==============================================================================
# 📋 CARREGAR DADOS
# ==============================================================================
def carregar_dados():
    try:
        response = requests.get(URL_CSV)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            return df
        else:
            return pd.DataFrame(columns=["Data", "Descrição", "Tipo", "Valor", "Método", "Categoria", "Status"])
    except:
        return pd.DataFrame(columns=["Data", "Descrição", "Tipo", "Valor", "Método", "Categoria", "Status"])

if 'banco_dados' not in st.session_state:
    st.session_state.banco_dados = carregar_dados()

# ==============================================================================
# 📋 LISTAS E CONFIGURAÇÕES
# ==============================================================================
RECEITAS_PERMITIDAS = ["Ordenado Meire", "Ordenado Junior", "VR Meire", "VR Junior", "Cartão Auchan Meire", "Cartão Auchan Junior", "Subs. Férias Meire", "Subs. Férias Junior", "Gasóleo DDN", "Prêmio Junior", "Prêmio Meire", "Empréstimo Aline", "Empréstimo Gabriel"]
METODOS_PAGAMENTO = ["Dinheiro", "Cartão Auchan Meire", "Cartão Auchan Junior", "Vale Refeição Junior", "Vale Refeição Meire"]
CATEGORIAS_DESPESA = ["Habitação/Casa", "Transportes", "Supermercado/Alimentação", "Família/Filhos", "Saúde & Seguros", "Créditos/Financiamentos", "Outros"]
CATEGORIAS_RECEITA = ["Salário/Ordenado", "Subsídios & Prémios", "Ajudas de Custo", "Empréstimos Recebidos", "Outras Entradas"]

# ==============================================================================
# 📊 INTERFACE PRINCIPAL
# ==============================================================================
st.title("💰 Finanças Meire e Junior")

# Filtro de mês
mes_atual = datetime.now().strftime('%Y-%m')
st.session_state.banco_dados['Data'] = pd.to_datetime(st.session_state.banco_dados['Data'], errors='coerce')
st.session_state.banco_dados['Ano_Mes'] = st.session_state.banco_dados['Data'].dt.strftime('%Y-%m')

meses = sorted(st.session_state.banco_dados['Ano_Mes'].dropna().unique())
if mes_atual not in meses: meses.append(mes_atual)
mes_selecionado = st.selectbox("📅 Escolha o Mês:", sorted(meses, reverse=True))

df_mes = st.session_state.banco_dados[st.session_state.banco_dados['Ano_Mes'] == mes_selecionado]

# Exibição básica
st.subheader(f"Resumo de {mes_selecionado}")
col1, col2 = st.columns(2)
col1.metric("Total Entradas", f"{df_mes[df_mes['Tipo'] == 'Receita']['Valor'].sum():.2f}€")
col2.metric("Total Despesas", f"{df_mes[df_mes['Tipo'] == 'Despesa']['Valor'].sum():.2f}€")

st.dataframe(df_mes, use_container_width=True)

st.info("Nota: Esta versão está otimizada para leitura. Para salvar novos dados, garante que a planilha está em modo 'Qualquer pessoa pode editar'.")
