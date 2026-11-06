import httpx
import random
import json
import os
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "9246784802:AAHxP96JoEXmjE_nmsWU12Pgm_TmV-LWghM"
WEATHER_API_KEY = "faedfd8d0fe879aab4f6d34c818ccb55"

CAT_IMAGES_BY_LEVEL = {
    0: "https://images.unsplash.com/photo-1519052537078-e6302a4968d4?w=600",
    1: "https://images.unsplash.com/photo-1533738363-b7f9aef128ce?w=600",
    2: "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600",
    3: "https://images.unsplash.com/photo-1518791841217-8f162f1e1131?w=600"
}

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

# Берем просто имя из профиля (без @)
def get_display_name(user):
    if user.first_name:
        return user.first_name
    else:
        return "Безымянный"

def add_experience(user_id, username):
    db = load_data()
    user_id = str(user_id)
    if user_id not in db:
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": username}
    
    db[user_id]["name"] = username

    db[user_id]["exp"] += 1
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

async def show_leaderboard(update: Update):
    db = load_data()
    if not db:
        await update.message.reply_text("Пока никто не играл. Будь первым! 🐱")
        return
        
    # Сортируем по уровню, затем по опыту, затем по количеству кормлений
    sorted_users = sorted(db.items(), key=lambda x: (x[1].get('level', 0), x[1].get('exp', 0), x[1].get('total_fed', 0)), reverse=True)
    
    text = "🏆 <b>Топ игроков (Короли дивана):</b>\n\n"
    for i, (uid, data) in enumerate(sorted_users[:5], 1):
        name = data.get('name', 'Безымянный')
        level = data.get('level', 0)
        fed = data.get('total_fed', 0)
        text += f"{i}. <b>{name}</b> — {get_level_name(level)}, 🐟 {fed}\n"
        
    await update.message.reply_text(text, parse_mode="HTML")

async def feed_cat(update: Update):
    user_id = str(update.effective_user.id)
    username = get_display_name(update.effective_user)
    db = load_data()
    if user_id not in db:
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": username}
        
    last_fed = db[user_id].get("last_fed", 0)
    time_passed = datetime.now().timestamp() - last_fed

    if time_passed < 300:
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
    username = get_display_name(update.effective_user)
    db = load_data()
    if user_id not in db:
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": username}
        save_data(db)
        
    data = db[user_id]
    level = data["level"]
    exp = data["exp"]
    total_fed = data.get("total_fed", 0)
    next_exp = LEVEL_UP_EXP.get(level, "MAX")
    
    text = (
        f"📊 <b>Твоя статистика:</b>\n\n"
        f"👤 Имя: <b>{data.get('name')}</b>\n"
        f"🐱 Уровень: {get_level_name(level)}\n"
        f"✨ Опыт: {exp}/{next_exp}\n"
        f"🐟 Всего съедено вкусняшек: {total_fed}\n\n"
    )
    if level < 3:
        text += f"До следующего уровня осталось получить {next_exp - exp} опыта!"

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
        level, exp, leveled_up = add_experience(update.effective_user.id, username)
        cat_image = CAT_IMAGES_BY_LEVEL.get(level, CAT_IMAGES_BY_LEVEL[0])
        weather_tip = WEATHER_TIPS.get(main_weather, WEATHER_TIPS["Default"])
        
        user_id = str(update.effective_user.id)
        db = load_data()
        last_fed = db[user_id].get("last_fed", 0)
        time_passed = datetime.now().timestamp() - last_fed
        
        hunger_status = ""
        if time_passed > 7200:
            hunger_status = "\n\n😿 <b>Мяу... Я очень голодный! Нажми 'Покормить котика'!</b>"
            cat_phrase = "Мяу-у-у... Дай мне рыбку, пожалуйста..."
        else:
            cat_phrase = get_cat_phrase(main_weather, level)

        level_up_text = ""
        if leveled_up:
            level_up_text = f"\n\n🎉 <b>Поздравляю! Твой котик вырос до уровня {get_level_name(level)}!</b>"

        next_level_exp = LEVEL_UP_EXP.get(level, "Максимум")
        exp_text = f"✨ Опыт: {exp}/{next_level_exp}" if level < 3 else "✨ Опыт: MAX"

        caption = (
            f"🌍 Погода в <b>{data['name']}</b>: {temp}°C, {desc}\n"
            f"{get_advice(temp)}\n"
            f"{weather_tip}\n\n"
            f"🐱 <b>Твой питомец (Ур. {level} - {get_level_name(level)}):</b>\n"
            f"<i>{cat_phrase}</i>{hunger_status}{level_up_text}\n\n"
            f"{exp_text}"
        )
        
        try:
            await update.message.reply_photo(photo=cat_image, caption=caption, parse_mode="HTML")
        except Exception:
            await update.message.reply_text(caption, parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Город не найден. Проверь название.")

async def prediction(update: Update):
    username = get_display_name(update.effective_user)
    add_experience(update.effective_user.id, username)
    pred = random.choice(PREDICTIONS)
    caption = f"🐱 <b>Кот-предсказатель:</b>\n\n<i>{pred}</i>"
    try:
        await update.message.reply_photo(photo="https://images.unsplash.com/photo-1519052537078-e6302a4968d4?w=600", caption=caption, parse_mode="HTML")
    except Exception:
        await update.message.reply_text(caption, parse_mode="HTML")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if context.user_data.get('last_action') == text:
        return
    context.user_data['last_action'] = text
    
    if "покормить" in text.lower():
        await feed_cat(update)
        return
        
    if "предсказание" in text.lower():
        await prediction(update)
        return
        
    if "статистика" in text.lower():
        await show_stats(update)
        return

    if "топ" in text.lower():
        await show_leaderboard(update)
        return
        
    if text.startswith("🐱") or "Мяу" in text:
        await update.message.reply_text("Муррр! Спасибо тебе! 😽 Ты лучший хозяин на свете!")
        return
        
    context.user_data['last_city'] = text
    await get_weather(update, city=text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = get_display_name(update.effective_user)
    db = load_data()
    if user_id not in db:
        db[user_id] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": username}
        save_data(db)
        
    keyboard = [
        [KeyboardButton("🐟 Покормить котика"), KeyboardButton("🔮 Предсказание")],
        [KeyboardButton("📊 Моя статистика"), KeyboardButton("🏆 Топ игроков")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! 👋\nНапиши название города, и я пришлю погоду и покажу твоего питомца 🐱\n\n"
        "Соревнуйся с друзьями! Смотри «🏆 Топ игроков» и качай своего котика!",
        reply_markup=reply_markup
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
