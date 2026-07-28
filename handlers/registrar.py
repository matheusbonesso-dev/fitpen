from datetime import datetime
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from database import (
    salvar_registro_peso, 
    salvar_registro_dose, 
    definir_caneta_usuario, 
    buscar_caneta_usuario
)

router = Router()

# ==========================================
# GRUPOS DE ESTADOS (FSM)
# ==========================================

class RegistroPesoState(StatesGroup):
    aguardando_peso = State()
    
class CanetaState(StatesGroup):
    aguardando_nome = State()
    aguardando_frequencia = State()

class RegistroDoseState(StatesGroup):
    escolhendo_unidade = State()
    aguardando_valor_dose = State()
    aguardando_dia_aplicacao = State()


# ==========================================
# FLUXO 1: REGISTRAR PESO
# ==========================================

@router.message(Command("registrar_peso"))
async def cmd_registrar_peso(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Por favor, digite o seu peso atual em kg (ex: 75.5):")
    await state.set_state(RegistroPesoState.aguardando_peso)

@router.message(RegistroPesoState.aguardando_peso)
async def processa_peso(message: types.Message, state: FSMContext):
    try:
        peso = float(message.text.replace(",", "."))
        salvar_registro_peso(message.from_user.id, peso)
        
        await message.answer(f"✅ Peso de **{peso} kg** registrado com sucesso!", parse_mode="Markdown")
        await state.clear()
    except ValueError:
        await message.answer("⚠️ Por favor, envie um número válido para o peso (ex: 70.5 ou 70).")


# ==========================================
# FLUXO 2: DEFINIR A CANETA DO USUÁRIO
# ==========================================
@router.message(Command("definir_caneta"))
async def cmd_definir_caneta(message: types.Message, state: FSMContext):
    await state.clear()
    
    teclado = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ozivy (EMS)")],
            [KeyboardButton(text="Ozempic 1mg")],
            [KeyboardButton(text="Wegovy")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer("Selecione ou digite o nome da caneta que você está utilizando:", reply_markup=teclado)
    await state.set_state(CanetaState.aguardando_nome)

@router.message(CanetaState.aguardando_nome)
async def processa_nome_caneta(message: types.Message, state: FSMContext):
    await state.update_data(nome_caneta=message.text.strip())
    
    teclado_freq = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1x por semana (7 dias)")],
            [KeyboardButton(text="A cada 3 dias")],
            [KeyboardButton(text="Diariamente (1 dia)")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer("Com qual frequência você precisa aplicar essa medicação?", reply_markup=teclado_freq)
    await state.set_state(CanetaState.aguardando_frequencia)

@router.message(CanetaState.aguardando_frequencia)
async def processa_frequencia_caneta(message: types.Message, state: FSMContext):
    texto = message.text.lower()
    data = await state.get_data()
    nome_caneta = data.get("nome_caneta")
    
    # Define o intervalo em dias
    if "7 dias" in texto or "semana" in texto:
        intervalo = 7
    elif "3 dias" in texto:
        intervalo = 3
    elif "diaria" in texto or "1 dia" in texto:
        intervalo = 1
    else:
        # Se digitou um numero customizado
        try:
            intervalo = int(''.join(filter(str.isdigit, texto)))
        except ValueError:
            intervalo = 7
            
    definir_caneta_usuario(
        user_id=message.from_user.id, 
        nome_caneta=nome_caneta, 
        mg_por_clique=0.0134, 
        intervalo_dias=intervalo
    )
    
    await message.answer(
        f"✅ Caneta **{nome_caneta}** configurada com sucesso!\n"
        f"🔔 Lembramos você a cada **{intervalo} dia(s)**.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()

# ==========================================
# FLUXO 3: REGISTRO DE DOSE (MG OU CLIQUES)
# ==========================================

@router.message(Command("registrar_dose"))
async def cmd_registrar_dose(message: types.Message, state: FSMContext):
    await state.clear()
    
    caneta = buscar_caneta_usuario(message.from_user.id)
    
    if not caneta:
        await message.answer(
            "⚠️ Você ainda não cadastrou qual caneta está usando.\n\n"
            "Use primeiro o comando `/definir_caneta` para cadastrar!",
            parse_mode="Markdown"
        )
        return

    await state.update_data(
        nome_caneta=caneta["nome_caneta"],
        mg_por_clique=caneta["mg_por_clique"]
    )
    
    teclado_opcao = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Em Cliques"), KeyboardButton(text="Em mg (mg)")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        f"Caneta ativa: **{caneta['nome_caneta']}**\n\n"
        "Como deseja informar a dose aplicada hoje?",
        parse_mode="Markdown",
        reply_markup=teclado_opcao
    )
    await state.set_state(RegistroDoseState.escolhendo_unidade)

@router.message(RegistroDoseState.escolhendo_unidade)
async def processa_opcao_unidade(message: types.Message, state: FSMContext):
    texto = message.text.strip().lower()
    
    if "clique" in texto:
        await state.update_data(modo="cliques")
        await message.answer(
            "Informe a quantidade de **cliques** aplicados (ex: 16):", 
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(RegistroDoseState.aguardando_valor_dose)
    elif "mg" in texto:
        await state.update_data(modo="mg")
        await message.answer(
            "Informe a dose aplicada em **mg** (ex: 0.25 ou 0.5):", 
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(RegistroDoseState.aguardando_valor_dose)
    else:
        await message.answer("Por favor, selecione uma das opções do menu: 'Em Cliques' ou 'Em mg (mg)'.")

@router.message(RegistroDoseState.aguardando_valor_dose)
async def processa_valor_dose(message: types.Message, state: FSMContext):
    data = await state.get_data()
    modo = data.get("modo")
    mg_por_clique = data.get("mg_por_clique", 0.0134)

    try:
        valor_digitado = float(message.text.replace(",", "."))
        
        if modo == "cliques":
            cliques = int(valor_digitado)
            dose_mg = round(cliques * mg_por_clique, 2)
        else:
            dose_mg = valor_digitado
            cliques = int(round(dose_mg / mg_por_clique))

        await state.update_data(dose_mg=dose_mg, cliques=cliques)
        
        await message.answer(
            f"Anotado: **{cliques} cliques** (~{dose_mg} mg).\n\n"
            "Agora informe a data da aplicação (ex: DD/MM/AAAA ou 'hoje'):",
            parse_mode="Markdown"
        )
        await state.set_state(RegistroDoseState.aguardando_dia_aplicacao)
        
    except ValueError:
        await message.answer("⚠️ Envie um número válido.")

@router.message(RegistroDoseState.aguardando_dia_aplicacao)
async def processa_dia_aplicacao(message: types.Message, state: FSMContext):
    texto = message.text.strip().lower()
    
    if texto == "hoje":
        data_aplicacao = datetime.now().strftime("%Y-%m-%d")
        data_exibicao = datetime.now().strftime("%d/%m/%Y")
    else:
        try:
            dt = datetime.strptime(texto, "%d/%m/%Y")
            data_aplicacao = dt.strftime("%Y-%m-%d")
            data_exibicao = texto
        except ValueError:
            await message.answer("⚠️ Formato de data inválido. Digite **DD/MM/AAAA** ou **hoje**.")
            return

    data = await state.get_data()
    dose_mg = data.get("dose_mg")
    cliques = data.get("cliques")

    salvar_registro_dose(message.from_user.id, dose_mg=dose_mg, cliques=cliques, data_aplicacao=data_aplicacao)
    
    await message.answer(
        f"✅ **Registro Salvo!**\n"
        f"• Dose: **{cliques} cliques** (~{dose_mg} mg)\n"
        f"• Data: **{data_exibicao}**",
        parse_mode="Markdown"
    )
    await state.clear()