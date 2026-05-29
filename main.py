# =========================================
# FULL REF BOT (STABLE + FIXED + ADMIN PANEL)
# =========================================

import telebot
from telebot import types
import sqlite3
import threading
import time
import random
import string

TOKEN = "8920387142:AAEf_Rv7GIYGLYn_3SfG4NFdtvuti1zHL7Q"
bot = telebot.TeleBot(TOKEN)

ADMINS = [8763987324]

REF_REWARD = 1000
DAILY_REWARD = 250
TASK_REWARD = 1500
WITHDRAW_MIN = 10000

CHANNEL = "@k9ntoORIG"
CHAT = "https://t.me/+leM5HRVvncY4M2Uy"

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

sql("""
CREATE TABLE IF NOT EXISTS promocodes (
code TEXT,
reward INTEGER,
activations INTEGER
)
""")

sql("""
CREATE TABLE IF NOT EXISTS promo_uses (
user_id INTEGER,
code TEXT
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

def ensure(uid, username="None"):

    u = sql(
        "SELECT * FROM users WHERE user_id=?",
        (uid,),
        fetch=True
    )

    if not u:
        sql(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (uid, username, 0, 0, 0, 0, 0, 0)
        )

def get(uid):
    ensure(uid)
    return sql(
        "SELECT * FROM users WHERE user_id=?",
        (uid,),
        fetch=True
    )[0]

def balance(uid):
    return safe(get(uid)[2])

def add(uid, val):

    sql(
        "UPDATE users SET balance=? WHERE user_id=?",
        (balance(uid) + safe(val), uid)
    )

def add_ref(uid):

    u = get(uid)

    refs = safe(u[3]) + 1

    sql(
        "UPDATE users SET refs=? WHERE user_id=?",
        (refs, uid)
    )

# =========================================
# MENUS
# =========================================

def menu():

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row("👤 Профиль", "👥 Рефералы")
    kb.row("🎁 Подарок дня", "📋 Задания")
    kb.row("🎟 Промокод", "💸 Вывод")
    kb.row("🏆 Топ")

    return kb

def back_menu():

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row("🔙 Назад")

    return kb

def admin_menu():

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row("📨 Заявки", "🎟 Создать промо")
    kb.row("📊 Статистика")
    kb.row("🔙 Назад")

    return kb

# =========================================
# START + REF SYSTEM
# =========================================

@bot.message_handler(commands=['start'])
def start(m):

    uid = m.from_user.id
    username = m.from_user.username or f"id{uid}"

    ensure(uid, username)

    args = m.text.split()

    ref = None

    if len(args) > 1:
        try:
            ref = int(args[1])
        except:
            ref = None

    if ref == uid:
        ref = None

    # =====================================
    # REF SYSTEM
    # =====================================

    if ref:

        ref_user = sql(
            "SELECT * FROM users WHERE user_id=?",
            (ref,),
            fetch=True
        )

        if ref_user:

            u = get(uid)

            if safe(u[4]) == 0:

                sql(
                    "UPDATE users SET invited_by=? WHERE user_id=?",
                    (ref, uid)
                )

                add(ref, REF_REWARD)
                add_ref(ref)

                bot.send_message(
                    ref,
                    f"🔥 +{REF_REWARD} G за нового реферала"
                )

    bot.send_message(
        m.chat.id,
        "👋 Добро пожаловать!",
        reply_markup=menu()
    )

# =========================================
# BACK
# =========================================

@bot.message_handler(func=lambda m: m.text == "🔙 Назад")
def back(m):

    if m.from_user.id in ADMINS:
        bot.send_message(
            m.chat.id,
            "🏠 Главное меню",
            reply_markup=menu()
        )
    else:
        bot.send_message(
            m.chat.id,
            "🏠 Главное меню",
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
        f"💰 Баланс: {safe(u[2])} G\n"
        f"👥 Рефералов: {safe(u[3])}"
    )

# =========================================
# REFS
# =========================================

@bot.message_handler(func=lambda m: m.text == "👥 Рефералы")
def refs(m):

    link = f"https://t.me/{bot.get_me().username}?start={m.from_user.id}"

    bot.send_message(
        m.chat.id,
        f"👥 Твоя ссылка:\n\n{link}"
    )

# =========================================
# DAILY BONUS
# =========================================

@bot.message_handler(func=lambda m: m.text == "🎁 Подарок дня")
def daily(m):

    uid = m.from_user.id

    now = int(time.time())

    u = get(uid)

    last = safe(u[5])

    if last and now - last < 86400:

        remain = 86400 - (now - last)

        h = remain // 3600
        mm = (remain % 3600) // 60

        return bot.send_message(
            m.chat.id,
            f"❌ Уже забрал\n⏳ {h}ч {mm}м"
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
        "1️⃣ Подписка +1500 G\n"
        f"👉 {CHANNEL}\n\n"
        "2️⃣ Чат +1500 G\n"
        f"👉 {CHAT}"
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
# PROMOCODE
# =========================================

@bot.message_handler(func=lambda m: m.text == "🎟 Промокод")
def promo(m):

    msg = bot.send_message(
        m.chat.id,
        "🎟 Введи промокод:",
        reply_markup=back_menu()
    )

    bot.register_next_step_handler(msg, promo_check)

def promo_check(m):

    if m.text == "🔙 Назад":
        return back(m)

    uid = m.from_user.id

    code = m.text.upper()

    p = sql(
        "SELECT * FROM promocodes WHERE code=?",
        (code,),
        fetch=True
    )

    if not p:
        return bot.send_message(uid, "❌ Промокод не найден")

    used = sql(
        "SELECT * FROM promo_uses WHERE user_id=? AND code=?",
        (uid, code),
        fetch=True
    )

    if used:
        return bot.send_message(uid, "❌ Ты уже активировал")

    reward = safe(p[0][1])
    activations = safe(p[0][2])

    if activations <= 0:
        return bot.send_message(uid, "❌ Промокод закончился")

    add(uid, reward)

    sql(
        "INSERT INTO promo_uses VALUES (?, ?)",
        (uid, code)
    )

    sql(
        "UPDATE promocodes SET activations=? WHERE code=?",
        (activations - 1, code)
    )

    bot.send_message(
        uid,
        f"✅ +{reward} G"
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
        "🎮 Напиши скин:",
        reply_markup=back_menu()
    )

    bot.register_next_step_handler(msg, w_skin)

def w_skin(m):

    if m.text == "🔙 Назад":
        return back(m)

    withdraw_cache[m.from_user.id] = {
        "skin": m.text
    }

    msg = bot.send_message(
        m.chat.id,
        "💰 Напиши сумму:"
    )

    bot.register_next_step_handler(msg, w_amount)

def w_amount(m):

    if m.text == "🔙 Назад":
        return back(m)

    uid = m.from_user.id

    try:
        amount = int(m.text)
    except:
        return bot.send_message(
            uid,
            "❌ Введи число"
        )

    if amount < WITHDRAW_MIN:
        return bot.send_message(
            uid,
            f"❌ Минимум {WITHDRAW_MIN} G"
        )

    if amount > balance(uid):
        return bot.send_message(
            uid,
            "❌ Недостаточно денег"
        )

    skin = withdraw_cache[uid]["skin"]

    sql(
        "INSERT INTO withdraws VALUES (NULL, ?, ?, ?, ?)",
        (uid, skin, amount, "WAIT")
    )

    add(uid, -amount)

    bot.send_message(
        uid,
        "⏳ Заявка отправлена"
    )

    wid = sql(
        "SELECT id FROM withdraws ORDER BY id DESC LIMIT 1",
        fetch=True
    )[0][0]

    for a in ADMINS:

        kb = types.InlineKeyboardMarkup()

        kb.add(
            types.InlineKeyboardButton(
                "✅ Выплатил",
                callback_data=f"paid_{wid}"
            )
        )

        kb.add(
            types.InlineKeyboardButton(
                "🔄 Вернуть",
                callback_data=f"return_{wid}"
            )
        )

        bot.send_message(
            a,
            f"💸 Новая заявка\n\n"
            f"🆔 ID: {wid}\n"
            f"👤 USER: {uid}\n"
            f"🎮 SKIN: {skin}\n"
            f"💰 SUM: {amount} G",
            reply_markup=kb
        )

# =========================================
# ADMIN PANEL
# =========================================

@bot.message_handler(commands=['admin'])
def admin(m):

    if m.from_user.id not in ADMINS:
        return

    bot.send_message(
        m.chat.id,
        "🛠 Админ панель",
        reply_markup=admin_menu()
    )

# =========================================
# ADMIN CREATE PROMO
# =========================================

@bot.message_handler(func=lambda m: m.text == "🎟 Создать промо")
def create_promo(m):

    if m.from_user.id not in ADMINS:
        return

    msg = bot.send_message(
        m.chat.id,
        "📦 Формат:\n\nCODE REWARD ACTIVATIONS"
    )

    bot.register_next_step_handler(msg, promo_create_finish)

def promo_create_finish(m):

    if m.from_user.id not in ADMINS:
        return

    try:

        data = m.text.split()

        code = data[0].upper()
        reward = int(data[1])
        activations = int(data[2])

    except:
        return bot.send_message(
            m.chat.id,
            "❌ Ошибка"
        )

    sql(
        "INSERT INTO promocodes VALUES (?, ?, ?)",
        (code, reward, activations)
    )

    bot.send_message(
        m.chat.id,
        f"✅ Промокод создан\n\n"
        f"🎟 CODE: {code}\n"
        f"💰 REWARD: {reward}\n"
        f"👥 USES: {activations}"
    )

# =========================================
# ADMIN STATS
# =========================================

@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats(m):

    if m.from_user.id not in ADMINS:
        return

    users = sql(
        "SELECT COUNT(*) FROM users",
        fetch=True
    )[0][0]

    withdraws = sql(
        "SELECT COUNT(*) FROM withdraws",
        fetch=True
    )[0][0]

    bot.send_message(
        m.chat.id,
        f"📊 Статистика\n\n"
        f"👥 Пользователей: {users}\n"
        f"💸 Выводов: {withdraws}"
    )

# =========================================
# ADMIN REQUESTS
# =========================================

@bot.message_handler(func=lambda m: m.text == "📨 Заявки")
def requests(m):

    if m.from_user.id not in ADMINS:
        return

    rows = sql(
        "SELECT * FROM withdraws WHERE status='WAIT'",
        fetch=True
    )

    if not rows:
        return bot.send_message(
            m.chat.id,
            "❌ Заявок нет"
        )

    for r in rows:

        wid = r[0]
        uid = r[1]
        skin = r[2]
        amount = r[3]

        kb = types.InlineKeyboardMarkup()

        kb.add(
            types.InlineKeyboardButton(
                "✅ Выплатил",
                callback_data=f"paid_{wid}"
            )
        )

        kb.add(
            types.InlineKeyboardButton(
                "🔄 Вернуть",
                callback_data=f"return_{wid}"
            )
        )

        bot.send_message(
            m.chat.id,
            f"🆔 {wid}\n"
            f"👤 {uid}\n"
            f"🎮 {skin}\n"
            f"💰 {amount} G",
            reply_markup=kb
        )

# =========================================
# CALLBACKS
# =========================================

@bot.callback_query_handler(func=lambda c: True)
def cb(c):

    uid = c.from_user.id

    # =====================================
    # SUB CHECK
    # =====================================

    if c.data == "check_sub":

        u = get(uid)

        if safe(u[6]) == 1:
            return bot.send_message(uid, "❌ Уже выполнено")

        try:

            member = bot.get_chat_member(CHANNEL, uid)

            if member.status in [
                "member",
                "administrator",
                "creator"
            ]:

                add(uid, TASK_REWARD)

                sql(
                    "UPDATE users SET sub_done=1 WHERE user_id=?",
                    (uid,)
                )

                bot.send_message(
                    uid,
                    f"✅ +{TASK_REWARD} G"
                )

            else:
                bot.send_message(uid, "❌ Ты не подписан")

        except:
            bot.send_message(uid, "❌ Ошибка проверки")

    # =====================================
    # CHAT TASK
    # =====================================

    elif c.data == "chat_done":

        u = get(uid)

        if safe(u[7]) == 1:
            return bot.send_message(uid, "❌ Уже выполнено")

        add(uid, TASK_REWARD)

        sql(
            "UPDATE users SET chat_done=1 WHERE user_id=?",
            (uid,)
        )

        bot.send_message(
            uid,
            f"✅ +{TASK_REWARD} G"
        )

    # =====================================
    # ADMIN PAY
    # =====================================

    elif c.data.startswith("paid_"):

        if uid not in ADMINS:
            return

        wid = int(c.data.split("_")[1])

        w = sql(
            "SELECT * FROM withdraws WHERE id=?",
            (wid,),
            fetch=True
        )

        if not w:
            return

        w = w[0]

        sql(
            "UPDATE withdraws SET status='PAID' WHERE id=?",
            (wid,)
        )

        bot.send_message(
            w[1],
            "✅ Твой вывод выплачен"
        )

        bot.edit_message_text(
            f"✅ ВЫПЛАЧЕНО\n\nID {wid}",
            c.message.chat.id,
            c.message.message_id
        )

    # =====================================
    # ADMIN RETURN
    # =====================================

    elif c.data.startswith("return_"):

        if uid not in ADMINS:
            return

        wid = int(c.data.split("_")[1])

        w = sql(
            "SELECT * FROM withdraws WHERE id=?",
            (wid,),
            fetch=True
        )

        if not w:
            return

        w = w[0]

        add(w[1], w[3])

        sql(
            "UPDATE withdraws SET status='RETURNED' WHERE id=?",
            (wid,)
        )

        bot.send_message(
            w[1],
            f"🔄 Тебе вернули {w[3]} G"
        )

        bot.edit_message_text(
            f"🔄 ВОЗВРАТ\n\nID {wid}",
            c.message.chat.id,
            c.message.message_id
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

        username = r[0]

        if not username:
            username = "NoName"
        else:
            username = f"@{username}"

        refs = safe(r[1])

        text += f"{i}. {username} — {refs}\n"

    bot.send_message(
        m.chat.id,
        text
    )

# =========================================
# RUN
# =========================================

print("BOT STARTED")

bot.infinity_polling(
    timeout=60,
    long_polling_timeout=60
    )
