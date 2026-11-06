import httpx
import random
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "9246784802:AAHxP96JoEXmjE_nmsWU12Pgm_TmV-LWghM"
WEATHER_API_KEY = "faedfd8d0fe879aab4f6d34c818ccb55"

# Картинки для котика в зависимости от погоды
CAT_IMAGES = {
    "Clear": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600", # Кот на солнце
    "Clouds": "https://images.unsplash.com/photo-1533738363-b7f9aef128ce?w=600", # Кот задумчивый
    "Rain": "https://images.unsplash.com/photo-1548247416-ec66f4900b2e?w=600", # Кот грустит
    "Snow": "https://images.unsplash.com/photo-1518791841217-8f162f1e1131?w=600", # Кот в снегу
    "Default": "https://images.unsplash.com/photo-1519052537078-e6302a4968d4?w=600" # Просто кот
}

# Фразы котика
CAT_PHRASES = {
    "Clear": ["Мяу! Солнце светит, я греюсь на подоконнике! ☀️🐈", "Ура, гулять! Пойдем ловить бабочек? 🦋🐾"],
    "Clouds": ["Мяу... Пасмурно. Я лучше посплю на твоих коленях. 😴☁️", "Хмурое небо, но мне всё равно тепло рядом с тобой. 🐱💤"],
    "Rain": ["Мррр... Дождь. Я не пойду гулять, буду смотреть в окно. 🌧🐾", "Мяу! Дождик, давай пить чай с молоком и смотреть мультики? 🍵🐱"],
    "Snow": ["Мяу! Холодно! Шапку мне, шапку! ❄️🧣🐈", "Снег! Я зарываюсь в плед и не выйду оттуда до весны. ⛄️🐱"],
    "Default": ["Мяу! Накорми меня, пожалуйста! 🐾", "Я сегодня самый милый кот на свете, погладь меня! 🐱✨"]
}

CAT_ACTIONS = [
    "Погладь меня! 🐾", 
    "Дай мне вкусняшку! 🐟", 
    "Почеши за ушком! 👆", 
    "Сыграем в клубочек? 🧶", 
    "Мяу! Я хочу спать... 😴"
]

def get_cat_phrase(main_weather):
    return random.choice(CAT_PHRASES.get(main_weather, CAT_PHRASES["Default"]))

def get_advice(temp):
    if temp <= 0: return "🧥 Очень холодно, наденьте пуховик и шапку!"
    elif temp <= 10: return "🧥 Прохладно, лучше надеть куртку."
    elif temp <= 18: return "🧥 Свежо, возьмите кофту или ветровку."
    elif temp <= 25: return "👕 Тепло, можно в футболке."
    else: return "🩳 Жарко, пейте больше воды и не забудьте панамку!"

async def get_weather(update: Update, context: ContextTypes.DEFAULT_TYPE, city=None):
    params = {"appid": WEATHER_API_KEY, "q": city, "units": "metric", "lang": "ru"}
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.openweathermap.org/data/2.5/weather", params=params)
    
    if r.status_code == 200:
        data = r.json()
        temp = round(data['main']['temp'])
        desc = data['weather'][0]['description'].capitalize()
        main_weather = data['weather'][0]['main']
        
        image_url = CAT_IMAGES.get(main_weather, CAT_IMAGES["Default"])
        cat_phrase = get_cat_phrase(main_weather)
        action = random.choice(CAT_ACTIONS)
        
        caption = (
            f"🌍 Погода в <b>{data['name']}</b>: {temp}°C, {desc}\n"
            f"{get_advice(temp)}\n\n"
            f"🐱 <b>Твой питомец говорит:</b>\n"
            f"<i>{cat_phrase}</i>\n\n"
            f"👉 <b>{action}</b>"
        )
        
        try:
            await update.message.reply_photo(photo=image_url, caption=caption, parse_mode="HTML")
        except Exception:
            await update.message.reply_text(caption, parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Город не найден. Проверь название.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.startswith("🐱") or "Мяу" in text or text in CAT_ACTIONS:
        await update.message.reply_text("Муррр! Спасибо тебе! 😽 Ты лучший хозяин на свете!")
        return
        
    context.user_data['last_city'] = text
    await get_weather(update, context, city=text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([[KeyboardButton("📍 Моя геолокация", request_location=True)]], resize_keyboard=True)
    await update.message.reply_text(
        "Привет! 👋\nНапиши название города, и я пришлю погоду и покажу твоего питомца 🐱",
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
