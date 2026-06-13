import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.express as px

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
    "Outras Entradas"
]

# ==============================================================================
# 📋 BANCO DE DADOS PERSISTENTE (Garante que os dados não somem)
# ==============================================================================
if 'banco_dados' not in st.session_state:
    dados_iniciais = [
        {"Data": "2026-06-01", "Descrição": "Entrada Mensal Base", "Tipo": "Receita", "Valor": 1500.0, "Método": "Ordenado Junior", "Categoria": "Salário/Ordenado", "Status": "Pago"},
    ]
    st.session_state.banco_dados = pd.DataFrame(dados_iniciais)

# ==============================================================================
# 🧠 REGRAS DE NEGÓCIO
# ==============================================================================
def validar_cartao(descricao, valor, metodo):
    if str(metodo).strip().lower() == "cartão auchan meire":
        desc_lower = str(descricao).lower()
        contem_auchan = "auchan" in desc_lower or "gasóleo" in desc_lower
        if not contem_auchan and valor > 50.0:
            return False
    return True

# ==============================================================================
# ➕ INTERFACE: BARRA LATERAL (Sem st.form para evitar conflitos de recarregamento)
# ==============================================================================
st.sidebar.header("➕ Novo Lançamento")

nova_data = st.sidebar.date_input("Data do Lançamento", datetime.now())
nova_desc = st.sidebar.text_input("Descrição da Conta / Origem")
novo_tipo = st.sidebar.selectbox("Tipo de Fluxo", ["Despesa", "Receita"])

# Troca dinâmica de categorias e métodos em tempo real
if novo_tipo == "Receita":
    novo_metodo = st.sidebar.selectbox("Forma de Receita", RECEITAS_PERMITIDAS)
    nova_cat = st.sidebar.selectbox("Categoria da Receita", CATEGORIAS_RECEITA)
else:
    novo_metodo = st.sidebar.selectbox("Forma de Pagamento", METODOS_PAGAMENTO)
    nova_cat = st.sidebar.selectbox("Categoria da Despesa", CATEGORIAS_DESPESA)
    
novo_valor = st.sidebar.number_input("Valor (€)", min_value=0.0, step=5.0)
novas_parcelas = st.sidebar.number_input("Quantidade de Parcelas", min_value=1, max_value=12, value=1)

# Botão direto e funcional
if st.sidebar.button("Salvar na Planilha"):
    if nova_desc and novo_valor > 0:
        if novo_tipo == "Despesa" and not validar_cartao(nova_desc, novo_valor, novo_metodo):
            st.sidebar.error("❌ BLOQUEADO: O 'Cartão Auchan Meire' não permite gastos acima de 50€ fora do grupo Auchan/Gasóleo!")
        else:
            novos_dados = []
            data_atual = nova_data
            for i in range(1, novas_parcelas + 1):
                desc_final = f"{nova_desc} ({i}/{novas_parcelas})" if novas_parcelas > 1 else nova_desc
                novos_dados.append({
                    "Data": data_atual.strftime("%Y-%m-%d"),
                    "Descrição": desc_final,
                    "Tipo": novo_tipo,
                    "Valor": float(novo_valor),
                    "Método": novo_metodo,
                    "Categoria": nova_cat,
                    "Status": "Pendente"
                })
                data_atual += relativedelta(months=1)
            
            # Adiciona diretamente e força a atualização visual imediata
            st.session_state
