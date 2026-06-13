import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.express as px

# Configuração da página para o modo estendido (visual moderno)
st.set_page_config(layout="wide", page_title="Gestão Financeira Familiar")

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
    "Dinheiro", "Cartão de Crédito Meu", "Cartão Auchan Meire", 
    "Cartão Auchan Junior", "Vale Refeição Meu", "Vale Refeição da Esposa"
]

CATEGORIAS = [
    "Habitação/Casa (Renda, EDP, Água, Internet)",
    "Transportes (Gasóleo, Via Verde, Carro)",
    "Supermercado/Alimentação",
    "Família/Filhos (Creche, Explicações, ATL)",
    "Saúde & Seguros",
    "Créditos/Financiamentos",
    "Outros/Diversos"
]

# ==============================================================================
# 📋 BANCO DE DADOS VIRTUAL
# ==============================================================================
if 'banco' not in st.session_state:
    dados_iniciais = [
        {"Data": "2026-06-01", "Descrição": "Entrada Mensal Base", "Tipo": "Receita", "Valor": 1500.0, "Método": "Ordenado Junior", "Categoria": "Outros/Diversos", "Status": "Pago"},
    ]
    st.session_state.banco = pd.DataFrame(dados_iniciais)

# ==============================================================================
# 🧠 REGRAS DE NEGÓCIO
# ==============================================================================
def validar_cartao(descricao, valor, metodo):
    if str(metodo) == "Cartão Auchan Meire":
        desc_lower = str(descricao).lower()
        contem_auchan = "auchan" in desc_lower or "gasóleo" in desc_lower
        if not contem_auchan and valor > 50.0:
            return False
    return True

# ==============================================================================
# ➕ INTERFACE: FORMULÁRIO LATERAL DE CADASTRO
# ==============================================================================
st.sidebar.header("➕ Novo Lançamento")
nova_data = st.sidebar.date_input("Data do Lançamento", datetime.now())
nova_desc = st.sidebar.text_input("Descrição da Conta / Origem")
novo_tipo = st.sidebar.selectbox("Tipo de Fluxo", ["Despesa", "Receita"])

# Exibe a lista correta dependendo se é receita ou despesa
if novo_tipo == "Receita":
    novo_metodo = st.sidebar.selectbox("Forma de Receita", RECEITAS_PERMITIDAS)
else:
    novo_metodo = st.sidebar.selectbox("Forma de Pagamento", METODOS_PAGAMENTO)

nova_cat = st.sidebar.selectbox("Categoria", CATEGORIAS)
novo_valor = st.sidebar.number_input("Valor (€)", min_value=0.0, step=5.0)
novas_parcelas = st.sidebar.number_input("Quantidade de Parcelas", min_value=1, max_value=12, value=1)

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
            
            st.session_state.banco = pd.concat([st.session_state.banco, pd.DataFrame(novos_dados)], ignore_index=True)
            st.sidebar.success("✅ Adicionado com sucesso!")
            st.rerun()

# ==============================================================================
# 📊 INTERFACE PRINCIPAL
# ==============================================================================
st.title("💰 O Nosso Aplicativo de Finanças Familiar")

st.session_state.banco['Ano_Mes'] = pd.to_datetime(st.session_state.banco['Data']).dt.strftime('%Y-%m')
meses_disponiveis = sorted(st.session_state.banco['Ano_Mes'].unique())
mes_selecionado = st.selectbox("📅 Escolha o Mês para Navegar", meses_disponiveis)

df_mes = st.session_state.banco[st.session_state.banco['Ano_Mes'] == mes_selecionado].copy()

# --- CÁLCULO DA REGRA ESPECIAL DO DINHEIRO DO ROBERTO ---
# 1. Pegar todas as receitas PAGAS do mês
df_receitas_pagas = df_mes[(df_mes['Tipo'] == 'Receita') & (df_mes['Status'] == 'Pago')]
# 2. Filtrar excluindo os VRs e os cartões Auchan conforme a regra
receitas_que_geram_dinheiro = df_receitas_pagas[
    ~df_receitas_pagas['Método'].isin(["VR Meire", "VR Junior", "Cartão Auchan Meire", "Cartão Auchan Junior"])
]['Valor'].sum()

# 3. Subtrair as despesas que foram pagas efetivamente com o método "Dinheiro"
despesas_pagas_em_dinheiro = df_mes[(df_mes['Tipo'] == 'Despesa') & (df_mes['Status'] == 'Pago') & (df_mes['Método'] == 'Dinheiro')]['Valor'].sum()

# 4. Saldo Final de Dinheiro Vivo
saldo_dinheiro_carteira = receitas_que_geram_dinheiro - despesas_pagas_em_dinheiro

# Outros Indicadores
ganhou = df_mes[df_mes['Tipo'] == 'Receita']['Valor'].sum()
gastou = df_mes[df_mes['Tipo'] == 'Despesa']['Valor'].sum()
a_pagar = df_mes[(df_mes['Tipo'] == 'Despesa') & (df_mes['Status'] == 'Pendente')]['Valor'].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Ganhei no Mês Inteiro", f"{ganhou:.2f}€")
col2.metric("Gastei no Mês Inteiro", f"{gastou:.2f}€")
col3.error(f"A PAGAR AINDA: {a_pagar:.2f}€")
col4.success(f"💵 DINHEIRO NA CARTEIRA: {saldo_dinheiro_carteira:.2f}€")

st.markdown("---")

# LISTA DE MOVIMENTAÇÕES
st.subheader("📋 Lista de Movimentações de " + mes_selecionado)
if not df_mes.empty:
    for idx, row in df_mes.iterrows():
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
        c1.write(f"🔹 {row['Descrição']} ({row['Categoria']})")
        c2.write(f"**{row['Valor']:.2f}€**")
        c3.write(f"💳 {row['Método']}")
        
        if row['Status'] == 'Pendente':
            c4.write("🔴 *Pendente*")
            if c5.button("Dar Baixa (Pago)", key=f"btn_{idx}"):
                st.session_state.banco.at[idx, 'Status'] = 'Pago'
                st.rerun()
        else:
            c4.write("🟢 **Pago**")
            c5.write("✔️ Concluído")
else:
    st.info("Nenhum registo para este mês.")

st.markdown("---")

# GRÁFICOS
st.subheader("📊 Gráficos de Gastos por Categoria")
df_gastos_mes = df_mes[df_mes['Tipo'] == 'Despesa']
if not df_gastos_mes.empty:
    fig = px.pie(df_gastos_mes, values='Valor', names='Categoria', hole=0.4, title=f"Divisão de Despesas - {mes_selecionado}")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhuma despesa registada neste mês.")
