import asyncio
import os
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# Add your allowed Telegram user_id(s) here:
ALLOWED_USERS = [350174070]  # <-- change to your own Telegram user_id

def is_authorized(user_id):
    return user_id in ALLOWED_USERS

def today_str():
    return datetime.date.today().isoformat()

# ---- Progress phase logic ----

PHASES = [
    {'name': 'adaptation', 'limit': 5, 'msg': "Adaptation: Stick to basics. Build your routine."},
    {'name': 'discipline', 'limit': 14, 'msg': "Discipline Mode: Add daily reflection. Routine builds faith."},
    {'name': 'tactical',   'limit': 24, 'msg': "Tactical Mode: Weekly simulation, reflect on actions!"},
    {'name': 'mastery',    'limit': 9999, 'msg': "Mastery: No excuses, only results. You are the standard!"}
]

user_data = {}

def init_user(user_id):
    return {
        'checklist_done': False,
        'report_done': False,
        'journal': [],
        'last_simulation': None,
        'faith_streak': 0,
        'phase': 'adaptation',
        'phase_start_date': today_str(),
        'days_in_phase': 0
    }

def phase_idx(phase_name):
    for i, p in enumerate(PHASES):
        if p['name'] == phase_name:
            return i
    return 0

def check_phase_upgrade(user_id):
    u = user_data[user_id]
    current_phase = u['phase']
    idx = phase_idx(current_phase)
    limit = PHASES[idx]['limit']
    if u['faith_streak'] >= limit:
        if idx + 1 < len(PHASES):
            new_phase = PHASES[idx+1]['name']
            u['phase'] = new_phase
            u['phase_start_date'] = today_str()
            u['days_in_phase'] = 0
            return new_phase
    return None

def reset_to_adaptation(user_id):
    u = user_data[user_id]
    u['phase'] = 'adaptation'
    u['phase_start_date'] = today_str()
    u['days_in_phase'] = 0
    u['faith_streak'] = 0

# ---- COMMANDS ----

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = init_user(user_id)
    await message.reply(
        "Harry Protocol activated. Unbreakable discipline. Faith in the process brings victory. Use /help for protocol."
    )

@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    await message.reply(
        "/start – Activate protocol\n"
        "/status – Discipline dashboard\n"
        "/checklist – Mark your morning checklist\n"
        "/report – Submit evening report\n"
        "/shadow_mode – Enter silent mode\n"
        "/journal – Your transformation log\n"
        "/phase – View your current phase\n"
        "/simulate – Crisis scenario\n"
        "/reset – Restart progress"
    )

@dp.message_handler(commands=['status'])
async def status_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply("⛔ Access denied.")
        return
    u = user_data.get(user_id, init_user(user_id))
    checklist = '✅' if u.get('checklist_done') else '❌'
    report = '✅' if u.get('report_done') else '❌'
    faith = u.get('faith_streak', 0)
    msg = (
        f"📊 Discipline Status ({today_str()}):\n"
        f"- Morning checklist: {checklist}\n"
        f"- Evening report: {report}\n"
        f"- Faith streak: {faith} days\n"
        f"- Phase: {u['phase'].upper()} ({u['days_in_phase']} days)\n"
        f"- Journal entries: {len(u.get('journal', []))}"
    )
    if not u.get('checklist_done') or not u.get('report_done'):
        msg += "\n\n⚠️ Discipline gap detected! Remember: 'Faith in the process brings victory.'"
    await message.reply(msg)

@dp.message_handler(commands=['phase'])
async def phase_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply("⛔ Access denied.")
        return
    u = user_data[user_id]
    await message.reply(
        f"Your current phase: {u['phase'].upper()}\n"
        f"Days in this phase: {u['days_in_phase']}\n"
        f"Faith streak: {u['faith_streak']}\n"
        f"{PHASES[phase_idx(u['phase'])]['msg']}"
    )

