import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# Configuração da página
st.set_page_config(
    page_title="FitPen - Painel de Acompanhamento",
    page_icon="💉",
    layout="wide"
)

# Conexão com o Supabase usando os secrets do Streamlit
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPA_URL"]
    key = st.secrets["SUPABASE_SECRET"]
    return create_client(url, key)

supabase = init_supabase()

# -------------------------------------------------------------
# DADOS DE PESO
# -------------------------------------------------------------
@st.cache_data(ttl=60)
def carregar_dados_peso():
    res = supabase.table("registros_peso").select("*").order("created_at", desc=False).execute()
    if not res.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(res.data)
    
    # utc=True lida de forma segura com diferentes fusos/formatos
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    
    # Converte para a data formatada local
    df["data_formatada"] = df["created_at"].dt.strftime("%d/%m/%Y %H:%M")
    return df

# -------------------------------------------------------------
# DADOS DE DOSES
# -------------------------------------------------------------
@st.cache_data(ttl=60)
def carregar_dados_doses():
    res = supabase.table("registros_dose").select("*").order("data_aplicacao", desc=False).execute()
    if not res.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(res.data)
    df["data_aplicacao"] = pd.to_datetime(df["data_aplicacao"], utc=True)
    return df

# -------------------------------------------------------------
# DASHBOARD INTERFACE
# -------------------------------------------------------------
st.title("💉 FitPen — Dashboard de Evolução")
st.markdown("Acompanhamento de peso e aplicações de tratamento.")

# Botão de atualizar dados
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

df_peso = carregar_dados_peso()
df_dose = carregar_dados_doses()

# --- MÉTRICAS DE DESTAQUE ---
col1, col2, col3, col4 = st.columns(4)

if not df_peso.empty:
    peso_atual = df_peso.iloc[-1]["peso"]
    peso_inicial = df_peso.iloc[0]["peso"]
    diferenca = round(peso_atual - peso_inicial, 2)
    
    col1.metric("Peso Atual", f"{peso_atual} kg", f"{diferenca} kg")
    col2.metric("Peso Inicial", f"{peso_inicial} kg")
else:
    col1.metric("Peso Atual", "Sem dados")

if not df_dose.empty:
    total_doses = len(df_dose)
    ultima_dose = df_dose.iloc[-1]["data_aplicacao"].strftime("%d/%m/%Y")
    col3.metric("Total de Aplicações", f"{total_doses}")
    col4.metric("Última Aplicação", ultima_dose)

st.markdown("---")

# --- GRÁFICOS ---
tab1, tab2 = st.tabs(["📉 Evolução do Peso", "💉 Histórico de Doses"])

with tab1:
    st.subheader("Evolução do Peso ao Longo do Tempo")
    if not df_peso.empty:
        fig_peso = px.line(
            df_peso, 
            x="created_at", 
            y="peso",
            markers=True,
            title="Variação de Peso (kg)",
            labels={"created_at": "Data", "peso": "Peso (kg)"}
        )
        fig_peso.update_traces(line_color="#2E86C1", line_width=3, marker_size=8)
        st.plotly_chart(fig_peso, use_container_width=True)
        
        with st.expander("Ver Tabela de Registros de Peso"):
            st.dataframe(df_peso[["data_formatada", "peso"]].rename(columns={"data_formatada": "Data", "peso": "Peso (kg)"}), use_container_width=True)
    else:
        st.info("Nenhum registro de peso encontrado no banco de dados.")

with tab2:
    st.subheader("Aplicações Registradas")
    if not df_dose.empty:
        fig_dose = px.bar(
            df_dose, 
            x="data_aplicacao", 
            y="cliques",
            text="cliques",
            title="Doses Aplicadas (em Cliques)",
            labels={"data_aplicacao": "Data da Aplicação", "cliques": "Cliques"}
        )
        fig_dose.update_traces(marker_color="#27AE60")
        st.plotly_chart(fig_dose, use_container_width=True)
        
        with st.expander("Ver Tabela Detalhada de Doses"):
            st.dataframe(
                df_dose[["data_aplicacao", "cliques", "dose_mg"]].rename(
                    columns={"data_aplicacao": "Data", "cliques": "Cliques", "dose_mg": "Dose (mg)"}
                ), 
                use_container_width=True
            )
    else:
        st.info("Nenhuma aplicação de medicação registrada ainda.")