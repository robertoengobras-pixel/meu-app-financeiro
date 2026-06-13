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
# 📋 BANCO DE DADOS PERSISTENTE (Não apaga ao clicar nos botões)
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

if novo_tipo == "Receita":
    novo_metodo = st.sidebar.selectbox("Forma de Receita", RECEITAS_PERMITIDAS)
    nova_cat = st.sidebar.selectbox("Categoria da Receita", CATEGORIAS_RECEITA)
else:
    novo_metodo = st.sidebar.selectbox("Forma de Pagamento", METODOS_PAGAMENTO)
    nova_cat = st.sidebar.selectbox("Categoria da Despesa", CATEGORIAS_DESPESA)

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
            
            # União estável dos dados salvos
            st.session_state.banco_dados = pd.concat([st.session_state.banco_dados, pd.DataFrame(novos_dados)], ignore_index=True)
            st.sidebar.success("✅ Adicionado com sucesso!")
            st.meta_refresh = True
            st.rerun()

# ==============================================================================
# 📊 INTERFACE PRINCIPAL (Abas Dinâmicas)
# ==============================================================================
st.title("💰 Finanças Meire e Junior")

# Mantém a coluna de períodos sempre alinhada
st.session_state.banco_dados['Ano_Mes'] = pd.to_datetime(st.session_state.banco_dados['Data']).dt.strftime('%Y-%m')

# Criar duas abas de navegação no topo do site
aba_mensal, aba_anual = st.tabs(["📅 Controle Mensal", "📊 Resumos Gerais (Anual e Parcelas)"])

