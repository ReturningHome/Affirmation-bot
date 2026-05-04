import os
import random
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
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

conn.commit()

default_affirmations_en = [
    "You are capable of amazing things. Believe in yourself today! 🌟",
    "Every day is a fresh start. You have the power to make it great! 🌅",
    "You are enough, just as you are. Keep going! 💪",
    "Your potential is limitless. Dream big and take action! 🚀",
    "You radiate positivity and attract good things into your life! ✨",
    "Challenges make you stronger. You can handle anything! 🔥",
    "You deserve love, happiness, and all the good things in life! 💛",
    "Today is full of possibilities. Make the most of every moment! 🌈",
    "You are growing every day, even when you can't see it! 🌱",
    "You are loved more than you know. You matter deeply! ❤️",
]

default_affirmations_fa = [
    "تو توانایی انجام کارهای شگفت‌انگیز را داری. به خودت ایمان داشته باش! 🌟",
    "هر روز یک شروع تازه است. تو قدرت درخشیدن داری! 🌅",
    "همان‌طور که هستی کافی هستی. ادامه بده! 💪",
    "پتانسیل تو بی‌حد است. بزرگ رویا بپرور و قدم بردار! 🚀",
    "تو انرژی مثبت داری و چیزهای خوب را به سمت خودت جذب می‌کنی! ✨",
    "چالش‌ها تو را قوی‌تر می‌کنند. از پس هر چیزی برمی‌آیی! 🔥",
    "تو لایق عشق، شادی و تمام خوبی‌های زندگی هستی! 💛",
    "امروز پر از فرصت‌های جدید است. از هر لحظه بهره ببر! 🌈",
    "هر روز در حال رشد هستی، حتی وقتی که نمی‌بینی! 🌱",
    "بیشتر از آنچه فکر می‌کنی دوست داشته می‌شوی. وجودت مهم است! ❤️",
]


def get_lang(user_id):
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else "en"


def t(user_id, en, fa):
    return fa if get_lang(user_id) == "fa" else en


def get_affs(user_id):
    cursor.execute("SELECT text FROM affirmations WHERE user_id = ?", (user_id,))
    return [r[0] for r in cursor.fetchall()]


def lang_keyboard():
return ReplyKeyboardMarkup([["English", "Farsi | فارسی"]], resize_keyboard=True, one_time_keyboard=True)

def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id, language) VALUES (?, ?)", (user_id, "en"))
    conn.commit()
    update.message.reply_text(t(user_id,
        "🌸 Welcome!\n\nCommands:\n/language — Choose language\n/affirmation — Get affirmation\n/add your text — Add your own\n/list — View your affirmations\n/settime 08:00 — Set daily reminder\n/cancelreminder — Cancel reminder",
        "🌸 خوش آمدید!\n\nدستورات:\n/language — انتخاب زبان\n/affirmation — دریافت تأییدیه\n/add متن — افزودن تأییدیه\n/list — دیدن تأییدیه‌ها\n/settime 08:00 — تنظیم یادآور\n/cancelreminder — لغو یادآور"
    ))


def language(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Choose your language / زبان خود را انتخاب کنید:",
        reply_markup=lang_keyboard()
    )


def set_language(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text
    if "English" in text:
        cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", ("en", user_id))
        conn.commit()
        update.message.reply_text("✅ Language set to English!")
elif "Farsi" in text or "فارسی" in text:
cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", ("fa", user_id))
        conn.commit()
        update.message.reply_text("✅ زبان فارسی انتخاب شد!")


def affirmation(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    lang = get_lang(user_id)
    defaults = default_affirmations_fa if lang == "fa" else default_affirmations_en
    affs = get_affs(user_id) + defaults
    update.message.reply_text(random.choice(affs))


def add(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = " ".join(context.args)
    if not text:
        update.message.reply_text(t(user_id,
            "Please write after /add. Example: /add I am confident",
            "بعد از /add بنویسید. مثال: /add من قوی هستم"
        ))
        return
    cursor.execute("INSERT INTO affirmations (user_id, text) VALUES (?, ?)", (user_id, text))
    conn.commit()
    update.message.reply_text(t(user_id, "✅ Added!", "✅ اضافه شد!"))


def list_affirmations(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    affs = get_affs(user_id)
    if not affs:
        update.message.reply_text(t(user_id, "No affirmations yet.", "هنوز تأییدیه‌ای ندارید."))
    else:
        update.message.reply_text("\n".join(f"• {a}" for a in affs))


def send_reminder(context: CallbackContext):
    user_id = context.job.context
    lang = get_lang(user_id)
    defaults = default_affirmations_fa if lang == "fa" else default_affirmations_en
    affs = get_affs(user_id) + defaults
    header = "🌸 یادآور روزانه:\n\n" if lang == "fa" else "🌸 Your daily affirmation:\n\n"
    context.bot.send_message(chat_id=user_id, text=header + random.choice(affs))


def set_time(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not context.args:
        update.message.reply_text(t(user_id,
            "Example: /settime 08:00",
            "مثال: /settime 08:00"
        ))
        return
    try:
        hour, minute = map(int, context.args[0].split(":"))
        assert 0 <= hour <= 23 and 0 <= minute <= 59
    except Exception:
        update.message.reply_text(t(user_id, "❌ Invalid format. Use HH:MM", "❌ فرمت اشتباه. مثال: 08:00"))
        return

    current_jobs = context.job_queue.get_jobs_by_name(str(user_id))
    for job in current_jobs:
        job.schedule_removal()

    context.job_queue.run_daily(
        send_reminder,
        time=__import__("datetime").time(hour=hour, minute=minute),
        context=user_id,
        name=str(user_id)
    )
    update.message.reply_text(t(user_id,
        f"✅ Reminder set for {hour:02d}:{minute:02d} every day! 🔔",
        f"✅ یادآور برای ساعت {hour:02d}:{minute:02d} تنظیم شد! 🔔"
    ))


def cancel_reminder(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    jobs = context.job_queue.get_jobs_by_name(str(user_id))
    if jobs:
        for job in jobs:
            job.schedule_removal()
        update.message.reply_text(t(user_id, "✅ Reminder cancelled.", "✅ یادآور لغو شد."))
    else:
        update.message.reply_text(t(user_id, "No active reminder.", "یادآور فعالی ندارید."))


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("language", language))
    dp.add_handler(CommandHandler("affirmation", affirmation))
    dp.add_handler(CommandHandler("add", add))
    dp.add_handler(CommandHandler("list", list_affirmations))
    dp.add_handler(CommandHandler("settime", set_time))
    dp.add_handler(CommandHandler("cancelreminder", cancel_reminder))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, set_language))

    print("Bot is running...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
