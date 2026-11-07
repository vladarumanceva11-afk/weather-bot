import httpx
import random
import json
import os
from datetime import datetime, time
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TELEGRAM_TOKEN = "9246784802:AAHxP96JoEXmjE_nmsWU12Pgm_TmV-LWghM"
WEATHER_API_KEY = "faedfd8d0fe879aab4f6d34c818ccb55"
CHANNEL_USERNAME = "@murchashaya_pogoda"

# --- ФЕЙКОВЫЙ СЕРВЕР ДЛЯ RENDER ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()
# ----------------------------------

CAT_IMAGES_BY_LEVEL = {
    0: "https://images.unsplash.com/photo-1519052537078-e6302a4968d4?w=600",
    1: "https://images.unsplash.com/photo-1533738363-b7f9aef128ce?w=600",
    2: "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600",
    3: "https://images.unsplash.com/photo-1518791841217-8f162f1e1131?w=600"
}

FACTS = [
    "Знаете ли вы, что самая низкая температура на Земле была зафиксирована в Антарктиде: -89.2°C? 🥶",
    "Коты могут спать до 16 часов в сутки. Погода к этому очень располагает! 😴",
    "Молния бьет в Землю около 100 раз в секунду! ⚡️",
    "Самая высокая температура в России была в Калмыкии: +45.4°C. 🔥",
    "Дождевые капли падают со скоростью около 9 метров в секунду. ☔️",
    "Снежинки на 95% состоят из воздуха, поэтому падают так медленно. ❄️",
    "Радуга на самом деле имеет форму круга, мы просто видим только ее часть. 🌈",
    "Коты отлично чувствуют смену погоды. Если кот спит клубком — жди похолодания! 🐱",
    "В пустыне Атакама (Чили) дождей не было более 400 лет. 🌵",
    "Уши кота могут поворачиваться на 180 градусов, чтобы лучше слышать. 👂"
]

# Новые вечерние фразы
EVENING_PHRASES = [
    "Пусть твой вечер будет таким же уютным, как клубок пряжи. 🧶🐾",
    "Время снять усталость и обнять котика. Хорошего вечера! 🌙",
    "За окном вечер, а значит пора пить чай и отдыхать. ☕️🐱",
    "Пусть сегодняшний вечер принесет спокойствие и тепло. ✨",
    "Котик уже свернулся калачиком. А ты готов отдохнуть? 💤",
    "Отличный повод закончить дела пораньше и полежать в обнимку с любимцем. 🐈"
]

CAT_PHRASES = {
    "Clear": ["Мяу! Солнце светит, я греюсь на подоконнике! ☀️🐈", "Ура, гулять! Пойдем ловить бабочек? 🦋🐾"],
    "Clouds": ["Мяу... Пасмурно. Я лучше посплю на твоих коленях. 😴☁️", "Хмурое небо, но мне всё равно тепло рядом с тобой. 🐱💤"],
    "Rain": ["Мррр... Дождь. Я не пойду гулять, буду смотреть в окно. 🌧🐾", "Мяу! Дождик, давай пить чай с молоком? 🍵🐱"],
    "Snow": ["Мяу! Холодно! Шапку мне, шапку! ❄️🧣🐈", "Снег! Я зарываюсь в плед и не выйду оттуда до весны. ⛄️🐱"],
    "Default": ["Мяу! Накорми меня, пожалуйста! 🐾", "Я сегодня самый милый кот на свете, погладь меня! 🐱✨"]
}

PREDICTIONS = [
    "🔮 Сегодня звёзды говорят: тебе повезёт! Улыбнись!",
    "🔮 Мой хвост говорит, что сегодня отличный день для новых знакомств!",
    "🔮 Мурр... Судя по моим усам, сегодня тебя ждет что-то приятное!",
    "🔮 Предсказание дня: не забудь погладить кота! Это принесёт удачу!",
    "🔮 Сегодня твой день! Верь в себя, и всё получится!"
]

