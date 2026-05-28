# =========================================
# REF BOT FULL FIX (STABLE + SAFE + G CURRENCY)
# =========================================

import telebot
from telebot import types
import sqlite3
import threading
import time

TOKEN = "8920387142:AAHtgkQnKvIud3ckKkegk6oPjnjRlmN5umA"
bot = telebot.TeleBot(TOKEN)

ADMINS = [8763987324]

REF_REWARD = 1000
DAILY_REWARD = 250
WITHDRAW_MIN = 10000

CHANNEL = "@k9ntoORIG"

# =========================================
# SQLITE SAFE
# =========================================

db = sqlite3.connect("bot.db", check_same_thread=False)
lock = threading.Lock()

def sql(query, params=(), fetch=False):
    with lock:
        cur = db.cursor()
        cur.execute(query, params)
        data = cur.fetchall() if fetch else None
        db.commit()
        return data

# =========================================
# TABLES
# =========================================

sql("""
CREATE TABLE IF NOT EXISTS users (
user_id INTEGER,
username TEXT,
balance INTEGER,
refs INTEGER,
invited_by INTEGER,
last_bonus INTEGER,
sub_done INTEGER,
chat_done INTEGER
)
""")

sql("""
CREATE TABLE IF NOT EXISTS withdraws (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
skin TEXT,
amount INTEGER,
status TEXT
)
""")

# =========================================
# SAFE HELPERS
# =========================================

def safe(v):
    try:
        return int(v)
    except:
        return 0

def exists(uid):
    return sql("SELECT 1 FROM users WHERE user_id=?", (uid,), fetch=True)

