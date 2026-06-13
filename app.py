import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(layout="wide", page_title="Finanças Meire e Junior")

st.title("💰 Finanças Meire e Junior")

# Interface simples para verificares que o app está a rodar
st.subheader("Bem-vindo de volta ao sistema base!")
st.write("O sistema está online e funcional.")

# Exemplo de como podes ter os teus dados visualmente
data = {
    "Data": [datetime.now().strftime("%Y-%m-%d")],
    "Descrição": ["Sistema reiniciado"],
    "Tipo": ["Receita"],
    "Valor": [0.0],
    "Categoria": ["Outros"]
}

df_teste = pd.DataFrame(data)
st.dataframe(df_teste, use_container_width=True)

st.info("O sistema está limpo e a funcionar. Agora podes construir os teus lançamentos a partir daqui!")
