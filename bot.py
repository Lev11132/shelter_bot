import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

scheduler = AsyncIOScheduler()
user_data = {}

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_data[message.from_user.id] = {'checklist': False, 'report': False}
    await message.reply("Режим 'Гаррі' активовано. Сьогодні ти дієш як фіксер.")

@dp.message_handler(commands=['status'])
async def status_cmd(message: types.Message):
    data = user_data.get(message.from_user.id, {})
    checklist_status = '✅' if data.get('checklist') else '❌'
    report_status = '✅' if data.get('report') else '❌'
    await message.reply(
        f"📊 Статус дня:
"
        f"- Ранкова перевірка: {checklist_status}
"
        f"- Вечірній звіт: {report_status}"
    )

@dp.message_handler(commands=['report'])
async def report_cmd(message: types.Message):
    user_data[message.from_user.id]['report'] = True
    await message.reply("📓 Вечірній звіт прийнято. Завтра — новий день.")

@dp.message_handler(commands=['shadow_mode'])
async def shadow_mode_cmd(message: types.Message):
    await message.reply("🕶 Режим мовчання активовано на 6 годин. Не відповідай на провокації.")

async def send_morning_message():
    for user_id in user_data:
        await bot.send_message(user_id, "🕶 Починай день, Гаррі. Пройди базову перевірку:
- Холодна вода
- Розминка
- Тиша 2 хв
- 1 речення зі стоїків")

async def on_startup(_):
    scheduler.add_job(send_morning_message, 'cron', hour=6, minute=0)
    scheduler.start()

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
