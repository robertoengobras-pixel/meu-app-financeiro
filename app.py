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
    "PETS",
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
# 📋 BANCO DE DADOS (Leitura Direta via CSV)
# ==============================================================================

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1dusMDuXQC4a2xiotVm5Gm4vKrc22VcBudsgeupB55OY/export?format=csv"

if 'banco_dados' not in st.session_state:
    try:
        # Tenta ler o CSV diretamente do Google
        st.session_state.banco_dados = pd.read_csv(URL_PLANILHA)
    except:
        # Se falhar, cria uma tabela vazia para não travar o App
        st.error("Erro ao ler a planilha. Verifica se a planilha está 'Publicada na Web' como CSV.")
        st.session_state.banco_dados = pd.DataFrame(columns=["Data", "Descrição", "Tipo", "Valor", "Método", "Categoria", "Status"])

# ==============================================================================
# 🧠 REGRAS DE NEGÓCIO (Trava Exata do Cartão Auchan Meire)
# ==============================================================================
def validar_teto_cartao_auchan(novo_valor, subdespesa, mes_alvo):
    df = st.session_state.banco_dados
    
    # 1. Verificar se o texto digitado é exatamente uma das duas opções oficiais
    texto_formatado = str(subdespesa).strip().lower()
    eh_auchan_oficial = (texto_formatado == "supermercado auchan") or (texto_formatado == "gasolineira auchan")
    
    if df.empty:
        gastos_atuais_fora = 0.0
        gastos_atuais_total = 0.0
    else:
        df['Ano_Mes_Tmp'] = pd.to_datetime(df['Data']).dt.strftime('%Y-%m')
        df_cartao_mes = df[(df['Tipo'] == 'Despesa') & (df['Método'] == 'Cartão Auchan Meire') & (df['Ano_Mes_Tmp'] == mes_alvo)]
        
        if df_cartao_mes.empty:
            gastos_atuais_fora = 0.0
            gastos_atuais_total = 0.0
        else:
            # Para o histórico, verifica quem NÃO escreveu o texto exato
            gastos_fora = df_cartao_mes[
                ~(df_cartao_mes['Descrição'].str.lower().str.contains("supermercado auchan")) & 
                ~(df_cartao_mes['Descrição'].str.lower().str.contains("gasolineira auchan"))
            ]
            gastos_atuais_fora = gastos_fora['Valor'].sum()
            gastos_atuais_total = df_cartao_mes['Valor'].sum()

    # A. Bloqueio Geral do Limite Total do Cartão (165€)
    if gastos_atuais_total + novo_valor > 165.0:
        return False, f"❌ BLOQUEADO: Este lançamento ultrapassa o limite total de 165,00€ do cartão! (Gasto atual: {gastos_atuais_total:.2f}€)"

    # B. Bloqueio por falta de identificação do local oficial
    if not eh_auchan_oficial:
        if gastos_atuais_fora + novo_valor > 50.0:
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
novas_parcelas = st.sidebar.number_input("Quantidade de Parcelas", min_value=1, max_value=120, value=1, key="sb_parcelas")
tipo_periodo = st.sidebar.selectbox("Periodicidade", ["Mensal", "Trimestral"], key="sb_periodo")

