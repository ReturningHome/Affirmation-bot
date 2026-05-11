import os
import random
import sqlite3
import datetime
import pytz
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

# ── Database ──────────────────────────────────────────────────────────────────
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    timezone TEXT DEFAULT 'UTC'
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

# ── Default Affirmations ──────────────────────────────────────────────────────
DEFAULT_AFFIRMATIONS = [
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
    "You have survived every hard day so far. You've got this! 🙌",
    "Peace and joy are your natural state. Welcome them in! 🕊️",
    "You are worthy of success and you are working towards it! 🏆",
    "Good things are coming your way. Stay open and grateful! 🎁",
    "Your kindness and strength inspire everyone around you! 🌸",
]

# ── Common timezones helper ───────────────────────────────────────────────────
COMMON_TIMEZONES = {
    "sydney": "Australia/Sydney",
    "melbourne": "Australia/Melbourne",
    "brisbane": "Australia/Brisbane",
    "perth": "Australia/Perth",
    "adelaide": "Australia/Adelaide",
    "new york": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "dubai": "Asia/Dubai",
    "tehran": "Asia/Tehran",
    "tokyo": "Asia/Tokyo",
    "toronto": "America/Toronto",
    "utc": "UTC",
}


def get_user(user_id):
    cursor.execute("SELECT timezone FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, timezone) VALUES (?, ?)", (user_id, "UTC"))
        conn.commit()
        return "UTC"
    return row[0]


