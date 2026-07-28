from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime, date

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL ou SUPABASE_KEY não configurados no .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def salvar_registro_peso(user_id: int, peso: float):
    dados = {"user_id": user_id, "peso": peso}
    return supabase.table("registros_peso").insert([dados]).execute()

def definir_caneta_usuario(user_id: int, nome_caneta: str, mg_por_clique: float = 0.0134, intervalo_dias: int = 7):
    dados = {
        "user_id": user_id,
        "nome_caneta": nome_caneta,
        "mg_por_clique": mg_por_clique,
        "intervalo_dias": intervalo_dias
    }
    return supabase.table("canetas_usuario").upsert(dados, on_conflict="user_id").execute()

def buscar_aplicacoes_pendentes_hoje():
    """Retorna lista de usuarios que precisam aplicar hoje com base no ultimo registro e intervalo."""
    # Busca a ultima dose cadastrada de cada usuario
    # (Em uma consulta simplificada no Supabase)
    canetas = supabase.table("canetas_usuario").select("*").execute().data
    pendentes = []
    
    hoje = date.today()
    
    for c in canetas:
        user_id = c["user_id"]
        intervalo = c.get("intervalo_dias", 7)
        
        # Busca o registro de dose mais recente desse usuario
        res = supabase.table("registros_dose") \
            .select("data_aplicacao") \
            .eq("user_id", user_id) \
            .order("data_aplicacao", desc=True) \
            .limit(1) \
            .execute()
            
        if res.data:
            ultima_data_str = res.data[0]["data_aplicacao"]
            ultima_data = datetime.strptime(ultima_data_str, "%Y-%m-%d").date()
            dias_passados = (hoje - ultima_data).days
            
            # Se bateu o intervalo exato
            if dias_passados == intervalo:
                pendentes.append({
                    "user_id": user_id,
                    "nome_caneta": c["nome_caneta"]
                })
                
    return pendentes

def buscar_caneta_usuario(user_id: int):
    res = supabase.table("canetas_usuario").select("*").eq("user_id", user_id).execute()
    return res.data[0] if res.data else None

def salvar_registro_dose(user_id: int, dose_mg: float, cliques: int = None, data_aplicacao: str = None):
    dados = {
        "user_id": user_id,
        "dose_mg": dose_mg
    }
    if cliques is not None:
        dados["cliques"] = cliques
    if data_aplicacao:
        dados["data_aplicacao"] = data_aplicacao
        
    return supabase.table("registros_dose").insert([dados]).execute()

def buscar_historico_peso(user_id: int, limit: int = 10):
    return (
        supabase.table("registros_peso")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )