import streamlit as st
import pandas as pd
from database import buscar_historico_peso

st.title("📊 Painel do FitPen")

user_id = st.number_input("Digite o User ID do Telegram:", value=0, step=1)

if st.button("Buscar Histórico"):
    res = buscar_historico_peso(user_id)
    if res.data:
        df = pd.DataFrame(res.data)
        st.line_chart(df.set_index("created_at")["peso"])
        st.dataframe(df)
    else:
        st.warning("Nenhum registro encontrado.")