@dp.message_handler(commands=['checklist'])
async def checklist_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply("⛔ Access denied.")
        return
    if user_id not in user_data:
        user_data[user_id] = init_user(user_id)
    u = user_data[user_id]
    u['checklist_done'] = True
    u.setdefault('journal', []).append(f"{today_str()} #checklist completed")
    await message.reply(
        f"☑️ Morning checklist done. {PHASES[phase_idx(u['phase'])]['msg']}\nFaith in the process brings victory."
    )

@dp.message_handler(commands=['report'])
async def report_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply("⛔ Access denied.")
        return
    if user_id not in user_data:
        user_data[user_id] = init_user(user_id)
    u = user_data[user_id]
    u['report_done'] = True
    u.setdefault('journal', []).append(f"{today_str()} #evening_report submitted")
    u['faith_streak'] += 1
    u['days_in_phase'] += 1
    upgraded = check_phase_upgrade(user_id)
    if upgraded:
        await message.reply(
            f"🔥 Level Up: You have reached a new phase: {upgraded.upper()}!\n{PHASES[phase_idx(upgraded)]['msg']}"
        )
    else:
        await message.reply(
            f"📓 Evening report accepted. Another day. {PHASES[phase_idx(u['phase'])]['msg']}\nFaith in the process brings victory."
        )

@dp.message_handler(commands=['journal'])
async def journal_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply("⛔ Access denied.")
        return
    u = user_data[user_id]
    journal = u.get('journal', [])
    if not journal:
        await message.reply("🗒 Transformation journal is empty.")
    else:
        last_entries = journal[-5:] if len(journal) > 5 else journal
        msg = "🗒 Last journal entries:\n" + "\n".join(f"- {e}" for e in last_entries)
        await message.reply(msg)

@dp.message_handler(commands=['reset'])
async def reset_cmd(message: types.Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply("⛔ Access denied.")
        return
    user_data[user_id] = init_user(user_id)
    await message.reply("🔄 Protocol reset. Start clean. Faith in the process brings victory.")

# ---- Strict reset on discipline failure ----

async def morning_check():
    for user_id in user_data:
        if not is_authorized(user_id): continue
        u = user_data[user_id]
        if not u.get('checklist_done', False):
            await bot.send_message(
                user_id,
                "🚨 You missed your morning checklist! Protocol reset. Start again.\nFaith in the process brings victory."
            )
            u.setdefault('journal', []).append(f"{today_str()} #discipline_breach (morning)")
            reset_to_adaptation(user_id)

async def evening_check():
    for user_id in user_data:
        if not is_authorized(user_id): continue
        u = user_data[user_id]
        if not u.get('report_done', False):
            await bot.send_message(
                user_id,
                "🚨 Evening report missing! Protocol reset. Start again.\nFaith in the process brings victory."
            )
            u.setdefault('journal', []).append(f"{today_str()} #discipline_breach (evening)")
            reset_to_adaptation(user_id)

# ---- Automated morning/evening routines ----

async def send_morning_message():
    for user_id in user_data:
        if not is_authorized(user_id): continue
        u = user_data[user_id]
        await bot.send_message(
            user_id,
            f"🕶 Morning protocol ({u['phase'].upper()}):\n- Cold shower\n- Physical warm-up\n- 2 min silence\n- Stoic quote\nFaith in the process brings victory."
        )
        u['checklist_done'] = False

async def send_evening_message():
    for user_id in user_data:
        if not is_authorized(user_id): continue
        u = user_data[user_id]
        await bot.send_message(
            user_id,
            f"📓 Evening protocol ({u['phase'].upper()}):\n- Review day\n- Submit /report\n- Meditation\nFaith in the process brings victory."
        )
        u['report_done'] = False

# ---- Scheduler setup ----

async def on_startup(_):
    scheduler.add_job(send_morning_message, 'cron', hour=6, minute=0)
    scheduler.add_job(morning_check, 'cron', hour=9, minute=0)
    scheduler.add_job(send_evening_message, 'cron', hour=21, minute=0)
    scheduler.add_job(evening_check, 'cron', hour=22, minute=0)
    scheduler.start()

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
