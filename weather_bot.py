import httpx
import random
import json
import os
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "9246784802:AAHxP96JoEXmjE_nmsWU12Pgm_TmV-LWghM"
WEATHER_API_KEY = "faedfd8d0fe879aab4f6d34c818ccb55"

# Картинки для котика
CAT_IMAGES = {
    "Clear": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600",
    "Clouds": "https://images.unsplash.com/photo-1533738363-b7f9aef128ce?w=600",
    "Rain": "https://images.unsplash.com/photo-1548247416-ec66f4900b2e?w=600",
    "Snow": "https://images.unsplash.com/photo-1518791841217-8f162f1e1131?w=600",
    "Default": "https://images.unsplash.com/photo-1519052537078-e6302a4968d4?w=600"
}

# Фразы котика
CAT_PHRASES = {
    "Clear": ["Мяу! Солнце светит, я греюсь на подоконнике! ☀️🐈", "Ура, гулять! Пойдем ловить бабочек? 🦋🐾"],
    "Clouds": ["Мяу... Пасмурно. Я лучше посплю на твоих коленях. 😴☁️", "Хмурое небо, но мне всё равно тепло рядом с тобой. 🐱💤"],
    "Rain": ["Мррр... Дождь. Я не пойду гулять, буду смотреть в окно. 🌧🐾", "Мяу! Дождик, давай пить чай с молоком? 🍵🐱"],
    "Snow": ["Мяу! Холодно! Шапку мне, шапку! ❄️🧣🐈", "Снег! Я зарываюсь в плед и не выйду оттуда до весны. ⛄️🐱"],
    "Default": ["Мяу! Накорми меня, пожалуйста! 🐾", "Я сегодня самый милый кот на свете, погладь меня! 🐱✨"]
}

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

def get_cat_phrase(main_weather):
    return random.choice(CAT_PHRASES.get(main_weather, CAT_PHRASES["Default"]))

def get_advice(temp):
    if temp <= 0: return "🧥 Очень холодно, наденьте пуховик и шапку!"
    elif temp <= 10: return "🧥 Прохладно, лучше надеть куртку."
    elif temp <= 18: return "🧥 Свежо, возьмите кофту или ветровку."
    elif temp <= 25: return "👕 Тепло, можно в футболке."
    else: return "🩳 Жарко, пейте больше воды и не забудьте панамку!"

# Функция кормления
async def feed_cat(update: Update):
    user_id = str(update.effective_user.id)
    db = load_data()
    last_fed = db.get(user_id, 0)
    time_passed = datetime.now().timestamp() - last_fed

    if time_passed < 300: # Если кормили меньше 5 минут назад
        await update.message.reply_text("Мяу! Я уже сыт, но спасибо! 😸 Не перекорми меня!")
        return
        
    db[user_id] = datetime.now().timestamp()
    save_data(db)
    caption = "😻 <b>Муррр! Спасибо за вкусняшку!</b>\nЯ всё съел и теперь довольный сплю. 💤🐾"
    try:
        await update.message.reply_photo(photo="https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600", caption=caption, parse_mode="HTML")
    except Exception:
        await update.message.reply_text(caption, parse_mode="HTML")

# Функция погоды
async def get_weather(update: Update, city=None):
    params = {"appid": WEATHER_API_KEY, "q": city, "units": "metric", "lang": "ru"}
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.openweathermap.org/data/2.5/weather", params=params)
    
    if r.status_code == 200:
        data = r.json()
        temp = round(data['main']['temp'])
        desc = data['weather'][0]['description'].capitalize()
        main_weather = data['weather'][0]['main']
        
        image_url = CAT_IMAGES.get(main_weather, CAT_IMAGES["Default"])
        
        # Проверяем, голоден ли котик
        user_id = str(update.effective_user.id)
        db = load_data()
        last_fed = db.get(user_id, 0)
        time_passed = datetime.now().timestamp() - last_fed
        
        hunger_status = ""
        if time_passed > 7200: # 2 часа
            hunger_status = "\n\n😿 <b>Мяу... Я очень голодный! Нажми 'Покормить котика'!</b>"
            cat_phrase = "Мяу-у-у... Дай мне рыбку, пожалуйста..."
        else:
            cat_phrase = get_cat_phrase(main_weather)

        caption = (
            f"🌍 Погода в <b>{data['name']}</b>: {temp}°C, {desc}\n"
            f"{get_advice(temp)}\n\n"
            f"🐱 <b>Твой питомец говорит:</b>\n"
            f"<i>{cat_phrase}</i>{hunger_status}"
        )
        
        try:
            await update.message.reply_photo(photo=image_url, caption=caption, parse_mode="HTML")
        except Exception:
            await update.message.reply_text(caption, parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Город не найден. Проверь название.")

# Обработчик текста
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # Если нажали кнопку или написали "Покормить"
    if "покормить" in text.lower():
        await feed_cat(update)
        return
        
    if text.startswith("🐱") or "Мяу" in text:
        await update.message.reply_text("Муррр! Спасибо тебе! 😽 Ты лучший хозяин на свете!")
        return
        
    context.user_data['last_city'] = text
    await get_weather(update, city=text)

# Обработчик геолокации
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    params = {"appid": WEATHER_API_KEY, "lat": loc.latitude, "lon": loc.longitude, "units": "metric", "lang": "ru"}
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.openweathermap.org/data/2.5/weather", params=params)
    if r.status_code == 200:
        data = r.json()
        temp = round(data['main']['temp'])
        await update.message.reply_text(f"📍 Погода по геолокации:\n🌡 {temp}°C в {data['name']}")
    else:
        await update.message.reply_text("❌ Не удалось определить погоду.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📍 Моя геолокация", request_location=True)],
        [KeyboardButton("🐟 Покормить котика")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! 👋\nНапиши название города, и я пришлю погоду и покажу твоего питомца 🐱\n\n"
        "Не забывай кормить котика кнопкой ниже, иначе он расстроится! 🐟",
        reply_markup=reply_markup
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
