import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Configuração da página para o modo estendido (visual moderno)
st.set_page_config(layout="wide", page_title="Gestão Financeira Familiar")

# ==============================================================================
# 📋 BANCO DE DADOS VIRTUAL (Guarda as informações enquanto o site está aberto)
# ==============================================================================
if 'banco' not in st.session_state:
    dados_iniciais = [
        {"Data": "2026-06-01", "Descrição": "Salário", "Tipo": "Receita", "Valor": 2500.0, "Método": "Dinheiro", "Categoria": "Trabalho", "Status": "Pago"},
        {"Data": "2026-06-01", "Descrição": "Vale Refeição Meio Mês", "Tipo": "Receita", "Valor": 150.0, "Método": "Vale Refeição Meu", "Categoria": "Benefícios", "Status": "Pago"},
        {"Data": "2026-06-05", "Descrição": "Renda/Aluguel", "Tipo": "Despesa", "Valor": 700.0, "Método": "Dinheiro", "Categoria": "Habitação", "Status": "Pendente"},
    ]
    st.session_state.banco = pd.DataFrame(dados_iniciais)

# ==============================================================================
# 🧠 REGRAS DE NEGÓCIO (A segurança do sistema)
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
nova_desc = st.sidebar.text_input("Descrição da Conta / Receita")
novo_tipo = st.sidebar.selectbox("Tipo de Fluxo", ["Despesa", "Receita"])
novo_valor = st.sidebar.number_input("Valor (€)", min_value=0.0, step=5.0)
novo_metodo = st.sidebar.selectbox("Forma de Pagamento", ["Dinheiro", "Cartão de Crédito Meu", "Cartão Auchan Meire", "Vale Refeição Meu", "Vale Refeição da Esposa"])
nova_cat = st.sidebar.selectbox("Categoria", ["Trabalho", "Habitação", "Supermercado", "Transporte", "Educação", "Lazer", "Benefícios", "Outros"])
novas_parcelas = st.sidebar.number_input("Quantidade de Parcelas (Deixa 1 para conta única)", min_value=1, max_value=12, value=1)

if st.sidebar.button("Salvar na Planilha"):
    if nova_desc and novo_valor > 0:
        if not validar_cartao(nova_desc, ... = novo_valor, metodo = novo_metodo):
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
            st.sidebar.success("✅ Lançamento adicionado com sucesso!")
            st.rerun()

# ==============================================================================
# 📊 INTERFACE PRINCIPAL: PAINÉIS, BOTÕES E GRÁFICOS
# ==============================================================================
st.title("💰 O Nosso Aplicativo de Finanças")

# Filtro de meses amigável no topo da página
st.session_state.banco['Ano_Mes'] = pd.to_datetime(st.session_state.banco['Data']).dt.strftime('%Y-%m')
meses_disponiveis = sorted(st.session_state.banco['Ano_Mes'].unique())
mes_selecionado = st.selectbox("📅 Escolha o Mês para Navegar", meses_disponiveis)

df_mes = st.session_state.banco[st.session_state.banco['Ano_Mes'] == mes_selecionado].copy()

# CARDS INDICADORES EM DESTAQUE
ganhou = df_mes[df_mes['Tipo'] == 'Receita']['Valor'].sum()
gastou = df_mes[df_mes['Tipo'] == 'Despesa']['Valor'].sum()
a_pagar = df_mes[(df_mes['Tipo'] == 'Despesa') & (df_mes['Status'] == 'Pendente')]['Valor'].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Faturamento Total do Mês", f"{ganhou:.2f}€")
col2.metric("Gasto Total (Orçamento)", f"{gastou:.2f}€")
col3.error(f"VALOR A PAGAR AINDA: {a_pagar:.2f}€")

st.markdown("---")

# LISTA DE CONTAS COM BOTÃO DE DAR BAIXA INTERATIVO
st.subheader("📋 Lista de Movimentações de " + mes_selecionado)
for idx, row in df_mes.iterrows():
    c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
    c1.write(f"🔹 {row['Descrição']}")
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

st.markdown("---")

# GRÁFICOS POR CATEGORIAS DO MÊS
st.subheader("📊 Gráficos de Gastos por Categoria")
df_gastos_mes = df_mes[df_mes['Tipo'] == 'Despesa']
if not df_gastos_mes.empty:
    import plotly.express as px
    fig = px.pie(df_gastos_mes, values='Valor', names='Categoria', hole=0.4, title=f"Divisão de Despesas - {mes_selecionado}")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhuma despesa registada neste mês.")