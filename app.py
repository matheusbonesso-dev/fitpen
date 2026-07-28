import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime
from dateutil import parser

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

# Captura o ID do usuário diretamente da URL (?user_id=12345)
query_params = st.query_params
user_id_param = query_params.get("user_id", None)

if user_id_param:
    try:
        user_id_param = int(user_id_param)
    except ValueError:
        user_id_param = None

# -------------------------------------------------------------
# DADOS DE PESO (Aceita o user_id como parâmetro)
# -------------------------------------------------------------
@st.cache_data(ttl=30)
def carregar_dados_peso(user_id: int = None):
    try:
        query = supabase.table("registros_peso").select("*").order("created_at", desc=False)
        if user_id:
            query = query.eq("user_id", user_id)
            
        res = query.execute()
        if not res.data:
            return pd.DataFrame()
        
        df = pd.DataFrame(res.data)
        
        def converter_data(val):
            try:
                dt = parser.parse(str(val))
                return dt.replace(tzinfo=None)
            except Exception:
                return None

        df["created_at"] = df["created_at"].apply(converter_data)
        df = df.dropna(subset=["created_at"])
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["data_formatada"] = df["created_at"].dt.strftime("%d/%m/%Y %H:%M")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados de peso: {e}")
        return pd.DataFrame()

# -------------------------------------------------------------
# DADOS DE DOSES (Aceita o user_id como parâmetro)
# -------------------------------------------------------------
@st.cache_data(ttl=30)
def carregar_dados_doses(user_id: int = None):
    try:
        query = supabase.table("registros_dose").select("*").order("data_aplicacao", desc=False)
        if user_id:
            query = query.eq("user_id", user_id)
            
        res = query.execute()
        if not res.data:
            return pd.DataFrame()
        
        df = pd.DataFrame(res.data)
        
        def converter_data(val):
            try:
                dt = parser.parse(str(val))
                return dt.replace(tzinfo=None)
            except Exception:
                return None

        df["data_aplicacao"] = df["data_aplicacao"].apply(converter_data)
        df = df.dropna(subset=["data_aplicacao"])
        df["data_aplicacao"] = pd.to_datetime(df["data_aplicacao"])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados de doses: {e}")
        return pd.DataFrame()

# -------------------------------------------------------------
# CARREGAMENTO DOS DADOS (Chama uma única vez)
# -------------------------------------------------------------
df_peso = carregar_dados_peso(user_id_param)
df_dose = carregar_dados_doses(user_id_param)

# -------------------------------------------------------------
# DASHBOARD INTERFACE
# -------------------------------------------------------------
st.title("💉 FitPen — Dashboard de Evolução")
st.markdown("Acompanhamento de peso e aplicações de tratamento.")

if not user_id_param:
    st.info("💡 Dica: Acesse o dashboard pelo link enviado no Telegram para ver apenas os seus dados personalizados.")

# Botão de atualizar dados
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

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
else:
    col3.metric("Total de Aplicações", "0")
    col4.metric("Última Aplicação", "-")

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
            st.dataframe(
                df_peso[["data_formatada", "peso"]].rename(columns={"data_formatada": "Data", "peso": "Peso (kg)"}), 
                use_container_width=True
            )
    else:
        st.info("Nenhum registro de peso encontrado para este usuário.")

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
        st.info("Nenhuma aplicação de medicação registrada para este usuário.")