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

# Костюмы (включая секретный)
SKINS = {
    "default": {"name": "Дворовый", "price": 0, "image": "https://images.unsplash.com/photo-1519052537078-e6302a4968d4?w=600"},
    "gentleman": {"name": "Джентльмен", "price": 500, "image": "https://images.unsplash.com/photo-1533738363-b7f9aef128ce?w=600"},
    "astronaut": {"name": "Космонавт", "price": 1500, "image": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600"},
    "mafia": {"name": "Мафиози", "price": 5000, "image": "https://images.unsplash.com/photo-1518791841217-8f162f1e1131?w=600"},
    "emperor": {"name": "Император 👑", "price": 10000, "image": "https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=600"},
    "secret": {"name": "??? (В разработке)", "price": 99999, "image": "https://images.unsplash.com/photo-1519052537078-e6302a4968d4?w=600"} 
}

# Взрослые факты
FACTS = [
    "Знаете ли вы, что скорость звука в воздухе составляет около 343 м/с?",
    "Атмосферное давление на уровне моря составляет 760 мм рт. ст. Если оно падает — жди перемены погоды.",
    "Самая высокая температура на Земле: +56.7°C (Долина Смерти, США).",
    "Кучевые облака могут весить более 500 тонн.",
    "Радуга образуется из-за преломления света в каплях воды.",
    "В Антарктиде находится 90% всего льда на планете.",
    "Молния разогревает воздух до 30 000°C.",
    "Самый сухой континент — Австралия."
]

# Взрослые вечерние мысли
EVENING_PHRASES = [
    "Вечер — это время, когда можно наконец выдохнуть и заняться собой.",
    "Пусть этот вечер пройдет в тишине и спокойствии. Вы это заслужили.",
    "Иногда лучший способ перезагрузиться — это просто выспаться.",
    "Спокойствие — это роскошь, которую мы можем себе позволить.",
    "За окном темнеет. Отличный повод закончить работу.",
    "Не забывайте: даже самая длинная рабочая неделя заканчивается."
]

CAT_PHRASES = {
    "Clear": ["Солнце светит, птички поют. Я, пожалуй, вздремну на подоконнике. ☀️🐈", "Отличная погода, чтобы выбраться из берлоги и выпить кофе на веранде. 🦋🐾"],
    "Clouds": ["Пасмурно. Идеальное время для умных мыслей и сна. 😴☁️", "Серое небо, но мой вязаный плед все еще в деле. 🐱💤"],
    "Rain": ["Дождь стучит по крыше. С удовольствием составлю компанию за чашкой чая. 🌧🐾", "Мяу. Отличная погода для просмотра сериала. 🍵🐱"],
    "Snow": ["Холодно. Убедительная просьба: шапку мне и тебе. ❄️🧣🐈", "Снег на улице. Я в домике. Разбудите меня весной. ⛄️🐱"],
    "Default": ["Я не сплю, я медитирую и набираюсь опыта. 🐾", "Погода сегодня философская. Как и я. Погладь. 🐱✨"]
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

LEVEL_UP_EXP = {0: 50, 1: 150, 2: 400, 3: 9999}
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
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": username, "last_bonus": 0, "coins": 0, "skin": "default"}
    
    db[user_id]["coins"] = db[user_id].get("coins", 0) + amount 
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

async def send_daily_fact(context: ContextTypes.DEFAULT_TYPE):
    fact = random.choice(FACTS)
    text = f"🌅 <b>Доброе утро.</b>\n\n<b>Факт дня:</b>\n<i>{fact}</i>\n\nХорошего дня."
    try:
        await context.bot.send_photo(chat_id=CHANNEL_USERNAME, photo="https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600", caption=text, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка: {e}")

async def send_evening_message(context: ContextTypes.DEFAULT_TYPE):
    phrase = random.choice(EVENING_PHRASES)
    text = f"🌙 <b>Добрый вечер.</b>\n\n<i>{phrase}</i>\n\nСпокойной ночи."
    try:
        await context.bot.send_photo(chat_id=CHANNEL_USERNAME, photo="https://images.unsplash.com/photo-1519052537078-e6302a4968d4?w=600", caption=text, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка: {e}")

async def show_wardrobe(update: Update):
    user_id = str(update.effective_user.id)
    db = load_data()
    if user_id not in db:
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": get_display_name(update.effective_user), "last_bonus": 0, "coins": 0, "skin": "default"}
        save_data(db)
    
    user_coins = db[user_id].get("coins", 0)
    current_skin = db[user_id].get("skin", "default")
    
    keyboard = []
    for skin_id, skin_data in SKINS.items():
        if skin_id == current_skin:
            keyboard.append([InlineKeyboardButton(f"✅ {skin_data['name']} (Надето)", callback_data="noop")])
        elif skin_id == "secret":
            keyboard.append([InlineKeyboardButton(f"🔒 {skin_data['name']}", callback_data="secret_info")])
        else:
            keyboard.append([InlineKeyboardButton(f"{skin_data['name']} - {skin_data['price']} 🐟", callback_data=f"buy_{skin_id}")])
            
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🎨 <b>Гардероб котика</b>\n\n"
        f"У тебя на счету: <b>{user_coins} 🐟</b>\n"
        f"Выбери, что надеть:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("buy_"):
        skin_id = query.data.replace("buy_", "")
        user_id = str(update.effective_user.id)
        db = load_data()
        
        if user_id not in db:
            return
            
        skin_price = SKINS[skin_id]["price"]
        user_coins = db[user_id].get("coins", 0)
        
        if user_coins >= skin_price:
            db[user_id]["coins"] -= skin_price
            db[user_id]["skin"] = skin_id
            save_data(db)
            await query.edit_message_text(f"✅ Отлично! Ты купил шубку «{SKINS[skin_id]['name']}». Теперь твой котик выглядит стильно! (Остаток: {db[user_id]['coins']} 🐟)")
        else:
            await query.edit_message_text(f"❌ Недостаточно рыбок! Нужно {skin_price} 🐟, а у тебя только {user_coins} 🐟.")
    
    elif query.data == "secret_info":
        await query.answer("🔒 Секретный костюм в разработке. Приглашай друзей, чтобы открыть его быстрее!", show_alert=True)
    
    elif query.data == "noop":
        await query.answer("Эта шубка уже надета!")
        return

    if query.data == "check_sub":
        if await check_subscription(update.effective_user.id, context):
            await query.edit_message_text("✅ Спасибо за подписку! Теперь напиши город.")
        else:
            await query.edit_message_text("❌ Ты ещё не подписался.")

async def daily_bonus(update: Update):
    user_id = str(update.effective_user.id)
    username = get_display_name(update.effective_user)
    db = load_data()
    if user_id not in db:
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": username, "last_bonus": 0, "coins": 0, "skin": "default"}
    last_bonus = db[user_id].get("last_bonus", 0)
    now = datetime.now().timestamp()
    if now - last_bonus < 86400:
        time_left = 86400 - (now - last_bonus)
        await update.message.reply_text(f"Ты уже получал бонус сегодня. Приходи через {int(time_left // 3600)} ч. {int((time_left % 3600) // 60)} мин. 🕰")
        return
    db[user_id]["last_bonus"] = now
    save_data(db)
    await add_experience(user_id, username, 3)
    bonus_text = random.choice(DAILY_BONUSES)
    caption = f"🎁 <b>Ежедневный бонус получен!</b>\n\n{bonus_text}\n\n✨ Ты получаешь <b>+3 опыта</b> и <b>+3 рыбки 🐟</b>!"
    try:
        current_skin = db[user_id].get("skin", "default")
        await update.message.reply_photo(photo=SKINS[current_skin]["image"], caption=caption, parse_mode="HTML")
    except Exception:
        await update.message.reply_text(caption, parse_mode="HTML")

async def show_leaderboard(update: Update):
    db = load_data()
    if not db:
        await update.message.reply_text("Пока никто не играл. Будь первым!")
        return
    sorted_users = sorted(db.items(), key=lambda x: (x[1].get('level', 0), x[1].get('exp', 0), x[1].get('total_fed', 0)), reverse=True)
    text = "🏆 <b>Топ игроков:</b>\n\n"
    for i, (uid, data) in enumerate(sorted_users[:5], 1):
        text += f"{i}. <b>{data.get('name')}</b> — {get_level_name(data.get('level', 0))}, 🐟 {data.get('total_fed', 0)}\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def feed_cat(update: Update):
    user_id = str(update.effective_user.id)
    username = get_display_name(update.effective_user)
    db = load_data()
    if user_id not in db:
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": username, "last_bonus": 0, "coins": 0, "skin": "default"}
    if datetime.now().timestamp() - db[user_id].get("last_fed", 0) < 300:
        await update.message.reply_text("Я уже сыт. Не перекармливай, пожалуйста. 😸")
        return
    db[user_id]["last_fed"] = datetime.now().timestamp()
    db[user_id]["total_fed"] = db[user_id].get("total_fed", 0) + 1
    save_data(db)
    
    await add_experience(user_id, username, 2)
    
    caption = "😻 <b>Спасибо. Было вкусно.</b>\nПойду вздремну, разбудишь, если что. 💤\n\n✨ Ты получаешь <b>+2 опыта</b> и <b>+2 рыбки 🐟</b>."
    try:
        current_skin = db[user_id].get("skin", "default")
        await update.message.reply_photo(photo=SKINS[current_skin]["image"], caption=caption, parse_mode="HTML")
    except Exception:
        await update.message.reply_text(caption, parse_mode="HTML")

async def show_stats(update: Update):
    user_id = str(update.effective_user.id)
    db = load_data()
    if user_id not in db:
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": get_display_name(update.effective_user), "last_bonus": 0, "coins": 0, "skin": "default"}
        save_data(db)
    data = db[user_id]
    level = data["level"]
    next_exp = LEVEL_UP_EXP.get(level, "MAX")
    text = f"📊 <b>Твоя статистика:</b>\n\n👤 Имя: <b>{data.get('name')}</b>\n🐱 Уровень: {get_level_name(level)}\n✨ Опыт: {data['exp']}/{next_exp}\n🐟 Рыбок: {data.get('coins', 0)}\n🐾 Съедено вкусняшек: {data.get('total_fed', 0)}"
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
        level, exp, leveled_up = await add_experience(update.effective_user.id, username, 1)
        
        user_id = str(update.effective_user.id)
        db = load_data()
        current_skin = db[user_id].get("skin", "default")
        cat_image = SKINS[current_skin]["image"]
        
        time_passed = datetime.now().timestamp() - db[user_id].get("last_fed", 0)
        
        hunger_status = "\n\n😿 <b>Кстати, я голоден. Это намек.</b>" if time_passed > 7200 else ""
        cat_phrase = "Я голоден. Покорми, и я продолжу медитировать..." if time_passed > 7200 else get_cat_phrase(main_weather, level)
        level_up_text = f"\n\n🎉 <b>Мои поздравления. Я вырос до уровня {get_level_name(level)}.</b>" if leveled_up else ""
        exp_text = f"✨ Опыт: {exp}/{LEVEL_UP_EXP.get(level, 'MAX')}" if level < 3 else "✨ Опыт: MAX"
        coins_text = f"🐟 Рыбок: {db[user_id].get('coins', 0)}"

        caption = (
            f"🌍 <b>{data['name']}</b>: {temp}°C, {desc}\n"
            f"{get_advice(temp)}\n"
            f"{WEATHER_TIPS.get(main_weather, WEATHER_TIPS['Default'])}\n\n"
            f"🐱 <b>Мой статус (Ур. {level} - {get_level_name(level)}):</b>\n"
            f"<i>{cat_phrase}</i>{hunger_status}{level_up_text}\n\n{exp_text}\n{coins_text}"
        )
        try:
            await update.message.reply_photo(photo=cat_image, caption=caption, parse_mode="HTML")
        except Exception:
            await update.message.reply_text(caption, parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Город не найден.")

async def prediction(update: Update):
    await add_experience(update.effective_user.id, get_display_name(update.effective_user), 1)
    pred = random.choice(PREDICTIONS)
    caption = f"🐱 <b>Кот-предсказатель:</b>\n\n<i>{pred}</i>"
    try:
        user_id = str(update.effective_user.id)
        db = load_data()
        current_skin = db[user_id].get("skin", "default")
        await update.message.reply_photo(photo=SKINS[current_skin]["image"], caption=caption, parse_mode="HTML")
    except Exception:
        await update.message.reply_text(caption, parse_mode="HTML")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    
    if not await check_subscription(update.effective_user.id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")], [InlineKeyboardButton("✅ Я подписался", callback_data="check_sub")]]
        await update.message.reply_text("Для начала неплохо бы подписаться на наш канал. 👇", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    greetings = ["привет", "здравствуй", "хай", "добрый день", "добрый вечер", "доброе утро", "приветик"]
    if any(word in text for word in greetings):
        await update.message.reply_text(f"Приветствую, {get_display_name(update.effective_user)}. Чем займемся? Узнаем погоду или займемся прокачкой? 🐱")
        return
    if "как дела" in text:
        await update.message.reply_text("Всё в порядке. Наслаждаюсь покоем. А у тебя? 😸")
        return
    if "спасибо" in text or "благодарю" in text:
        await update.message.reply_text("Не за что. Обращайся. 😽")
        return
    if "пока" in text or "до свидания" in text:
        await update.message.reply_text("До встречи. Не забывай меня. 🐾")
        return

    if "покормить" in text: await feed_cat(update)
    elif "предсказание" in text: await prediction(update)
    elif "статистика" in text: await show_stats(update)
    elif "топ" in text: await show_leaderboard(update)
    elif "бонус" in text: await daily_bonus(update)
    elif "гардероб" in text or "шубка" in text: await show_wardrobe(update)
    elif "погода" in text: 
        await update.message.reply_text("Какой город тебя интересует?")
    elif "ещё" in text or "меню" in text:
        keyboard = [
            [KeyboardButton("🔮 Предсказание"), KeyboardButton("📊 Статистика")],
            [KeyboardButton("🎨 Гардероб"), KeyboardButton("🏆 Топ игроков")],
            [KeyboardButton("⬅️ Назад")]
        ]
        await update.message.reply_text("Дополнительные опции:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    elif "назад" in text:
        keyboard = [
            [KeyboardButton("🌍 Погода"), KeyboardButton("🐟 Покормить котика")],
            [KeyboardButton("🎁 Ежедневный бонус"), KeyboardButton("🎮 Ещё")]
        ]
        await update.message.reply_text("Главное меню:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    elif text.startswith("🐱") or "мяу" in text: await update.message.reply_text("Мурр. 😽")
    else:
        context.user_data['last_city'] = update.message.text
        await get_weather(update, city=update.message.text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_data()
    if user_id not in db:
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": get_display_name(update.effective_user), "last_bonus": 0, "coins": 0, "skin": "default"}
        save_data(db)

    if not await check_subscription(update.effective_user.id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")], [InlineKeyboardButton("✅ Я подписался", callback_data="check_sub")]]
        await update.message.reply_text("Добро пожаловать. Для начала подпишись на наш канал. 👇", reply_markup=InlineKeyboar
