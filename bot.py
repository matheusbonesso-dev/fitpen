import asyncio
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from fitpen.handlers import dashboard
from handlers import registrar
from database import buscar_aplicacoes_pendentes_hoje

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Função do Job de Lembrete
async def verificar_lembretes_dose():
    pendentes = buscar_aplicacoes_pendentes_hoje()
    for item in pendentes:
        try:
            await bot.send_message(
                chat_id=item["user_id"],
                text=(
                    f"⏰ **Lembrete de Aplicação!**\n\n"
                    f"Hoje é o dia de aplicar sua dose da **{item['nome_caneta']}**.\n"
                    f"Após aplicar, registre usando o comando `/registrar_dose`!"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Erro ao enviar lembrete para {item['user_id']}: {e}")

async def main():
    dp.include_router(registrar.router)
    dp.include_router(dashboard.router)
    # Configura o agendador de tarefas
    scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")
    # Executa a verificação todos os dias às 09:00 da manhã
    scheduler.add_job(verificar_lembretes_dose, "cron", hour=9, minute=0)
    scheduler.start()

    print("Bot rodando com agendador de lembretes ativo...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())