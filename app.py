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
# 🧠 REGRAS DE NEGÓCIO
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
    novo_metodo = st.sidebar.selectbox("Forma de Receita", RECEITAS_PERMITIDAS, key="sb_metodo_rec")
    nova_cat = st.sidebar.selectbox("Categoria da Receita", CATEGORIAS_RECEITA, key="sb_cat_rec")
    nova_desc = novo_metodo 
else:
    novo_metodo = st.sidebar.selectbox("Forma de Pagamento", METODOS_PAGAMENTO, key="sb_metodo_des")
    nova_cat = st.sidebar.selectbox("Categoria da Despesa", CATEGORIAS_DESPESA, key="sb_cat_des")
    
    sub_despesa = st.sidebar.text_input("O que é esta despesa? (Ex: Supermercado Auchan, Gasolineira Auchan, Aluguer)", key="sb_sub_desc")
    
    nome_cat_limpo = nova_cat.split('/')[0].split(' (')[0]
    detalhe = f" - {sub_despesa}" if sub_despesa else ""
    nova_desc = f"{nome_cat_limpo}{detalhe} ({novo_metodo})"
    
novo_valor = st.sidebar.number_input("Valor (€)", min_value=0.0, step=5.0, key="sb_valor")
novas_parcelas = st.sidebar.number_input("Quantidade de Parcelas", min_value=1, max_value=12, value=1, key="sb_parcelas")

if st.sidebar.button("Salvar na Planilha", key="btn_salvar_principal"):
    mes_alvo_cadastro = nova_data.strftime('%Y-%m')
    
    if novo_valor <= 0:
        st.sidebar.warning("⚠️ Insira um valor maior que 0€ antes de salvar!")
    elif novo_tipo == "Despesa" and not sub_despesa:
        st.sidebar.warning("⚠️ Por favor, preencha o campo informando o que é a despesa!")
    else:
        valido = True
        msg_erro = ""
        if novo_tipo == "Despesa" and str(novo_metodo).strip() == "Cartão Auchan Meire":
            valido, msg_erro = validar_teto_cartao_auchan(novo_valor, sub_despesa, mes_alvo_cadastro)
            
        if not valido:
            st.sidebar.error(msg_erro)
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
            
            df_novos = pd.DataFrame(novos_dados)
            st.session_state.banco_dados = pd.concat([st.session_state.banco_dados, df_novos], ignore_index=True)
            
            try:
                planilha_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
                conn.update(spreadsheet=planilha_url, data=st.session_state.banco_dados)
                st.sidebar.success("✅ Guardado com sucesso!")
                st.rerun()
            except Exception as ex:
                st.sidebar.error(f"Erro ao salvar: {ex}")

# ==============================================================================
# 📊 INTERFACE PRINCIPAL
# ==============================================================================
st.title("💰 Finanças Meire e Junior")

# CORREÇÃO AQUI: Garante que o mês atual sempre existe para não quebrar a tela
mes_atual_sistema = datetime.now().strftime('%Y-%m')

if not st.session_state.banco_dados.empty:
    st.session_state.banco_dados['Year_Month_Check'] = pd.to_datetime(st.session_state.banco_dados['Data'], errors='coerce')
    st.session_state.banco_dados['Ano_Mes'] = st.session_state.banco_dados['Year_Month_Check'].dt.strftime('%Y-%m')
    st.session_state.banco_dados = st.session_state.banco_dados.drop(columns=['Year_Month_Check'], errors='ignore')
    meses_disponiveis = sorted(st.session_state.banco_dados['Ano_Mes'].dropna().unique())
    if mes_atual_sistema not in meses_disponiveis:
        meses_disponiveis.append(mes_atual_sistema)
        meses_disponiveis = sorted(meses_disponiveis)
else:
    meses_disponiveis = [mes_atual_sistema]

mes_selecionado = st.selectbox("📅 Escolha o Mês para Analisar", meses_disponiveis, key="filtro_mes")

if not st.session_state.banco_dados.empty:
    df_mes = st.session_state.banco_dados[st.session_state.banco_dados['Ano_Mes'] == mes_selecionado].copy()
else:
    df_mes = pd.DataFrame(columns=["Data", "Descrição", "Tipo", "Valor", "Método", "Categoria", "Status", "Ano_Mes"])

# --- CÁLCULOS MATEMÁTICOS ---
ganhou = df_mes[df_mes['Tipo'] == 'Receita']['Valor'].sum() if not df_mes.empty else 0.0
gastou = df_mes[df_mes['Tipo'] == 'Despesa']['Valor'].sum() if not df_mes.empty else 0.0
a_pagar = df_mes[(df_mes['Tipo'] == 'Despesa') & (df_mes['Status'] == 'Pendente')]['Valor'].sum() if not df_mes.empty else 0.0

def calcular_saldo_recurso(df, nome_receita, nome_pagamento):
    rec = df[(df['Tipo'] == 'Receita') & (df['Status'] == 'Pago') & (df['Método'] == nome_receita)]['Valor'].sum()
    desp = df[(df['Tipo'] == 'Despesa') & (df['Status'] == 'Pago') & (df['Método'] == nome_pagamento)]['Valor'].sum()
    return rec - desp

saldo_vr_meire = calcular_saldo_recurso(df_mes, "VR Meire", "Vale Refeição Meire")
saldo_vr_junior = calcular_saldo_recurso(df_mes, "VR Junior", "Vale Refeição Junior")
saldo_auchan_meire = calcular_saldo_recurso(df_mes, "Cartão Auchan Meire", "Cartão Auchan Meire")
saldo_auchan_junior = calcular_saldo_recurso(df_mes, "Cartão Auchan Junior", "Cartão Auchan Junior")

if not df_mes.empty:
    df_receitas_pagas = df_mes[(df_mes['Tipo'] == 'Receita') & (df_mes['Status'] == 'Pago')]
    receitas_que_geram_dinheiro = df_receitas_pagas[
        ~df_receitas_pagas['Método'].isin(["VR Meire", "VR Junior", "Cartão Auchan Meire", "Cartão Auchan Junior"])
    ]['Valor'].sum()
    despesas_pagas_em_dinheiro = df_mes[(df_mes['Tipo'] == 'Despesa') & (df_mes['Status'] == 'Pago') & (df_mes['Método'] == 'Dinheiro')]['Valor'].sum()
    saldo_dinheiro_carteira = receitas_que_geram_dinheiro - despesas_pagas_em_dinheiro
else:
    saldo_dinheiro_carteira = 0.0