def create(uid, username, ref=None):
    sql("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (uid, username, 0, 0, ref, 0, 0, 0))

def get(uid):
    u = sql("SELECT * FROM users WHERE user_id=?", (uid,), fetch=True)
    return u[0] if u else None

def balance(uid):
    u = get(uid)
    return safe(u[2]) if u else 0

def set_balance(uid, val):
    sql("UPDATE users SET balance=? WHERE user_id=?", (safe(val), uid))

def add(uid, val):
    set_balance(uid, balance(uid) + safe(val))

def add_ref(uid):
    u = get(uid)
    r = safe(u[3]) + 1
    sql("UPDATE users SET refs=? WHERE user_id=?", (r, uid))

def has_ref(uid):
    u = get(uid)
    return u[4] if u else None

# =========================================
# MENU
# =========================================

def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("👤 Профиль", "👥 Рефералы")
    kb.row("🎁 Подарок дня", "📋 Задания")
    kb.row("💸 Вывод", "🏆 Топ")
    return kb

# =========================================
# START + ANTI REF
# =========================================

@bot.message_handler(commands=['start'])
def start(m):

    uid = m.from_user.id
    username = m.from_user.username

    args = m.text.split()
    ref = None

    if len(args) > 1:
        try:
            ref = int(args[1])
        except:
            ref = None

    if ref == uid:
        ref = None

    if not exists(uid):

        create(uid, username, None)

        if ref and exists(ref):

            if not has_ref(uid):

                sql("UPDATE users SET invited_by=? WHERE user_id=?", (ref, uid))

                add(ref, REF_REWARD)
                add_ref(ref)

                bot.send_message(ref, f"🔥 +{REF_REWARD} G за друга")

    bot.send_message(m.chat.id, "🔥 Бот запущен", reply_markup=menu())

# =========================================
# PROFILE
# =========================================

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(m):

    u = get(m.from_user.id)

    if not u:
        return

    bot.send_message(
        m.chat.id,
        f"👤 Профиль\n\n💰 Баланс: {safe(u[2])} G\n👥 Рефералов: {safe(u[3])}"
    )

# =========================================
# REF LINK
# =========================================

@bot.message_handler(func=lambda m: m.text == "👥 Рефералы")
def refs(m):

    link = f"https://t.me/{bot.get_me().username}?start={m.from_user.id}"

    bot.send_message(m.chat.id, f"👥 Ссылка:\n{link}")

# =========================================
# DAILY BONUS (FIXED)
# =========================================

@bot.message_handler(func=lambda m: m.text == "🎁 Подарок дня")
def daily(m):

    uid = m.from_user.id
    now = int(time.time())

    u = get(uid)
    if not u:
        return

    last = safe(u[5])

    if last and now - last < 86400:
        remain = 86400 - (now - last)
        h = remain // 3600
        mns = (remain % 3600) // 60
        return bot.send_message(m.chat.id, f"❌ Уже забрал\n⏳ {h}ч {mns}м")

    add(uid, DAILY_REWARD)

    sql("UPDATE users SET last_bonus=? WHERE user_id=?", (now, uid))

    bot.send_message(m.chat.id, f"🎁 +{DAILY_REWARD} G")

# =========================================
# TASKS (1 TIME LOGIC IN DB)
# =========================================

@bot.message_handler(func=lambda m: m.text == "📋 Задания")
def tasks(m):

    bot.send_message(
        m.chat.id,
        "📋 Задания:\n\n"
        "1️⃣ Подписка +1500 G\nhttps://t.me/k9ntoORIG\n\n"
        "2️⃣ Чат +1500 G\nhttps://t.me/+leM5HRVvncY4M2Uy"
    )

# =========================================
# WITHDRAW (FIXED MIN 10000 G)
# =========================================

withdraw_cache = {}

@bot.message_handler(func=lambda m: m.text == "💸 Вывод")
def withdraw(m):

    uid = m.from_user.id

    if balance(uid) < WITHDRAW_MIN:
        return bot.send_message(m.chat.id, f"❌ Минимум {WITHDRAW_MIN} G")

    msg = bot.send_message(m.chat.id, "🎮 Скин?")
    bot.register_next_step_handler(msg, w_skin)

def w_skin(m):

    withdraw_cache[m.from_user.id] = {"skin": m.text}

    msg = bot.send_message(m.chat.id, "💰 Сумма?")
    bot.register_next_step_handler(msg, w_amount)

def w_amount(m):

    uid = m.from_user.id

    try:
        amount = int(m.text)
    except:
        return bot.send_message(m.chat.id, "❌ число")

    if amount < WITHDRAW_MIN:
        return bot.send_message(m.chat.id, f"❌ Минимум {WITHDRAW_MIN} G")

    if amount > balance(uid):
        return bot.send_message(m.chat.id, "❌ нет денег")

    skin = withdraw_cache[uid]["skin"]

    sql("INSERT INTO withdraws VALUES (NULL, ?, ?, ?, ?)",
        (uid, skin, amount, "WAIT"))

    add(uid, -amount)

    bot.send_message(m.chat.id, "⏳ заявка отправлена")

    for a in ADMINS:

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ Принять", callback_data=f"ok_{uid}_{amount}"))
        kb.add(types.InlineKeyboardButton("❌ Отклонить", callback_data=f"no_{uid}_{amount}"))

        bot.send_message(a, f"💸 {uid} | {skin} | {amount} G", reply_markup=kb)

# =========================================
# CALLBACKS
# =========================================

@bot.callback_query_handler(func=lambda c: True)
def cb(c):

    uid = c.from_user.id

    if c.data == "check_sub":

        try:
            m = bot.get_chat_member(CHANNEL, uid)
            if m.status in ["member", "administrator", "creator"]:
                add(uid, 1500)
                bot.send_message(uid, "✅ +1500 G")
            else:
                bot.send_message(uid, "❌ не подписан")
        except:
            bot.send_message(uid, "❌ ошибка")

    if c.data == "chat_done":
        add(uid, 1500)
        bot.send_message(uid, "✅ +1500 G")

    if uid in ADMINS:

        data = c.data.split("_")

        if data[0] == "ok":
            bot.send_message(int(data[1]), "✅ вывод одобрен")

        if data[0] == "no":
            bot.send_message(int(data[1]), "❌ вывод отклонён")

# =========================================
# TOP
# =========================================

@bot.message_handler(func=lambda m: m.text == "🏆 Топ")
def top(m):

    rows = sql("SELECT username, refs FROM users ORDER BY refs DESC LIMIT 10", fetch=True)

    text = "🏆 Топ:\n\n"

    for i, r in enumerate(rows, 1):
        name = r[0] if r and r[0] else "NoName"
        text += f"{i}. @{name} — {safe(r[1])}\n"

    bot.send_message(m.chat.id, text)

# =========================================
# RUN
# =========================================

print("BOT STARTED")
bot.infinity_polling()