WEATHER_TIPS = {
    "Clear": "Совет дня: не забудь надеть головной убор! 🧢",
    "Clouds": "Совет дня: отличная погода для прогулки! 🍂",
    "Rain": "Совет дня: возьми зонт и надень непромокаемую обувь! ☔️",
    "Snow": "Совет дня: одевайся слоями, чтобы было тепло! 🧣",
    "Default": "Совет дня: пей больше воды и улыбайся! 😊"
}

DAILY_BONUSES = [
    "Держи виртуальную рыбку! 🐟",
    "Вот тебе клубок пряжи для игр! 🧶",
    "Поздравляю, ты получаешь статус 'Лучший хозяин дня'! 🏆",
    "Мой хвост виляет от счастья, что ты зашла! 🐾",
    "Дарю тебе мурчание на весь день! 😽"
]

LEVEL_UP_EXP = {0: 10, 1: 30, 2: 70, 3: 9999}
DB_FILE = "cat_data.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def get_display_name(user):
    return user.first_name if user.first_name else "Хозяин"

async def check_subscription(user_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        return True

async def add_experience(user_id, username, amount=1):
    db = load_data()
    user_id = str(user_id)
    if user_id not in db:
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": username, "last_bonus": 0}
    db[user_id]["name"] = username
    db[user_id]["exp"] += amount
    current_level = db[user_id]["level"]
    if current_level < 3 and db[user_id]["exp"] >= LEVEL_UP_EXP[current_level]:
        db[user_id]["level"] += 1
        db[user_id]["exp"] = 0
    save_data(db)
    return db[user_id]["level"], db[user_id]["exp"], current_level != db[user_id]["level"]

def get_level_name(level):
    names = ["🐣 Котенок", "🐱 Подросток", "🐈 Взрослый Кот", "👑 Король дивана"]
    return names[level]

def get_cat_phrase(main_weather, level):
    if level == 3:
        return "Мяу. Я король. Принеси мне рыбу, простолюдин. 👑🐾"
    return random.choice(CAT_PHRASES.get(main_weather, CAT_PHRASES["Default"]))

def get_advice(temp):
    if temp <= 0: return "🧥 Очень холодно, наденьте пуховик и шапку!"
    elif temp <= 10: return "🧥 Прохладно, лучше надеть куртку."
    elif temp <= 18: return "🧥 Свежо, возьмите кофту или ветровку."
    elif temp <= 25: return "👕 Тепло, можно в футболке."
    else: return "🩳 Жарко, пейте больше воды!"

# --- УТРЕННЯЯ РАССЫЛКА ---
async def send_daily_fact(context: ContextTypes.DEFAULT_TYPE):
    fact = random.choice(FACTS)
    text = f"🌅 <b>Доброе утро!</b>\n\n<b>Факт дня:</b>\n<i>{fact}</i>\n\nХорошего вам дня! 🐱"
    try:
        await context.bot.send_photo(chat_id=CHANNEL_USERNAME, photo="https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600", caption=text, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка: {e}")

# --- ВЕЧЕРНЯЯ РАССЫЛКА ---
async def send_evening_message(context: ContextTypes.DEFAULT_TYPE):
    phrase = random.choice(EVENING_PHRASES)
    text = f"🌙 <b>Добрый вечер!</b>\n\n<i>{phrase}</i>\n\nСладких снов! 🐾"
    try:
        await context.bot.send_photo(chat_id=CHANNEL_USERNAME, photo="https://images.unsplash.com/photo-1519052537078-e6302a4968d4?w=600", caption=text, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка: {e}")

async def daily_bonus(update: Update):
    user_id = str(update.effective_user.id)
    username = get_display_name(update.effective_user)
    db = load_data()
    if user_id not in db:
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": username, "last_bonus": 0}
    last_bonus = db[user_id].get("last_bonus", 0)
    now = datetime.now().timestamp()
    if now - last_bonus < 86400:
        time_left = 86400 - (now - last_bonus)
        await update.message.reply_text(f"Мяу! Ты уже получала бонус сегодня. Приходи через {int(time_left // 3600)} ч. {int((time_left % 3600) // 60)} мин. 🕰")
        return
    db[user_id]["last_bonus"] = now
    save_data(db)
    await add_experience(user_id, username, 2)
    bonus_text = random.choice(DAILY_BONUSES)
    caption = f"🎁 <b>Ежедневный бонус получен!</b>\n\n{bonus_text}\n\n✨ Ты получаешь <b>+2 опыта</b> для своего котика!"
    try:
        await update.message.reply_photo(photo="https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600", caption=caption, parse_mode="HTML")
    except Exception:
        await update.message.reply_text(caption, parse_mode="HTML")

async def show_leaderboard(update: Update):
    db = load_data()
    if not db:
        await update.message.reply_text("Пока никто не играл. Будь первым! 🐱")
        return
    sorted_users = sorted(db.items(), key=lambda x: (x[1].get('level', 0), x[1].get('exp', 0), x[1].get('total_fed', 0)), reverse=True)
    text = "🏆 <b>Топ игроков:</b>\n\n"
    for i, (uid, data) in enumerate(sorted_users[:5], 1):
        text += f"{i}. <b>{data.get('name')}</b> — {get_level_name(data.get('level', 0))}, 🐟 {data.get('total_fed', 0)}\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def feed_cat(update: Update):
    user_id = str(update.effective_user.id)
    db = load_data()
    if user_id not in db:
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": get_display_name(update.effective_user), "last_bonus": 0}
    if datetime.now().timestamp() - db[user_id].get("last_fed", 0) < 300:
        await update.message.reply_text("Мяу! Я уже сыт, но спасибо! 😸 Не перекорми меня!")
        return
    db[user_id]["last_fed"] = datetime.now().timestamp()
    db[user_id]["total_fed"] = db[user_id].get("total_fed", 0) + 1
    save_data(db)
    caption = "😻 <b>Муррр! Спасибо за вкусняшку!</b>\nЯ всё съел и теперь довольный сплю. 💤🐾"
    try:
        await update.message.reply_photo(photo="https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600", caption=caption, parse_mode="HTML")
    except Exception:
        await update.message.reply_text(caption, parse_mode="HTML")

async def show_stats(update: Update):
    user_id = str(update.effective_user.id)
    db = load_data()
    if user_id not in db:
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": get_display_name(update.effective_user), "last_bonus": 0}
        save_data(db)
    data = db[user_id]
    level = data["level"]
    next_exp = LEVEL_UP_EXP.get(level, "MAX")
    text = f"📊 <b>Твоя статистика:</b>\n\n👤 Имя: <b>{data.get('name')}</b>\n🐱 Уровень: {get_level_name(level)}\n✨ Опыт: {data['exp']}/{next_exp}\n🐟 Съедено вкусняшек: {data.get('total_fed', 0)}"
    await update.message.reply_text(text, parse_mode="HTML")

async def get_weather(update: Update, city=None):
    params = {"appid": WEATHER_API_KEY, "q": city, "units": "metric", "lang": "ru"}
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.openweathermap.org/data/2.5/weather", params=params)
    if r.status_code == 200:
        data = r.json()
        temp = round(data['main']['temp'])
        desc = data['weather'][0]['description'].capitalize()
        main_weather = data['weather'][0]['main']
        
        username = get_display_name(update.effective_user)
        level, exp, leveled_up = await add_experience(update.effective_user.id, username)
        cat_image = CAT_IMAGES_BY_LEVEL.get(level, CAT_IMAGES_BY_LEVEL[0])
        
        user_id = str(update.effective_user.id)
        db = load_data()
        time_passed = datetime.now().timestamp() - db[user_id].get("last_fed", 0)
        
        hunger_status = "\n\n😿 <b>Мяу... Я очень голодный!</b>" if time_passed > 7200 else ""
        cat_phrase = "Мяу-у-у... Дай мне рыбку..." if time_passed > 7200 else get_cat_phrase(main_weather, level)
        level_up_text = f"\n\n🎉 <b>Поздравляю! Твой котик вырос до уровня {get_level_name(level)}!</b>" if leveled_up else ""
        exp_text = f"✨ Опыт: {exp}/{LEVEL_UP_EXP.get(level, 'MAX')}" if level < 3 else "✨ Опыт: MAX"

        caption = (
            f"🌍 Погода в <b>{data['name']}</b>: {temp}°C, {desc}\n"
            f"{get_advice(temp)}\n"
            f"{WEATHER_TIPS.get(main_weather, WEATHER_TIPS['Default'])}\n\n"
            f"🐱 <b>Твой питомец (Ур. {level} - {get_level_name(level)}):</b>\n"
            f"<i>{cat_phrase}</i>{hunger_status}{level_up_text}\n\n{exp_text}"
        )
        try:
            await update.message.reply_photo(photo=cat_image, caption=caption, parse_mode="HTML")
        except Exception:
            await update.message.reply_text(caption, parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Город не найден.")

async def prediction(update: Update):
    await add_experience(update.effective_user.id, get_display_name(update.effective_user))
    pred = random.choice(PREDICTIONS)
    caption = f"🐱 <b>Кот-предсказатель:</b>\n\n<i>{pred}</i>"
    try:
        await update.message.reply_photo(photo="https://images.unsplash.com/photo-1519052537078-e6302a4968d4?w=600", caption=caption, parse_mode="HTML")
    except Exception:
        await update.message.reply_text(caption, parse_mode="HTML")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not await check_subscription(update.effective_user.id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")], [InlineKeyboardButton("✅ Я подписался", callback_data="check_sub")]]
        await update.message.reply_text("Мяу! Подпишись на наш канал! 👇", reply_markup=InlineKeyboardMarkup(keyboard))
        return
        
    if "покормить" in text.lower(): await feed_cat(update)
    elif "предсказание" in text.lower(): await prediction(update)
    elif "статистика" in text.lower(): await show_stats(update)
    elif "топ" in text.lower(): await show_leaderboard(update)
    elif "бонус" in text.lower(): await daily_bonus(update)
    elif "погода" in text.lower(): 
        await update.message.reply_text("🌍 Напиши название города, и я пришлю погоду и котика!")
    elif "ещё" in text.lower() or "меню" in text.lower():
        keyboard = [
            [KeyboardButton("🔮 Предсказание"), KeyboardButton("📊 Статистика")],
            [KeyboardButton("🏆 Топ игроков"), KeyboardButton("⬅️ Назад")]
        ]
        await update.message.reply_text("🎮 Дополнительное меню:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    elif "назад" in text.lower():
        keyboard = [
            [KeyboardButton("🌍 Погода"), KeyboardButton("🐟 Покормить котика")],
            [KeyboardButton("🎁 Ежедневный бонус"), KeyboardButton("🎮 Ещё")]
        ]
        await update.message.reply_text("Главное меню:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    elif text.startswith("🐱") or "Мяу" in text: await update.message.reply_text("Муррр! Спасибо тебе! 😽")
    else:
        context.user_data['last_city'] = text
        await get_weather(update, city=text)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check_sub":
        if await check_subscription(update.effective_user.id, context):
            await query.edit_message_text("✅ Спасибо за подписку! Теперь напиши город, и я покажу погоду 🐱")
        else:
            await query.edit_message_text("❌ Ты ещё не подписался.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_data()
    if user_id not in db:
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": get_display_name(update.effective_user), "last_bonus": 0}
        save_data(db)

    if not await check_subscription(update.effective_user.id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")], [InlineKeyboardButton("✅ Я подписался", callback_data="check_sub")]]
        await update.message.reply_text("Привет! Чтобы пользоваться ботом, подпишись на наш канал! 👇", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    keyboard = [
        [KeyboardButton("🌍 Погода"), KeyboardButton("🐟 Покормить котика")],
        [KeyboardButton("🎁 Ежедневный бонус"), KeyboardButton("🎮 Ещё")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! 👋 Добро пожаловать в «Мурчащую погоду»! 🌤🐱\n\n"
        "Жми на кнопку «🌍 Погода», чтобы узнать прогноз, или выбери другую кнопку ниже!",
        reply_markup=reply_markup
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    job_queue = app.job_queue
    # Утренний факт в 8:00 по твоему времени (5:00 UTC)
    job_queue.run_daily(send_daily_fact, time=time(hour=5, minute=0))
    
    # Вечернее сообщение в 20:00 по твоему времени (17:00 UTC)
    job_queue.run_daily(send_evening_message, time=time(hour=17, minute=0))
    
    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