if st.sidebar.button("Salvar na Planilha", key="btn_salvar_principal"):
    mes_alvo_cadastro = nova_data.strftime('%Y-%m')
    
    if novo_valor <= 0:
        st.sidebar.warning("⚠️ Insira um valor maior que 0€ antes de salvar!")
    elif novo_tipo == "Despesa" and not sub_despesa:
        st.sidebar.warning("⚠️ Por favor, preencha o campo informando o que é a despesa!")
    else:
        valido = True
        msg_erro = ""
        # Validação do cartão Auchan (mantém-se igual)
        if novo_tipo == "Despesa" and str(novo_metodo).strip() == "Cartão Auchan Meire":
            valido, msg_erro = validar_teto_cartao_auchan(novo_valor, sub_despesa, mes_alvo_cadastro)
            
        if not valido:
            st.sidebar.error(msg_erro)
        else:
            lista_lancamentos = []
            data_atual = nova_data
            
            # AGORA O LOOP USA A VARIÁVEL QUE DEFINIMOS NA BARRA LATERAL
            for i in range(1, novas_parcelas + 1):
                desc_final = f"{nova_desc} ({i}/{novas_parcelas})" if novas_parcelas > 1 else nova_desc
                lista_lancamentos.append({
                    "Data": data_atual.strftime("%Y-%m-%d"),
                    "Descrição": desc_final,
                    "Tipo": novo_tipo,
                    "Valor": float(novo_valor),
                    "Método": novo_metodo,
                    "Categoria": nova_cat,
                    "Status": "Pendente"
                })
                
                # A lógica agora está segura:
                if tipo_periodo == "Trimestral":
                    data_atual += relativedelta(months=3)
                else:
                    data_atual += relativedelta(months=1)

            # Concatenar
            st.session_state.banco_dados = pd.concat([st.session_state.banco_dados, pd.DataFrame(lista_lancamentos)], ignore_index=True)
            st.sidebar.success("Lançamento adicionado!")
            st.rerun()

            # Criar DataFrame com a lista correta
            df_novos = pd.DataFrame(lista_lancamentos)
            
            # Concatenar com os dados existentes
            st.session_state.banco_dados = pd.concat([st.session_state.banco_dados, df_novos], ignore_index=True)
            st.sidebar.success("Lançamento adicionado à memória! (Exporta o CSV para guardar na Planilha)")
            st.session_state.primeiro_acesso = False
            st.rerun()

# ==============================================================================
# 📊 INTERFACE PRINCIPAL
# ==============================================================================
st.title("💰 Finanças Meire e Junior")

if not st.session_state.banco_dados.empty:
    st.session_state.banco_dados['Ano_Mes'] = pd.to_datetime(st.session_state.banco_dados['Data']).dt.strftime('%Y-%m')
    meses_disponiveis = sorted(st.session_state.banco_dados['Ano_Mes'].unique())
else:
    st.session_state.banco_dados['Ano_Mes'] = pd.Series(dtype='str')
    meses_disponiveis = [datetime.now().strftime('%Y-%m')]

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

# Layout Visual
st.markdown("#### 📊 Balanço Geral do Mês")
top_col1, top_col2 = st.columns(2)
top_col1.metric("🍏 Ganhei no Mês", f"{ganhou:.2f}€")
top_col2.metric("❌ Gasto No Mês", f"{gastou:.2f}€")

st.markdown("##### 🚨 Controle Financeiro Imediato")
mid_col1, mid_col2 = st.columns(2)
mid_col1.error(f"A PAGAR AINDA: {a_pagar:.2f}€")
mid_col2.success(f"💵 DINHEIRO NA CARTEIRA: {saldo_dinheiro_carteira:.2f}€")

st.markdown("##### 💳 Saldos Disponíveis em Cartões / Vales")
bot_col1, bot_col2, bot_col3, bot_col4 = st.columns(4)
bot_col1.metric("🍱 VR Meire", f"{saldo_vr_meire:.2f}€")
bot_col2.metric("🍱 VR Junior", f"{saldo_vr_junior:.2f}€")
bot_col3.metric("🛒 Auchan Meire", f"{saldo_auchan_meire:.2f}€")
bot_col4.metric("🛒 Auchan Junior", f"{saldo_auchan_junior:.2f}€")

st.markdown("---")

# ==============================================================================
# ABAS DE CONTROLE - ESTRUTURA RÍGIDA
# ==============================================================================
aba_mensal, aba_anual = st.tabs(["📅 Controle Mensal", "📊 Resumos Gerais (Anual e Parcelas)"])