def get_affs(user_id):
    cursor.execute("SELECT text FROM affirmations WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    return [r[0] for r in rows]


def random_aff(user_id):
    custom = get_affs(user_id)
    pool = custom + DEFAULT_AFFIRMATIONS
    return random.choice(pool)


# ── /start ────────────────────────────────────────────────────────────────────
def start(update, context):
    user_id = update.message.from_user.id
    get_user(user_id)
    update.message.reply_text(
        "🌸 Welcome to your Daily Affirmation Bot!\n\n"
        "Here's what I can do:\n\n"
        "/affirmation — Get an affirmation now\n"
        "/add I am confident — Add your own affirmation\n"
        "/list — View your affirmations\n"
        "/remove 1 — Remove affirmation by number\n"
        "/settimezone Sydney — Set your timezone\n"
        "/settime 08:00 once — Get affirmation once a day\n"
        "/settime 08:00 twice — Get affirmation twice a day (8am + 8pm)\n"
        "/cancelreminder — Cancel your reminder\n"
        "/help — Show this menu again"
    )


# ── /help ─────────────────────────────────────────────────────────────────────
def help_command(update, context):
    update.message.reply_text(
        "🌸 Commands:\n\n"
        "/affirmation — Get an affirmation now\n"
        "/add I am confident — Add your own affirmation\n"
        "/list — View your affirmations\n"
        "/remove 1 — Remove affirmation by number\n"
        "/settimezone Sydney — Set your timezone\n"
        "/settime 08:00 once — Remind once a day\n"
        "/settime 08:00 twice — Remind twice a day\n"
        "/cancelreminder — Cancel your reminder"
    )


# ── /affirmation ──────────────────────────────────────────────────────────────
def affirmation(update, context):
    user_id = update.message.from_user.id
    update.message.reply_text("🌸 " + random_aff(user_id))


# ── /add ──────────────────────────────────────────────────────────────────────
def add(update, context):
    user_id = update.message.from_user.id
    text = " ".join(context.args).strip()
    if not text:
        update.message.reply_text("Please write your affirmation after /add\nExample: /add I am strong and capable")
        return
    cursor.execute("INSERT INTO affirmations (user_id, text) VALUES (?, ?)", (user_id, text))
    conn.commit()
    update.message.reply_text(f"✅ Added: \"{text}\"\n\nUse /list to see all your affirmations.")


# ── /list ─────────────────────────────────────────────────────────────────────
def list_affirmations(update, context):
    user_id = update.message.from_user.id
    affs = get_affs(user_id)
    if not affs:
        update.message.reply_text("You haven't added any affirmations yet.\nUse /add to add your own!")
    else:
        msg = "📋 Your affirmations:\n\n"
        for i, a in enumerate(affs, 1):
            msg += f"{i}. {a}\n"
        msg += "\nUse /remove 1 to remove by number."
        update.message.reply_text(msg)


# ── /remove ───────────────────────────────────────────────────────────────────
def remove(update, context):
    user_id = update.message.from_user.id
    if not context.args:
        update.message.reply_text("Please provide the number to remove.\nExample: /remove 1")
        return
    try:
        num = int(context.args[0])
        affs = get_affs(user_id)
        if num < 1 or num > len(affs):
            update.message.reply_text(f"Invalid number. You have {len(affs)} affirmation(s).")
            return
        text_to_remove = affs[num - 1]
        cursor.execute("DELETE FROM affirmations WHERE user_id = ? AND text = ? LIMIT 1", (user_id, text_to_remove))
        conn.commit()
        update.message.reply_text(f"✅ Removed: \"{text_to_remove}\"")
    except Exception:
        update.message.reply_text("Please provide a valid number. Example: /remove 1")


# ── /settimezone ──────────────────────────────────────────────────────────────
def set_timezone(update, context):
    user_id = update.message.from_user.id
    if not context.args:
        update.message.reply_text(
            "Please provide your city or timezone.\n\n"
            "Examples:\n"
            "/settimezone Sydney\n"
            "/settimezone Melbourne\n"
            "/settimezone London\n"
            "/settimezone New York\n"
            "/settimezone Dubai\n"
            "/settimezone Tehran\n"
            "/settimezone Tokyo\n"
            "/settimezone UTC"
        )
        return

    tz_input = " ".join(context.args).lower().strip()

    # Check common names first
    tz_name = COMMON_TIMEZONES.get(tz_input)

    # Try direct pytz lookup
    if not tz_name:
        try:
            pytz.timezone(" ".join(context.args))
            tz_name = " ".join(context.args)
        except Exception:
            pass

    if not tz_name:
        update.message.reply_text(
            f"❌ Could not find timezone for \"{' '.join(context.args)}\".\n\n"
            "Try common cities like:\n"
            "/settimezone Sydney\n"
            "/settimezone London\n"
            "/settimezone New York\n"
            "/settimezone Dubai\n"
            "/settimezone Tehran"
        )
        return

    cursor.execute("UPDATE users SET timezone = ? WHERE user_id = ?", (tz_name, user_id))
    conn.commit()

    # Show current time in their timezone
    tz = pytz.timezone(tz_name)
    now = datetime.datetime.now(tz).strftime("%I:%M %p")
    update.message.reply_text(
        f"✅ Timezone set to {tz_name}!\n"
        f"Current time there: {now}\n\n"
        f"Now use /settime 08:00 once or /settime 08:00 twice to set your reminder!"
    )


# ── /settime ──────────────────────────────────────────────────────────────────
def set_time(update, context):
    user_id = update.message.from_user.id
    tz_name = get_user(user_id)

    if len(context.args) < 2:
        update.message.reply_text(
            "Please provide time and frequency.\n\n"
            "Examples:\n"
            "/settime 08:00 once — Once a day at 8am\n"
            "/settime 08:00 twice — Twice a day at 8am and 8pm\n\n"
            "Make sure to set your timezone first with /settimezone"
        )
        return

    try:
        hour, minute = map(int, context.args[0].split(":"))
        assert 0 <= hour <= 23 and 0 <= minute <= 59
    except Exception:
        update.message.reply_text("❌ Invalid time format. Use HH:MM\nExample: /settime 08:00 once")
        return

    frequency = context.args[1].lower()
    if frequency not in ["once", "twice"]:
        update.message.reply_text("❌ Please use 'once' or 'twice'.\nExample: /settime 08:00 once")
        return

    # Remove existing jobs
    for job in context.job_queue.get_jobs_by_name(str(user_id)):
        job.schedule_removal()
    for job in context.job_queue.get_jobs_by_name(f"{user_id}_2"):
        job.schedule_removal()

    # Convert user local time to UTC
    tz = pytz.timezone(tz_name)
    local_dt = datetime.datetime.now(tz).replace(hour=hour, minute=minute, second=0, microsecond=0)
    utc_dt = local_dt.astimezone(pytz.utc)
    utc_hour = utc_dt.hour
    utc_minute = utc_dt.minute

    # Schedule first reminder
    context.job_queue.run_daily(
        send_reminder,
        time=datetime.time(hour=utc_hour, minute=utc_minute),
        context=user_id,
        name=str(user_id)
    )

    msg = f"✅ Reminder set for {hour:02d}:{minute:02d} every day ({tz_name})! 🔔"

    if frequency == "twice":
        # Second reminder 12 hours later
        evening_hour = (hour + 12) % 24
        local_dt2 = datetime.datetime.now(tz).replace(hour=evening_hour, minute=minute, second=0, microsecond=0)
        utc_dt2 = local_dt2.astimezone(pytz.utc)

        context.job_queue.run_daily(
            send_reminder,
            time=datetime.time(hour=utc_dt2.hour, minute=utc_dt2.minute),
            context=user_id,
            name=f"{user_id}_2"
        )
        msg = (
            f"✅ Reminders set for {hour:02d}:{minute:02d} and "
            f"{evening_hour:02d}:{minute:02d} every day ({tz_name})! 🔔"
        )

    update.message.reply_text(msg)


# ── /cancelreminder ───────────────────────────────────────────────────────────
def cancel_reminder(update, context):
    user_id = update.message.from_user.id
    jobs = (
        context.job_queue.get_jobs_by_name(str(user_id)) +
        context.job_queue.get_jobs_by_name(f"{user_id}_2")
    )
    if jobs:
        for job in jobs:
            job.schedule_removal()
        update.message.reply_text("✅ Your reminder(s) have been cancelled.")
    else:
        update.message.reply_text("You don't have any active reminders.")


# ── Reminder callback ─────────────────────────────────────────────────────────
def send_reminder(context):
    user_id = context.job.context
    context.bot.send_message(
        chat_id=user_id,
        text="🌸 Your daily affirmation:\n\n" + random_aff(user_id)
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("affirmation", affirmation))
    dp.add_handler(CommandHandler("add", add))
    dp.add_handler(CommandHandler("list", list_affirmations))
    dp.add_handler(CommandHandler("remove", remove))
    dp.add_handler(CommandHandler("settimezone", set_timezone))
    dp.add_handler(CommandHandler("settime", set_time))
    dp.add_handler(CommandHandler("cancelreminder", cancel_reminder))

    print("Bot is running...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
