import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Criando as instâncias uma única vez
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Definindo a classe de estado
class Form(StatesGroup):
    aguardando_peso = State()

@dp.message(Command("start"))
async def start_hadler(message: types.Message):
    await message.answer(
        f"Olá, {message.from_user.first_name}! 👋\n\n"
        "Estou pronto para registrar a evolução do peso e as doses do Ozivy.\n"
        "Use comandos como:\n"
        "• `/registrar` para registrar seu peso\n"
        "• `/dose` para registrar a aplicação semanal",
        parse_mode="Markdown"
    )

# Passo 1: Usuário digita /registrar
@dp.message(Command("registrar"))
async def iniciar_peso(message: types.Message, state: FSMContext):
    await state.set_state(Form.aguardando_peso)
    await message.answer(
        "⚖️ **Registro de Peso**\n\n"
        "Por favor, digite apenas o valor do seu peso em kg.\n"
        "Exemplo: `68.5` ou `68,5`",
        parse_mode="Markdown"
    )

# Passo 2: O bot escuta a mensagem seguinte
@dp.message(Form.aguardando_peso)
async def receber_peso(message: types.Message, state: FSMContext):
    texto_recebido = message.text

    try:
        valor_peso = float(texto_recebido.replace(',', '.'))
        print(f"Peso recebido de {message.from_user.first_name}: {valor_peso}")

        # TODO: Salvar o valor_peso no Supabase aqui!

        await message.answer(f"✅ Peso de **{valor_peso} kg** gravado com sucesso!", parse_mode="Markdown")
        await state.clear()

    except ValueError:
        await message.answer("❌ Não consegui entender esse número. Digite apenas o valor exato (ex: 68.5).")

async def main():
    print("Bot rodando...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())