with aba_mensal:
    # --- BLOCO DE RECEITAS ---
    st.subheader("🍏 Receitas / Entradas")
    df_rec_mes = df_mes[df_mes['Tipo'] == 'Receita'] if not df_mes.empty else pd.DataFrame()
    if not df_rec_mes.empty:
        for idx, row in df_rec_mes.iterrows():
            dia_entrada = datetime.strptime(str(row['Data']), "%Y-%m-%d").strftime("%d/%m")
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                c1.write(f"**{row['Descrição']}**\n*{row['Categoria']}*")
                c2.write(f"Valor: **{row['Valor']:.2f}€**")
                c3.write(f"📅 Entrada: {dia_entrada}\n💳 {row['Método']}")
                with c4:
                    cc1, cc2 = st.columns(2)
                    if row['Status'] == 'Pendente':
                        if cc1.button("Receber ✅", key=f"pago_rec_{idx}"):
                            st.session_state.banco_dados.at[idx, 'Status'] = 'Pago'
                            st.rerun()
                    else:
                        cc1.write("🟢 Recebido")
                    if cc2.button("Apagar ❌", key=f"del_rec_{idx}"):
                        st.session_state.banco_dados = st.session_state.banco_dados.drop(idx)
                        st.rerun()
    else:
        st.info("Nenhuma receita registada para este mês.")

    st.markdown("---")

   # --- BLOCO DE DESPESAS ---
    st.subheader("🛑 Despesas / Contas a Pagar")
    df_des_mes = df_mes[df_mes['Tipo'] == 'Despesa'] if not df_mes.empty else pd.DataFrame()

    if df_des_mes.empty:
        st.info("Nenhuma despesa registada para este mês.")
    else:
        for idx, row in df_des_mes.iterrows():
            dia_vencimento = datetime.strptime(str(row['Data']), "%Y-%m-%d").strftime("%d/%m")
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                c1.write(f"**{row['Descrição']}**\n*{row['Categoria']}*")
                c2.write(f"Valor: **{row['Valor']:.2f}€**")
                c3.write(f"📅 Vencimento: {dia_vencimento}\n💳 {row['Método']}")
                with c4:
                    cc1, cc2 = st.columns(2)
                    if row['Status'] == 'Pendente':
                        if cc1.button("Dar Baixa ✅", key=f"pago_des_{idx}"):
                            st.session_state.banco_dados.at[idx, 'Status'] = 'Pago'
                            st.rerun()
                    else:
                        cc1.write("🟢 Pago")
                    if cc2.button("Apagar ❌", key=f"del_des_{idx}"):
                        desc_base = row['Descrição'].split(' (')[0]
                        data_referencia = pd.to_datetime(row['Data'])
                        mask_remover = (
                            (st.session_state.banco_dados['Descrição'].str.contains(desc_base)) & 
                            (pd.to_datetime(st.session_state.banco_dados['Data']) >= data_referencia)
                        )
                        st.session_state.banco_dados = st.session_state.banco_dados[~mask_remover]
                        st.rerun()
        
        # O gráfico agora está DENTRO do 'else' das despesas existentes
        st.markdown("---")
        st.subheader("📊 Distribuição de Gastos do Mês")
        fig = px.pie(df_des_mes, values='Valor', names='Categoria', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    # --- BLOCO DE DESPESAS ---
    st.subheader("🛑 Despesas / Contas a Pagar")
    df_des_mes = df_mes[df_mes['Tipo'] == 'Despesa'] if not df_mes.empty else pd.DataFrame()

    if df_des_mes.empty:
        st.info("Nenhuma despesa registada para este mês.")
    else:
        for idx, row in df_des_mes.iterrows():
            dia_vencimento = datetime.strptime(str(row['Data']), "%Y-%m-%d").strftime("%d/%m")
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                c1.write(f"**{row['Descrição']}**\n*{row['Categoria']}*")
                c2.write(f"Valor: **{row['Valor']:.2f}€**")
                c3.write(f"📅 Vencimento: {dia_vencimento}\n💳 {row['Método']}")
                with c4:
                    cc1, cc2 = st.columns(2)
                    if row['Status'] == 'Pendente':
                        if cc1.button("Dar Baixa ✅", key=f"pago_des_{idx}"):
                            st.session_state.banco_dados.at[idx, 'Status'] = 'Pago'
                            st.rerun()
                    else:
                        cc1.write("🟢 Pago")
                    if cc2.button("Apagar ❌", key=f"del_des_{idx}"):
                        desc_base = row['Descrição'].split(' (')[0]
                        data_referencia = pd.to_datetime(row['Data'])
                        mask_remover = (
                            (st.session_state.banco_dados['Descrição'].str.contains(desc_base)) & 
                            (pd.to_datetime(st.session_state.banco_dados['Data']) >= data_referencia)
                        )
                        st.session_state.banco_dados = st.session_state.banco_dados[~mask_remover]
                        st.rerun()

    # --- GRÁFICO (FORA DO IF/ELSE PARA EVITAR ERROS) ---
    if not df_des_mes.empty:
        st.markdown("---")
        st.subheader("📊 Distribuição de Gastos do Mês")
        fig = px.pie(df_des_mes, values='Valor', names='Categoria', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

with aba_anual:
    # --- 1. RESUMO ANUAL (Fluxo) ---
    st.subheader("📅 Resumo Anual (Fluxo Mês a Mês)")
    
    # Limpeza e preparação dos dados
    df_atual = st.session_state.banco_dados.dropna(subset=['Data', 'Valor']).copy()
    df_atual['Ano_Mes'] = pd.to_datetime(df_atual['Data']).dt.strftime('%Y-%m')
    
    if not df_atual.empty:
        resumo_anual = df_atual.groupby(['Ano_Mes', 'Tipo'])['Valor'].sum().unstack().fillna(0)
        if 'Receita' not in resumo_anual.columns: resumo_anual['Receita'] = 0.0
        if 'Despesa' not in resumo_anual.columns: resumo_anual['Despesa'] = 0.0
        
        resumo_anual['Saldo_no_Mês'] = resumo_anual['Receita'] - resumo_anual['Despesa']
        resumo_anual['Saldo_Acumulado'] = resumo_anual['Saldo_no_Mês'].cumsum()
        
        st.dataframe(resumo_anual.style.format("{:.2f}€"), use_container_width=True)
    else:
        st.info("Nenhum dado disponível para o resumo anual.")

    st.markdown("---")

    # --- 2. RESUMO DE PARCELAS ---
    st.subheader("📋 Resumo de Despesas Parceladas")
    df_parceladas = df_atual[df_atual['Descrição'].str.contains(r'\(\d+/\d+\)')].copy()
    
    if not df_parceladas.empty:
        df_parceladas['Nome_Despesa'] = df_parceladas['Descrição'].str.split(' \(').str[0]
        resumo_parcelas = df_parceladas.groupby('Nome_Despesa').agg(
            Valor_Parcela=('Valor', 'first'),
            Total_Parcelas=('Descrição', 'count'),
            Parcelas_Pagas=('Status', lambda x: (x == 'Pago').sum()),
            Parcelas_A_Pagar=('Status', lambda x: (x == 'Pendente').sum()),
            Fim_do_Contrato=('Data', 'max')
        ).reset_index()
        st.dataframe(resumo_parcelas, use_container_width=True)
    else:
        st.info("Não existem despesas parceladas registadas.")

    st.markdown("---")

    # --- 3. GRÁFICO ANUAL ---
    st.subheader("📊 Distribuição Anual de Gastos")
    df_des_anual = df_atual[df_atual['Tipo'] == 'Despesa']
    if not df_des_anual.empty:
        fig = px.pie(df_des_anual, values='Valor', names='Categoria', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados de despesas para o gráfico anual.")
    
# --- FORA DAS ABAS (Botão de download no fim da página) ---
st.markdown("---")
csv = st.session_state.banco_dados.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Descarregar dados atualizados (CSV)",
    data=csv,
    file_name='financas_meire_junior.csv',
    mime='text/csv',
)

        

