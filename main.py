# =========================================
# STANDLEO FACEIT BOT FULL FIX
# Python 3.11+
# pip install pyTelegramBotAPI
# =========================================

import telebot
from telebot import types
import sqlite3
import random
import time
import re

# =========================================
# TOKEN
# =========================================

TOKEN = "8818405158:AAHWwdPc3qLRXjWvO4eOFQf-0L4MSaA80Ow"

bot = telebot.TeleBot(TOKEN)

match_reports = {}

# =========================================
# SAFE INT
# =========================================

def safe_int(text):

    numbers = re.findall(r'\d+', str(text))

    if not numbers:
        return None

    return int(numbers[0])

# =========================================
# ADMINS
# =========================================

ADMINS = [8663599703]

# =========================================
# DATABASE
# =========================================

conn = sqlite3.connect("standleo.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    nickname TEXT,
    game_id TEXT,
    elo INTEGER DEFAULT 0,
    lvl INTEGER DEFAULT 0,
    calibration INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    loses INTEGER DEFAULT 0,
    kd REAL DEFAULT 1.00,
    warns INTEGER DEFAULT 0,
    mute_until INTEGER DEFAULT 0
)
""")

conn.commit()

# =========================================
# MAPS
# =========================================

MAPS = [
    "Rust",
    "Province",
    "Sandstone",
    "Breeze",
    "Hanami",
    "Prison"
]

# =========================================
# LOBBIES
# =========================================

lobbies = {
    "pc_1x1": [],
    "pc_2x2": [],
    "pc_5x5": [],

    "mobile_1x1": [],
    "mobile_2x2": [],
    "mobile_5x5": []
}

sizes = {
    "pc_1x1": 2,
    "pc_2x2": 4,
    "pc_5x5": 10,

    "mobile_1x1": 2,
    "mobile_2x2": 4,
    "mobile_5x5": 10
}

# =========================================
# PLAY MENU
# =========================================

@bot.message_handler(func=lambda m: m.text == "🎮 Играть")
def play_menu(message):

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row("💻 PC 1x1", "💻 PC 2x2")
    kb.row("💻 PC 5x5")

    kb.row("📱 MOBILE 1x1", "📱 MOBILE 2x2")
    kb.row("📱 MOBILE 5x5")

    kb.row("🔙 Назад")

    bot.send_message(
        message.chat.id,
        "🎮 Выбери режим",
        reply_markup=kb
    )

# =========================================
# JOIN LOBBY
# =========================================

@bot.message_handler(func=lambda m: m.text in [
    "💻 PC 1x1",
    "💻 PC 2x2",
    "💻 PC 5x5",
    "📱 MOBILE 1x1",
    "📱 MOBILE 2x2",
    "📱 MOBILE 5x5"
])
def join_lobby(message):

    uid = message.from_user.id

    user = get_user(uid)

    if not user:

        bot.send_message(
            message.chat.id,
            "❌ Сначала напиши /start"
        )

        return

    if user[11] > int(time.time()):

        bot.send_message(
            message.chat.id,
            "🔇 У тебя мут"
        )

        return

    mode_map = {
        "💻 PC 1x1": "pc_1x1",
        "💻 PC 2x2": "pc_2x2",
        "💻 PC 5x5": "pc_5x5",

        "📱 MOBILE 1x1": "mobile_1x1",
        "📱 MOBILE 2x2": "mobile_2x2",
        "📱 MOBILE 5x5": "mobile_5x5"
    }

    mode = mode_map[message.text]

    for m in lobbies:

        if uid in lobbies[m]:
            lobbies[m].remove(uid)

    if uid not in lobbies[mode]:
        lobbies[mode].append(uid)

    # =========================================
    # TITLE
    # =========================================

    if "1x1" in mode:
        title = "1x1"

    elif "2x2" in mode:
        title = "2x2"

    else:
        title = "5x5"

    # =========================================
    # DEVICE
    # =========================================

    if "pc" in mode:
        device = "💻 Лобби (PC)"
    else:
        device = "📱 Лобби (MOBILE)"

    text = f"🛡 Standleo\n"
    text += f"🎮 ЛОББИ {title}\n\n"

    text += f"{device}\n"

    text += (
        f"Игроков в лобби: "
        f"{len(lobbies[mode])}/{sizes[mode]}\n\n"
    )

    text += "Игроки в лобби:\n"

    for player in lobbies[mode]:

        u = get_user(player)

        if not u:
            continue

        if u[6] < 5:

            text += f"🔒 {u[2]} ({u[6]}/5)\n"

        else:

            text += (
                f"{u[5]}️⃣ "
                f"{u[2]} "
                f"(ELO: {u[4]})\n"
            )

    text += "\n🔥 Fastuk Faceit"

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🚪 Выйти из лобби")

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=kb
    )

    # =========================================
    # READY MATCH SYSTEM
    # =========================================

    if len(lobbies[mode]) >= sizes[mode]:

        ready_matches[mode] = []

        kb_ready = types.InlineKeyboardMarkup()

        kb_ready.add(
            types.InlineKeyboardButton(
                "✅ Подтвердить",
                callback_data=f"ready_{mode}"
            )
        )

        for player in lobbies[mode]:

            try:

                bot.send_message(
                    player,
                    f"🔥 Лобби {title} найдено\n\n"
                    f"Нажмите подтвердить готовность",
                    reply_markup=kb_ready
                )

            except:
                pass

# =========================================
# PARTIES
# =========================================

parties = {}

# =========================================
# READY SYSTEM
# =========================================

ready_matches = {}

# =========================================
# PC / MOBILE MODES
# =========================================

mode_device = {
    "1x1": "💻 Лобби (PC)",
    "2x2": "💻 Лобби (PC)",
    "5x5": "💻 Лобби (PC)"
}

# =========================================
# MATCH REPORTS
# =========================================

match_reports = {}

# =========================================
# CREATE USER
# =========================================

def create_user(user_id, username):

    cur.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )

    user = cur.fetchone()

    if not user:

        cur.execute(
            "INSERT INTO users(user_id, username) VALUES(?, ?)",
            (user_id, username)
        )

        conn.commit()

# =========================================
# GET USER
# =========================================

def get_user(user_id):

    cur.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )

    return cur.fetchone()

# =========================================
# GET LEVEL
# =========================================

def get_level(elo):

    if elo >= 4000:
        return 10
    elif elo >= 3200:
        return 9
    elif elo >= 2600:
        return 8
    elif elo >= 2200:
        return 7
    elif elo >= 1800:
        return 6
    elif elo >= 1400:
        return 5
    elif elo >= 1000:
        return 4
    elif elo >= 700:
        return 3
    elif elo >= 400:
        return 2
    elif elo >= 200:
        return 1

    return 0

# =========================================
# MAIN MENU
# =========================================

def main_menu():

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🎮 Играть")
    kb.add("👤 Профиль", "👥 Пати")
    kb.add("🏆 Топ ELO")
    kb.add("⚙ Админ панель")

    return kb
  # =========================================
# BACK BUTTON
# =========================================

@bot.message_handler(func=lambda m: m.text == "🔙 Назад")
def back_menu(message):

    bot.send_message(
        message.chat.id,
        "🔙 Главное меню",
        reply_markup=main_menu()
    )
# =========================================
# START
# =========================================

@bot.message_handler(commands=["start"])
def start(message):

    uid = message.from_user.id
    username = message.from_user.username

    create_user(uid, username)

    bot.send_message(
        message.chat.id,
        "🛡 Добро пожаловать в STANDLEO FACEIT\n\n"
        "🎮 Введи ник в игре"
    )

    bot.register_next_step_handler(
        message,
        get_nickname
    )

# =========================
# CALLBACKS
# =========================

@bot.callback_query_handler(func=lambda c: c.data.startswith("result_"))
def send_result(call):

    mode = call.data.split("_", 1)[1]

    msg = bot.send_message(
        call.message.chat.id,
        "📸 Отправь скрин"
    )

    bot.register_next_step_handler(
        msg,
        process_screenshot,
        mode
    )

# =========================
# SCREENSHOT PROCESS
# =========================

def process_screenshot(message, mode):

    if not message.photo:

        bot.send_message(
            message.chat.id,
            "❌ Отправь именно фото (скрин)"
        )

        return

    file_id = message.photo[-1].file_id

    report_id = random.randint(1000, 9999)

    match_reports[report_id] = {
        "mode": mode,
        "photo": file_id,
        "user_id": message.from_user.id
    }

    bot.send_message(
        message.chat.id,
        f"✅ Скрин сохранён!\nID отчёта: {report_id}"
    )

# =========================================
# GET NICKNAME
# =========================================

def get_nickname(message):

    nickname = message.text

    cur.execute(
        "UPDATE users SET nickname=? WHERE user_id=?",
        (nickname, message.from_user.id)
    )

    conn.commit()

    bot.send_message(
        message.chat.id,
        "🆔 Введи ID в игре"
    )

    bot.register_next_step_handler(
        message,
        get_game_id
    )

# =========================================
# GET GAME ID
# =========================================

def get_game_id(message):

    game_id = message.text

    cur.execute(
        "UPDATE users SET game_id=? WHERE user_id=?",
        (game_id, message.from_user.id)
    )

    conn.commit()

    bot.send_message(
        message.chat.id,
        "✅ Регистрация завершена",
        reply_markup=main_menu()
    )

# =========================================
# PROFILE
# =========================================

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):

    user = get_user(message.from_user.id)

    calibration = user[6]
    elo = user[4]
    lvl = user[5]
    wins = user[7]
    loses = user[8]
    kd = user[9]
    warns = user[10]
    mute_until = user[11]

    total = wins + loses

    if total <= 0:
        wl = 0
    else:
        wl = int((wins / total) * 100)

    if calibration < 5:
        elo_text = "🔒 Calibration"
        lvl_text = "🔒 Calibration"
    else:
        elo_text = f"🔥 {elo}"
        lvl_text = f"{lvl}️⃣"

    mute_text = "Нет"

    if mute_until > int(time.time()):

        remain = mute_until - int(time.time())
        minutes = remain // 60

        mute_text = f"{minutes} мин"

    text = f"""
🛡 STANDLEO FACEIT

👤 Ник: {user[2]}
🆔 Bot ID: {message.from_user.id}
🎮 Игровой ID: {user[3]}
📱 Username: @{user[1]}

ELO: {elo_text}
LVL: {lvl_text}

📊 Калибровка: {calibration}/5

⚔ K/D: {kd}
🏆 W/L: {wl}%

⚠ Варны: {warns}
🔇 Мут: {mute_text}

🔥 Fastuk Faceit
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu()
    )

# =========================================
# PLAY MENU
# =========================================

@bot.message_handler(func=lambda m: m.text == "🎮 Играть")
def play_menu(message):

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("1x1", "2x2", "5x5")
    kb.add("🔙 Назад")

    bot.send_message(
        message.chat.id,
        "🎮 Выбери режим",
        reply_markup=kb
    )

# =========================================
# JOIN LOBBY
# =========================================

@bot.message_handler(func=lambda m: m.text in ["1x1", "2x2", "5x5"])
def join_lobby(message):

    uid = message.from_user.id
    mode = message.text

    user = get_user(uid)

    if not user:

        bot.send_message(
            message.chat.id,
            "❌ Сначала напиши /start"
        )

        return

    if user[11] > int(time.time()):

        bot.send_message(
            message.chat.id,
            "🔇 У тебя мут"
        )

        return

    for m in lobbies:

        if uid in lobbies[m]:
            lobbies[m].remove(uid)

    if uid not in lobbies[mode]:
        lobbies[mode].append(uid)

    text = f"🛡 Standleo\n"
    text += f"🎮 ЛОББИ {mode}\n\n"

    text += f"{mode_device[mode]}\n"

    text += f"Игроков в лобби: {len(lobbies[mode])}/{sizes[mode]}\n\n"

    text += "Игроки в лобби:\n"

    for player in lobbies[mode]:

        u = get_user(player)

        if not u:
            continue

        if u[6] < 5:
            text += f"🔒 {u[2]} ({u[6]}/5)\n"
        else:
            text += f"{u[5]}️⃣ {u[2]} (ELO: {u[4]})\n"

    text += "\n🔥 Fastuk Faceit"

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🚪 Выйти из лобби")

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=kb
    )

    # =========================================
    # READY MATCH SYSTEM
    # =========================================

    if len(lobbies[mode]) >= sizes[mode]:

        ready_matches[mode] = []

        kb_ready = types.InlineKeyboardMarkup()

        kb_ready.add(
            types.InlineKeyboardButton(
                "✅ Подтвердить",
                callback_data=f"ready_{mode}"
            )
        )

        for player in lobbies[mode]:

            try:

                bot.send_message(
                    player,
                    f"🔥 Лобби {mode} найдено\n\n"
                    f"Нажмите подтвердить готовность",
                    reply_markup=kb_ready
                )

            except:
                pass

# =========================================
# READY CALLBACK
# =========================================

@bot.callback_query_handler(func=lambda c: c.data.startswith("ready_"))
def ready_callback(call):

    uid = call.from_user.id

    mode = call.data.split("_")[1]

    if mode not in ready_matches:
        return

    if uid not in ready_matches[mode]:

        ready_matches[mode].append(uid)

    ready_count = len(ready_matches[mode])

    total = sizes[mode]

    for player in lobbies[mode]:

        try:

            bot.send_message(
                player,
                f"✅ Подтверждено: {ready_count}/{total}"
            )

        except:
            pass

# =========================================
# PARTY SYSTEM
# =========================================

party_invites = {}

@bot.message_handler(func=lambda m: m.text == "👥 Пати")
def party_menu(message):

    uid = message.from_user.id

    if uid not in parties:

        parties[uid] = {
            "leader": uid,
            "players": [uid]
        }

    party = parties[uid]

    text = "🛡 StandLeo\n\n"
    text += "👥 ПАТИ |\n\n"

    leader = get_user(party["leader"])

    text += f"👑 Лидер: {leader[2]}\n"

    text += (
        f"👥 Состав "
        f"({len(party['players'])}/2):\n"
    )

    pos = 1

    for player in party["players"]:

        u = get_user(player)

        role = ""

        if player == party["leader"]:
            role = " (Лидер)"

        text += (
            f"{pos}. {u[2]}"
            f"{role} "
            f"(ID: {player})\n"
        )

        pos += 1

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "➕ Пригласить",
            callback_data="party_invite"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🚪 Покинуть пати",
            callback_data="party_leave"
        )
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=kb
    )

# =========================================
# PARTY CALLBACKS
# =========================================

@bot.callback_query_handler(func=lambda c: c.data == "party_invite")
def party_invite(call):

    uid = call.from_user.id

    msg = bot.send_message(
        call.message.chat.id,
        "🆔 Введите ID игрока"
    )

    bot.register_next_step_handler(
        msg,
        send_party_invite,
        uid
    )

def send_party_invite(message, leader_id):

    try:
        target = int(message.text)
    except:
        return bot.send_message(
            message.chat.id,
            "❌ Неверный ID"
        )

    if leader_id not in parties:
        return

    party = parties[leader_id]

    if len(party["players"]) >= 2:
        return bot.send_message(
            message.chat.id,
            "❌ Пати заполнено"
        )

    party_invites[target] = leader_id

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "✅ Принять",
            callback_data=f"party_accept_{leader_id}"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "❌ Отказаться",
            callback_data=f"party_decline_{leader_id}"
        )
    )

    try:

        bot.send_message(
            target,
            "👥 Вас пригласили в пати",
            reply_markup=kb
        )

        bot.send_message(
            message.chat.id,
            "✅ Приглашение отправлено"
        )

    except:

        bot.send_message(
            message.chat.id,
            "❌ Игрок не найден"
        )

@bot.callback_query_handler(func=lambda c: c.data.startswith("party_accept_"))
def accept_party(call):

    uid = call.from_user.id

    leader_id = int(call.data.split("_")[2])

    if leader_id not in parties:
        return

    parties[leader_id]["players"].append(uid)

    parties[uid] = parties[leader_id]

    bot.send_message(
        uid,
        "✅ Вы вошли в пати"
    )

    bot.send_message(
        leader_id,
        "✅ Игрок вошёл в пати"
    )

@bot.callback_query_handler(func=lambda c: c.data == "party_leave")
def leave_party(call):

    uid = call.from_user.id

    if uid not in parties:
        return

    party = parties[uid]

    if uid in party["players"]:
        party["players"].remove(uid)

    if uid == party["leader"]:

        for p in party["players"]:

            if p in parties:
                del parties[p]

        if uid in parties:
            del parties[uid]

    else:

        if uid in parties:
            del parties[uid]

    bot.send_message(
        uid,
        "✅ Вы покинули пати"
    )

# =========================================
# ADMIN PANEL
# =========================================

@bot.message_handler(func=lambda m: m.text == "⚙ Админ панель")
def admin_panel(message):

    if message.from_user.id not in ADMINS:
        return

    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.row("➕ ADD ELO", "➖ REMOVE ELO")
    kb.row("➕ ADD LVL", "➖ REMOVE LVL")
    kb.row("⚠ ВАРН", "🔇 МУТ")
    kb.row("📨 ЗАЯВКИ")
    kb.row("🔙 Назад")

    bot.send_message(
        message.chat.id,
        "⚙ Админ панель",
        reply_markup=kb
    )

# =========================================
# ADMIN ACTIONS
# =========================================

@bot.message_handler(func=lambda m: m.text == "➕ ADD ELO")
def add_elo_start(message):

    if message.from_user.id not in ADMINS:
        return

    msg = bot.send_message(
        message.chat.id,
        "🆔 ID игрока и ELO\nПример:\n8663599703 500"
    )

    bot.register_next_step_handler(
        msg,
        add_elo_finish
    )

def add_elo_finish(message):

    try:

        uid = int(message.text.split()[0])
        elo = int(message.text.split()[1])

    except:

        return bot.send_message(
            message.chat.id,
            "❌ Ошибка"
        )

    user = get_user(uid)

    if not user:
        return

    new_elo = user[4] + elo
    lvl = get_level(new_elo)

    cur.execute(
        "UPDATE users SET elo=?, lvl=? WHERE user_id=?",
        (new_elo, lvl, uid)
    )

    conn.commit()

    bot.send_message(
        message.chat.id,
        "✅ ELO добавлено"
    )

@bot.message_handler(func=lambda m: m.text == "➖ REMOVE ELO")
def remove_elo_start(message):

    if message.from_user.id not in ADMINS:
        return

    msg = bot.send_message(
        message.chat.id,
        "🆔 ID игрока и ELO"
    )

    bot.register_next_step_handler(
        msg,
        remove_elo_finish
    )

def remove_elo_finish(message):

    try:

        uid = int(message.text.split()[0])
        elo = int(message.text.split()[1])

    except:

        return

    user = get_user(uid)

    if not user:
        return

    new_elo = max(0, user[4] - elo)
    lvl = get_level(new_elo)

    cur.execute(
        "UPDATE users SET elo=?, lvl=? WHERE user_id=?",
        (new_elo, lvl, uid)
    )

    conn.commit()

    bot.send_message(
        message.chat.id,
        "✅ ELO снято"
    )

@bot.message_handler(func=lambda m: m.text == "➕ ADD LVL")
def add_lvl(message):

    if message.from_user.id not in ADMINS:
        return

    msg = bot.send_message(
        message.chat.id,
        "🆔 ID и LVL"
    )

    bot.register_next_step_handler(
        msg,
        add_lvl_finish
    )

def add_lvl_finish(message):

    try:

        uid = int(message.text.split()[0])
        lvl = int(message.text.split()[1])

    except:
        return

    cur.execute(
        "UPDATE users SET lvl=? WHERE user_id=?",
        (lvl, uid)
    )

    conn.commit()

    bot.send_message(
        message.chat.id,
        "✅ LVL изменён"
    )

@bot.message_handler(func=lambda m: m.text == "⚠ ВАРН")
def warn_user(message):

    if message.from_user.id not in ADMINS:
        return

    msg = bot.send_message(
        message.chat.id,
        "🆔 ID игрока"
    )

    bot.register_next_step_handler(
        msg,
        warn_finish
    )

def warn_finish(message):

    try:
        uid = int(message.text)
    except:
        return

    user = get_user(uid)

    warns = user[10] + 1

    cur.execute(
        "UPDATE users SET warns=? WHERE user_id=?",
        (warns, uid)
    )

    conn.commit()

    bot.send_message(
        message.chat.id,
        "✅ Варн выдан"
    )

    bot.send_message(
        uid,
        f"⚠ Вам выдали варн\nВсего: {warns}"
    )

@bot.message_handler(func=lambda m: m.text == "🔇 МУТ")
def mute_user(message):

    if message.from_user.id not in ADMINS:
        return

    msg = bot.send_message(
        message.chat.id,
        "🆔 ID и минуты"
    )

    bot.register_next_step_handler(
        msg,
        mute_finish
    )

def mute_finish(message):

    try:

        uid = int(message.text.split()[0])
        mins = int(message.text.split()[1])

    except:
        return

    mute_until = int(time.time()) + (mins * 60)

    cur.execute(
        "UPDATE users SET mute_until=? WHERE user_id=?",
        (mute_until, uid)
    )

    conn.commit()

    bot.send_message(
        message.chat.id,
        "✅ Мут выдан"
    )

    bot.send_message(
        uid,
        f"🔇 Вам выдали мут на {mins} мин"
    )

# =========================================
# ADMIN MATCH REPORT
# =========================================

