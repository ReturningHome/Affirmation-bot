import os
import random
import sqlite3
from datetime import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Database setup
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    language TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS affirmations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    text TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reminder_times (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    time TEXT
)
""")

conn.commit()

default_affirmations_en = [
    "I am powerful 💫",
]

default_affirmations_fa = [
    "من قدرتمند هستم 💫",
]


def get_text(user_id, en_text, fa_text):
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    lang = row[0] if row else "en"
    return fa_text if lang == "fa" else en_text


def get_lang(user_id):
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else "en"


def get_affs(user_id):
    cursor.execute("SELECT text FROM affirmations WHERE user_id = ?", (user_id,))
    return [r[0] for r in cursor.fetchall()]


def lang_keyboard():
    keyboard = [["English 🇬🇧", "فارسی 🇮🇷"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, language) VALUES (?, ?)",
        (user_id, "en")
    )
    conn.commit()
    text = get_text(
        user_id,
        "Welcome 🌞\n\nI'll help you stay consistent with your affirmations 💫\n\n"
        "👉 First, choose your language:\n/language\n\n"
        "👉 Then set your reminder time:\n/settime 09:00\n\n"
        "👉 Add your own affirmation:\n/add I am confident",
        "سلام 🌞\n\nمن بهت کمک می‌کنم جملات تاکیدی رو منظم انجام بدی 💫\n\n"
        "👉 اول زبان رو انتخاب کن:\n/language\n\n"
        "👉 بعد زمان یادآور:\n/settime 09:00\n\n"
        "👉 جمله خودتو اضافه کن:\n/add من قوی هستم"
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = get_text(
        user_id,
        "🤖 Here's how to use me:\n\n"
        "/start - Start the bot\n/language - Choose language\n"
        "/add your affirmation - Add your own\n/list - View your affirmations\n"
        "/send - Get one now\n/settime HH:MM - Set reminder\n\nExample:\n/settime 09:00",
        "🤖 راهنمای استفاده:\n\n"
        "/start - شروع ربات\n/language - انتخاب زبان\n"
        "/add متن - افزودن جمله تاکیدی\n/list - دیدن جملات\n"
        "/send - دریافت جمله\n/settime HH:MM - تنظیم یادآور\n\nمثال:\n/settime 09:00"
    )
    await update.message.reply_text(text)


async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Choose your language / زبان خود را انتخاب کنید:",
        reply_markup=lang_keyboard()
    )


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    if "English" in text:
        cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", ("en", user_id))
        conn.commit()
        await update.message.reply_text("Language set to English ✅")
    elif "فارسی" in text:
        cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", ("fa", user_id))
        conn.commit()
        await update.message.reply_text("زبان تنظیم شد ✅")


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text(get_text(user_id,
            "Please write an affirmation after /add",
            "لطفاً بعد از /add یک تأییدیه بنویسید"
        ))
        return
    cursor.execute("INSERT INTO affirmations (user_id, text) VALUES (?, ?)", (user_id, text))
    conn.commit()
    await update.message.reply_text(get_text(user_id, "Added ✨", "اضافه شد ✨"))
    await update.message.reply_text(get_text(user_id,
        "Love it 💫 Want me to remind you daily? Use /settime",
        "عالیه 💫 میخوای یادآوری تنظیم کنم؟ /settime"
    ))


async def list_affirmations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    affs = get_affs(user_id)
    if not affs:
        await update.message.reply_text(get_text(user_id,
            "No affirmations yet.", "هنوز تأییدیه‌ای ندارید."
        ))
    else:
        await update.message.reply_text("\n".join(f"• {a}" for a in affs))


async def send_affirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = get_lang(user_id)
    defaults = default_affirmations_fa if lang == "fa" else default_affirmations_en
    affs = get_affs(user_id) + defaults
    await update.message.reply_text(random.choice(affs))


async def send_daily_affirmation(context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT user_id, language FROM users")
    for user_id, lang in cursor.fetchall():
        try:
            defaults = default_affirmations_fa if lang == "fa" else default_affirmations_en
            affs = get_affs(user_id) + defaults
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🌞 Time for your affirmation:\n\n{random.choice(affs)}"
            )
        except Exception:
            pass


async def send_user_affirmation(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.job.chat_id
    lang = get_lang(user_id)
    defaults = default_affirmations_fa if lang == "fa" else default_affirmations_en
    affs = get_affs(user_id) + defaults
    await context.bot.send_message(
        chat_id=user_id,
        text=f"⏰ Your affirmation:\n\n{random.choice(affs)}"
    )


async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not context.args:
        await update.message.reply_text("Use like this: /settime 09:00")
        return
    t = context.args[0]
    try:
        hour, minute = map(int, t.split(":"))
    except Exception:
        await update.message.reply_text("Invalid format. Use HH:MM")
        return
    cursor.execute("INSERT INTO reminder_times (user_id, time) VALUES (?, ?)", (user_id, t))
    conn.commit()
    context.job_queue.run_daily(
        send_user_affirmation,
        time(hour=hour, minute=minute),
        chat_id=user_id,
        name=str(user_id)
    )
    await update.message.reply_text(f"Reminder set for {t} ⏰")


token = os.environ.get("TELEGRAM_BOT_TOKEN")
if not token:
    raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set")

app = ApplicationBuilder().token(token).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("language", language))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("list", list_affirmations))
app.add_handler(CommandHandler("send", send_affirmation))
app.add_handler(CommandHandler("settime", set_time))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_language))

job_queue = app.job_queue

job_queue.run_daily(send_daily_affirmation, time(hour=9, minute=0))
job_queue.run_daily(send_daily_affirmation, time(hour=14, minute=0))
job_queue.run_daily(send_daily_affirmation, time(hour=20, minute=0))

cursor.execute("SELECT user_id, time FROM reminder_times")
for user_id, t in cursor.fetchall():
    try:
        hour, minute = map(int, t.split(":"))
        job_queue.run_daily(
            send_user_affirmation,
            time(hour=hour, minute=minute),
            chat_id=user_id,
            name=str(user_id)
        )
    except Exception:
        pass

print("Bot is running...")
app.run_polling()