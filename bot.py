import os
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

ALLOWED_USERS = [123456789]  # <-- твій Telegram user_id

def is_authorized(user_id):
    return user_id in ALLOWED_USERS

def today_str():
    return datetime.date.today().isoformat()

# --- Структура прогресу для кожного дня
DAILY_STEPS = [
    {"key": "step1", "label": "✅ Wake up, hydrate, cold shower"},
    {"key": "step2", "label": "🏃 Physical warm-up finished"},
    {"key": "step3", "label": "🧘 2 minutes silence complete"},
    {"key": "step4", "label": "🎯 Set your goal for today"},
    {"key": "step5", "label": "🟩 Ready for the day"}
]

user_progress = {}

# --- Кнопки для кожного кроку
def get_step_keyboard(current_step):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    step_cmd = f"/{current_step}"
    keyboard.add(KeyboardButton(step_cmd))
    return keyboard

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply("⛔ Access denied.")
        return
    user_progress[user_id] = {
        "date": today_str(),
        "steps": {s["key"]: False for s in DAILY_STEPS},
        "goal": "",
        "reflection": ""
    }
    await message.reply(
        "Harry Protocol: Daily routine initialized.\nPress /schedule to see your steps for today.",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message_handler(commands=['schedule'])
async def schedule_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply("⛔ Access denied.")
        return
    text = "🗓 Your steps for today:\n"
    for i, s in enumerate(DAILY_STEPS, 1):
        text += f"{i}. {s['label']}\n"
    first_step = DAILY_STEPS[0]["key"]
    await message.reply(
        text + "\nPress the button for each step when completed.",
        reply_markup=get_step_keyboard(first_step)
    )

# --- Логіка кожного кроку (запис і кнопка далі)
@dp.message_handler(commands=['step1'])
async def step1_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id): return
    user_progress.setdefault(user_id, {}).get("steps", {})["step1"] = True
    await message.reply(
        "Step 1 complete!\nNow do your physical warm-up.",
        reply_markup=get_step_keyboard("step2")
    )

@dp.message_handler(commands=['step2'])
async def step2_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id): return
    user_progress.setdefault(user_id, {}).get("steps", {})["step2"] = True
    await message.reply(
        "Step 2 complete!\nNow sit in silence for 2 minutes.",
        reply_markup=get_step_keyboard("step3")
    )

@dp.message_handler(commands=['step3'])
async def step3_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id): return
    user_progress.setdefault(user_id, {}).get("steps", {})["step3"] = True
    await message.reply(
        "Step 3 complete!\nNow send your goal for today using /goal [your text].",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message_handler(lambda message: message.text and message.text.startswith('/goal'))
async def goal_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id): return
    text = message.text[len('/goal'):].strip()
    user_progress.setdefault(user_id, {})["goal"] = text
    user_progress[user_id]["steps"]["step4"] = True
    await message.reply(
        "Goal for today saved.\nWhen you feel ready, press the button below.",
        reply_markup=get_step_keyboard("step5")
    )

@dp.message_handler(commands=['step5'])
async def step5_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id): return
    user_progress.setdefault(user_id, {}).get("steps", {})["step5"] = True
    await message.reply(
        "✅ All morning steps done!\nStay sharp the whole day.\nIn the evening, send your review using /reflect [text].",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message_handler(lambda message: message.text and message.text.startswith('/reflect'))
async def reflect_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id): return
    text = message.text[len('/reflect'):].strip()
    user_progress.setdefault(user_id, {})["reflection"] = text
    await message.reply(
        "Reflection saved. Protocol complete for today.\nFaith in the process brings victory."
    )

@dp.message_handler(commands=['progress'])
async def progress_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id): return
    data = user_progress.get(user_id, {})
    steps = data.get("steps", {})
    msg = "📊 Today's Progress:\n"
    for i, s in enumerate(DAILY_STEPS, 1):
        done = "✅" if steps.get(s["key"]) else "❌"
        msg += f"{i}. {s['label']} {done}\n"
    msg += f"\nGoal: {data.get('goal','-')}\nReflection: {data.get('reflection','-')}"
    await message.reply(msg)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