@bot.callback_query_handler(func=lambda c: c.data.startswith("result_"))
def send_result(call):

    mode = call.data.split("_", 1)[1]

    msg = bot.send_message(
        call.message.chat.id,
        "📸 Отправь скрин"
    )

    bot.register_next_step_handler(
        msg,
        process_screenshot,
        mode
    )

def process_screenshot(message, mode):

    if not message.photo:

        bot.send_message(
            message.chat.id,
            "❌ Отправь фото"
        )

        return

    file_id = message.photo[-1].file_id

    report_id = random.randint(1000, 9999)

    match_reports[report_id] = {
        "mode": mode,
        "photo": file_id,
        "user_id": message.from_user.id
    }

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "✅ Одобрить",
            callback_data=f"accept_{report_id}"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "❌ Отклонить",
            callback_data=f"reject_{report_id}"
        )
    )

    for admin in ADMINS:

        bot.send_photo(
            admin,
            file_id,
            caption=(
                f"📨 Новый матч\n"
                f"ID: {report_id}\n"
                f"Игрок: {message.from_user.id}\n"
                f"Режим: {mode}"
            ),
            reply_markup=kb
        )

    bot.send_message(
        message.chat.id,
        "✅ Скрин отправлен администрации"
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("accept_"))
def accept_match(call):

    if call.from_user.id not in ADMINS:
        return

    report_id = int(call.data.split("_")[1])

    if report_id not in match_reports:
        return

    report = match_reports[report_id]

    uid = report["user_id"]

    user = get_user(uid)

    new_elo = user[4] + 30
    new_wins = user[7] + 1
    lvl = get_level(new_elo)

    cur.execute(
        "UPDATE users SET elo=?, lvl=?, wins=? WHERE user_id=?",
        (new_elo, lvl, new_wins, uid)
    )

    conn.commit()

    bot.send_message(
        uid,
        "✅ Матч подтверждён\n+30 ELO"
    )

    del match_reports[report_id]

@bot.callback_query_handler(func=lambda c: c.data.startswith("reject_"))
def reject_match(call):

    if call.from_user.id not in ADMINS:
        return

    report_id = int(call.data.split("_")[1])

    if report_id not in match_reports:
        return

    uid = match_reports[report_id]["user_id"]

    bot.send_message(
        uid,
        "❌ Матч отклонён"
    )

    del match_reports[report_id]
    # =========================================
    # START MATCH
    # =========================================

    if ready_count >= total:

        players = lobbies[mode]

        match_text = f"🛡 MATCH FOUND ({mode})\n\n"

        pos = 1

        for player in players:

            u = get_user(player)

            if not u:
                continue

            match_text += f"{pos}. {u[2]}\n"

            pos += 1

        random_map = random.choice(MAPS)

        match_text += f"\n🗺 Карта: {random_map}"
        match_text += "\n\n📸 После игры нажмите кнопку ниже"

        kb_match = types.InlineKeyboardMarkup()

        kb_match.add(
            types.InlineKeyboardButton(
                "✅ Я выиграл",
                callback_data=f"result_{mode}"
            )
        )

        for player in players:

            try:

                bot.send_message(
                    player,
                    match_text,
                    reply_markup=kb_match
                )

            except:
                pass

        lobbies[mode] = []

        ready_matches[mode] = []

# =========================================
# EXIT LOBBY
# =========================================

@bot.message_handler(func=lambda m: m.text == "🚪 Выйти из лобби")
def leave_lobby(message):

    uid = message.from_user.id

    for mode in lobbies:

        if uid in lobbies[mode]:
            lobbies[mode].remove(uid)

    bot.send_message(
        message.chat.id,
        "✅ Вы вышли из лобби",
        reply_markup=main_menu()
    )

# =========================================
# TOP ELO
# =========================================

@bot.message_handler(func=lambda m: m.text == "🏆 Топ ELO")
def top_elo(message):

    cur.execute(
        "SELECT nickname, elo FROM users ORDER BY elo DESC LIMIT 10"
    )

    users = cur.fetchall()

    text = "🏆 ТОП ELO\n\n"

    pos = 1

    for u in users:

        text += f"{pos}. {u[0]} — {u[1]}\n"
        pos += 1

    bot.send_message(message.chat.id, text)

# =========================================
# RUN
# =========================================

bot.remove_webhook()

print("BOT STARTED")

bot.infinity_polling(skip_pending=True)