# ------------------------------------------------------------------------------
# ABA 1: CONTROLE MENSAL DO ROBERTO
# ------------------------------------------------------------------------------
with aba_mensal:
    meses_disponiveis = sorted(st.session_state.banco_dados['Ano_Mes'].unique())
    mes_selecionado = st.selectbox("Escolha o Mês para Analisar", meses_disponiveis, key="filtro_mes")
    
    df_mes = st.session_state.banco_dados[st.session_state.banco_dados['Ano_Mes'] == mes_selecionado].copy()
    
    # --- CÁLCULO DA REGRA MATEMÁTICA DO DINHEIRO DO ROBERTO ---
    df_receitas_pagas = df_mes[(df_mes['Tipo'] == 'Receita') & (df_mes['Status'] == 'Pago')]
    receitas_que_geram_dinheiro = df_receitas_pagas[
        ~df_receitas_pagas['Método'].isin(["VR Meire", "VR Junior", "Cartão Auchan Meire", "Cartão Auchan Junior"])
    ]['Valor'].sum()
    
    despesas_pagas_em_dinheiro = df_mes[(df_mes['Tipo'] == 'Despesa') & (df_mes['Status'] == 'Pago') & (df_mes['Método'] == 'Dinheiro')]['Valor'].sum()
    saldo_dinheiro_carteira = receitas_que_geram_dinheiro - despesas_pagas_em_dinheiro
    
    ganhou = df_mes[df_mes['Tipo'] == 'Receita']['Valor'].sum()
    gastou = df_mes[df_mes['Tipo'] == 'Despesa']['Valor'].sum()
    a_pagar = df_mes[(df_mes['Tipo'] == 'Despesa') & (df_mes['Status'] == 'Pendente')]['Valor'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ganhei no Mês", f"{ganhou:.2f}€")
    col2.metric("Gasto No Mês", f"{gastou:.2f}€")
    col3.error(f"A PAGAR AINDA: {a_pagar:.2f}€")
    col4.success(f"💵 DINHEIRO NA CARTEIRA: {saldo_dinheiro_carteira:.2f}€")
    
    st.markdown("---")
    
    st.subheader("📋 Lista de Movimentações")
    if not df_mes.empty:
        for idx, row in df_mes.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1.2, 1, 1, 0.8])
            prefixo = "🛑" if row['Tipo'] == "Despesa" else "🍏"
            c1.write(f"{prefixo} {row['Descrição']} *({row['Categoria']})*")
            c2.write(f"**{row['Valor']:.2f}€**")
            c3.write(f"💳 {row['Método']}")
            
            if row['Status'] == 'Pendente':
                c4.write("🔴 *Pendente*")
                if c5.button("Baixa ✅", key=f"pago_{idx}"):
                    st.session_state.banco_dados.at[idx, 'Status'] = 'Pago'
                    st.rerun()
            else:
                c4.write("🟢 **Pago**")
                c5.write("✔️ Concluído")
                
            if c6.button("Apagar ❌", key=f"del_{idx}"):
                st.session_state.banco_dados = st.session_state.banco_dados.drop(idx)
                st.rerun()
    else:
        st.info("Nenhum registo para este mês.")
        
    st.markdown("---")
    st.subheader("📊 Distribuição de Gastos do Mês")
    df_gastos_mes = df_mes[df_mes['Tipo'] == 'Despesa']
    if not df_gastos_mes.empty:
        fig = px.pie(df_gastos_mes, values='Valor', names='Categoria', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma despesa registada neste mês.")

# ------------------------------------------------------------------------------
# ABA 2: RESUMOS ANUAIS E CONTRATOS PARCELADOS
# ------------------------------------------------------------------------------
with aba_anual:
    st.subheader("📅 Resumo Anual (Fluxo Mês a Mês)")
    
    resumo_anual = st.session_state.banco_dados.groupby(['Ano_Mes', 'Tipo'])['Valor'].sum().unstack().fillna(0)
    if 'Receita' not in resumo_anual.columns: resumo_anual['Receita'] = 0.0
    if 'Despesa' not in resumo_anual.columns: resumo_anual['Despesa'] = 0.0
    
    resumo_anual['Saldo_no_Mês'] = resumo_anual['Receita'] - resumo_anual['Despesa']
    resumo_anual['Saldo_Acumulado'] = resumo_anual['Saldo_no_Mês'].cumsum()
    
    st.dataframe(resumo_anual.style.format("{:.2f}€"), use_container_width=True)
    
    st.markdown("---")
    st.subheader("📋 Resumo de Despesas Parceladas")
    
    df_parceladas = st.session_state.banco_dados[st.session_state.banco_dados['Descrição'].str.contains(r'\(\d+/\d+\)')].copy()
    if not df_parceladas.empty:
        df_parceladas['Nome_Despesa'] = df_parceladas['Descrição'].str.split(' \(').str[0]
        hoje = datetime.now()
        
        def calcular_atrasadas(series_status, series_data):
            return sum(1 for s, d in zip(series_status, series_data) if s == 'Pendente' and datetime.strptime(d, "%Y-%m-%d") < hoje)
            
        resumo_parcelas = df_parceladas.groupby('Nome_Despesa').agg(
            Valor_Parcela=('Valor', 'first'),
            Total_Parcelas=('Descrição', 'count'),
            Parcelas_Pagas=('Status', lambda x: (x == 'Pago').sum()),
            Parcelas_Atrasadas=('Status', lambda x: calcular_atrasadas(x, df_parceladas.loc[x.index, 'Data'])),
            Parcelas_A_Pagar=('Status', lambda x: (x == 'Pendente').sum()),
            Fim_do_Contrato=('Data', 'max')
        ).reset_index()
        st.dataframe(resumo_parcelas, use_container_width=True)
    else:
        st.info("Nenhuma conta parcelada ativa no momento.")
        
    st.markdown("---")
    st.subheader("📊 Gráfico Anual por Categorias")
    df_gastos_ano = st.session_state.banco_dados[st.session_state.banco_dados['Tipo'] == 'Despesa']
    if not df_gastos_ano.empty:
        fig_ano = px.bar(df_gastos_ano, x='Ano_Mes', y='Valor', color='Categoria', barmode='stack')
        st.plotly_chart(fig_ano, use_container_width=True)
