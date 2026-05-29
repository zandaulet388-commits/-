# =========================================
# REF BOT FIX + STABLE SQLITE + G CURRENCY + ANTI-REF CHEAT
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
# SQLITE FIX
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
# HELPERS
# =========================================

def exists(uid):
    return sql(
        "SELECT 1 FROM users WHERE user_id=?",
        (uid,),
        fetch=True
    )

def create(uid, username, ref=None):
    sql(
        "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (uid, username, 0, 0, ref, 0, 0, 0)
    )

def get(uid):
    return sql(
        "SELECT * FROM users WHERE user_id=?",
        (uid,),
        fetch=True
    )[0]

def balance(uid):
    return int(get(uid)[2])

def set_balance(uid, val):
    sql(
        "UPDATE users SET balance=? WHERE user_id=?",
        (int(val), uid)
    )

def add(uid, val):
    set_balance(uid, balance(uid) + int(val))

def add_ref(uid):
    r = int(get(uid)[3]) + 1

    sql(
        "UPDATE users SET refs=? WHERE user_id=?",
        (r, uid)
    )

def has_ref(uid):
    r = sql(
        "SELECT invited_by FROM users WHERE user_id=?",
        (uid,),
        fetch=True
    )

    return r[0][0] if r else None

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
# START
# =========================================

started = set()

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
            pass

    # self ref protect
    if ref == uid:
        ref = None

    if not exists(uid):

        create(uid, username, None)

        # anti-ref cheat
        if ref and exists(ref):

            already = has_ref(uid)

            if not already:

                sql(
                    "UPDATE users SET invited_by=? WHERE user_id=?",
                    (ref, uid)
                )

                add(ref, REF_REWARD)
                add_ref(ref)

                bot.send_message(
                    ref,
                    f"🔥 +{REF_REWARD} G за друга"
                )

    bot.send_message(
        m.chat.id,
        "🔥 Бот запущен",
        reply_markup=menu()
    )

# =========================================
# PROFILE
# =========================================

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(m):

    u = get(m.from_user.id)

    bot.send_message(
        m.chat.id,
        f"👤 Профиль\n\n"
        f"💰 Баланс: {u[2]} G\n"
        f"👥 Рефералов: {u[3]}"
    )

# =========================================
# REF
# =========================================

@bot.message_handler(func=lambda m: m.text == "👥 Рефералы")
def refs(m):

    link = f"https://t.me/{bot.get_me().username}?start={m.from_user.id}"

    bot.send_message(
        m.chat.id,
        f"👥 Твоя ссылка:\n\n{link}\n\n"
        f"💰 За друга: {REF_REWARD} G"
    )

# =========================================
# DAILY BONUS FIXED
# =========================================

@bot.message_handler(func=lambda m: m.text == "🎁 Подарок дня")
def daily(m):

    uid = m.from_user.id

    now = int(time.time())

    u = get(uid)

    try:
        last = int(u[5])
    except:
        last = 0

    # 24h
    if last != 0:

        if now - last < 86400:

            remain = 86400 - (now - last)

            hours = remain // 3600
            mins = (remain % 3600) // 60

            return bot.send_message(
                m.chat.id,
                f"❌ Уже забрал\n⏳ Осталось: {hours}ч {mins}м"
            )

    add(uid, DAILY_REWARD)

    sql(
        "UPDATE users SET last_bonus=? WHERE user_id=?",
        (now, uid)
    )

    bot.send_message(
        m.chat.id,
        f"🎁 +{DAILY_REWARD} G"
    )

# =========================================
# TASKS
# =========================================

@bot.message_handler(func=lambda m: m.text == "📋 Задания")
def tasks(m):

    text = (
        "📋 Задания:\n\n"
        "1️⃣ Подписка на канал +1500 G\n"
        "👉 https://t.me/k9ntoORIG\n\n"
        "2️⃣ Вступить в чат +1500 G\n"
        "👉 https://t.me/+leM5HRVvncY4M2Uy"
    )

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🔁 Проверить подписку",
            callback_data="check_sub"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "💬 Проверить чат",
            callback_data="chat_done"
        )
    )

    bot.send_message(
        m.chat.id,
        text,
        reply_markup=kb
    )

# =========================================
# WITHDRAW
# =========================================

withdraw_cache = {}

