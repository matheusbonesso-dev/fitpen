from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Substitua pela URL real do seu Streamlit App
URL_STREAMLIT = "https://fitpen.streamlit.app"
router = Router()

@router.message(Command("dashboard"))
@router.message(Command("grafico"))
async def cmd_enviar_dashboard(message: types.Message):
    user_id = message.from_user.id
    
    # Gera o link personalizado com o ID do usuário
    link_personalizado = f"{URL_STREAMLIT}/?user_id={user_id}"
    
    # Cria um botão bonitinho Inline no Telegram
    teclado_link = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Abrir Meu Dashboard", url=link_personalizado)]
        ]
    )
    
    await message.answer(
        "📈 **Seu Dashboard Interativo**\n\n"
        "Clique no botão abaixo para visualizar a evolução do seu peso e histórico de doses:",
        parse_mode="Markdown",
        reply_markup=teclado_link
    )