@bot.message_handler(func=lambda m: m.text == "💸 Вывод")
def withdraw(m):

    uid = m.from_user.id

    if balance(uid) < WITHDRAW_MIN:

        return bot.send_message(
            m.chat.id,
            f"❌ Минимум {WITHDRAW_MIN} G"
        )

    msg = bot.send_message(
        m.chat.id,
        "🎮 Напиши скин:"
    )

    bot.register_next_step_handler(msg, w_skin)

def w_skin(m):

    withdraw_cache[m.from_user.id] = {
        "skin": m.text
    }

    msg = bot.send_message(
        m.chat.id,
        "💰 Сколько вывести?"
    )

    bot.register_next_step_handler(msg, w_amount)

def w_amount(m):

    uid = m.from_user.id

    try:
        amount = int(m.text)
    except:
        return bot.send_message(
            m.chat.id,
            "❌ Введи число"
        )

    if amount > balance(uid):

        return bot.send_message(
            m.chat.id,
            "❌ Недостаточно денег"
        )

    if amount < WITHDRAW_MIN:

        return bot.send_message(
            m.chat.id,
            f"❌ Минимум {WITHDRAW_MIN} G"
        )

    skin = withdraw_cache[uid]["skin"]

    sql(
        "INSERT INTO withdraws VALUES (NULL, ?, ?, ?, ?)",
        (uid, skin, amount, "WAIT")
    )

    add(uid, -amount)

    bot.send_message(
        m.chat.id,
        "⏳ Заявка отправлена"
    )

    for a in ADMINS:

        kb = types.InlineKeyboardMarkup()

        kb.add(
            types.InlineKeyboardButton(
                "✅ Принять",
                callback_data=f"ok_{uid}_{amount}"
            )
        )

        kb.add(
            types.InlineKeyboardButton(
                "❌ Отклонить",
                callback_data=f"no_{uid}_{amount}"
            )
        )

        bot.send_message(
            a,
            f"💸 ВЫВОД\n\n"
            f"👤 ID: {uid}\n"
            f"🎮 Скин: {skin}\n"
            f"💰 Сумма: {amount} G",
            reply_markup=kb
        )

# =========================================
# CALLBACKS
# =========================================

@bot.callback_query_handler(func=lambda c: True)
def cb(c):

    uid = c.from_user.id

    # =====================================
    # SUB TASK (ONE TIME)
    # =====================================

    if c.data == "check_sub":

        u = get(uid)

        # already done
        if int(u[6]) == 1:

            return bot.send_message(
                uid,
                "❌ Ты уже выполнял это задание"
            )

        try:

            member = bot.get_chat_member(CHANNEL, uid)

            if member.status in [
                "member",
                "administrator",
                "creator"
            ]:

                add(uid, 1500)

                sql(
                    "UPDATE users SET sub_done=1 WHERE user_id=?",
                    (uid,)
                )

                bot.send_message(
                    uid,
                    "✅ +1500 G"
                )

            else:

                bot.send_message(
                    uid,
                    "❌ Подпишись на канал"
                )

        except:

            bot.send_message(
                uid,
                "❌ Ошибка проверки"
            )

    # =====================================
    # CHAT TASK (ONE TIME)
    # =====================================

    if c.data == "chat_done":

        u = get(uid)

        if int(u[7]) == 1:

            return bot.send_message(
                uid,
                "❌ Ты уже выполнял это задание"
            )

        add(uid, 1500)

        sql(
            "UPDATE users SET chat_done=1 WHERE user_id=?",
            (uid,)
        )

        bot.send_message(
            uid,
            "✅ +1500 G"
        )

    # =====================================
    # ADMIN
    # =====================================

    if uid in ADMINS:

        data = c.data.split("_")

        if data[0] == "ok":

            u = int(data[1])

            bot.send_message(
                u,
                "✅ Вывод одобрен"
            )

        if data[0] == "no":

            u = int(data[1])

            bot.send_message(
                u,
                "❌ Вывод отклонён"
            )

# =========================================
# TOP
# =========================================

@bot.message_handler(func=lambda m: m.text == "🏆 Топ")
def top(m):

    rows = sql(
        "SELECT username, refs FROM users ORDER BY refs DESC LIMIT 10",
        fetch=True
    )

    text = "🏆 Топ рефералов:\n\n"

    for i, r in enumerate(rows, 1):

        name = r[0] if r[0] else "NoName"

        text += f"{i}. @{name} — {r[1]}\n"

    bot.send_message(
        m.chat.id,
        text
    )

# =========================================
# RUN
# =========================================

print("BOT STARTED")

bot.infinity_polling()
