import httpx
import random
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "9246784802:AAHxP96JoEXmjE_nmsWU12Pgm_TmV-LWghM"
WEATHER_API_KEY = "faedfd8d0fe879aab4f6d34c818ccb55"

# Легкие и надежные картинки
IMAGES = {
    "Clear": "https://images.unsplash.com/photo-1601297183305-6df142704ea2?w=500",
    "Clouds": "https://images.unsplash.com/photo-1534088568595-a066f410cbda?w=500",
    "Rain": "https://images.unsplash.com/photo-1519692933481-e162a57d6721?w=500",
    "Snow": "https://images.unsplash.com/photo-1478265409131-1f65c88f965c?w=500",
    "Default": "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b?w=500"
}

# Шутки и стишки
JOKES = {
    "Clear": [
        "Солнце светит, птички поют, а ты сидишь и читаешь погоду. Иди гулять! ☀️",
        "На улице жара, доставай самокат, но не забудь крем от загара! 🛴",
        "Солнце — это не только свет, но и отличный повод для мороженого! 🍦"
    ],
    "Clouds": [
        "Облака на небе — это как мысли: иногда сгущаются, но потом обязательно рассеиваются. ☁️",
        "Пасмурно? Отличный повод надеть уютный свитер и попить какао. ☕",
        "Серое небо — это просто белый цвет, который забыл включить свет. 💡"
    ],
    "Rain": [
        "Дождь — это не повод грустить, это повод купить зонт с котиками! 🌂🐈",
        "Если дождь, значит, природа просто решила помыть улицы. Не мешай ей! 🚿",
        "Дождь стучит по крыше, а ты пей чай и улыбайся. Всё будет хорошо! 🍵"
    ],
    "Snow": [
        "Снег — это зимняя магия. Главное — не забыть шапку, а то уши отморозишь! ❄️🧣",
        "На улице снежно, значит, можно лепить снеговика и кататься с горки! ⛄️",
        "Холодно? Зато можно пить горячий шоколад и смотреть в окно. 🍫"
    ],
    "Default": [
        "Погода сегодня загадочная, как сюжет моего любимого сериала! 📺",
        "В любую погоду главное — хорошее настроение. Улыбнись! 😊",
        "Погода шепчет: возьми выходной и отдохни! 🛋"
    ]
}

def get_joke(main_weather):
    return random.choice(JOKES.get(main_weather, JOKES["Default"]))

def get_advice(temp):
    if temp <= 0: return "🧥 Очень холодно, наденьте пуховик и шапку!"
    elif temp <= 10: return "🧥 Прохладно, лучше надеть куртку."
    elif temp <= 18: return "🧥 Свежо, возьмите кофту или ветровку."
    elif temp <= 25: return "👕 Тепло, можно в футболке."
    else: return "🩳 Жарко, пейте больше воды и не забудьте панамку!"

async def get_weather(update: Update, context: ContextTypes.DEFAULT_TYPE, city=None, lat=None, lon=None, forecast=False):
    params = {"appid": WEATHER_API_KEY, "units": "metric", "lang": "ru"}
    if city:
        params["q"] = city
    else:
        params["lat"], params["lon"] = lat, lon

    if forecast:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            tomorrow = data['list'][8] 
            temp = round(tomorrow['main']['temp'])
            desc = tomorrow['weather'][0]['description'].capitalize()
            main_weather = tomorrow['weather'][0]['main']
            
            image_url = IMAGES.get(main_weather, IMAGES["Default"])
            joke = get_joke(main_weather)
            caption = (
                f"🔮 <b>Прогноз на завтра</b>\n\n"
                f"🌡 Температура: <b>{temp}°C</b>\n"
                f"📝 Ожидается: {desc}\n\n"
                f"{get_advice(temp)}\n\n"
                f"<i>{joke}</i>"
            )
            try:
                await update.message.reply_photo(photo=image_url, caption=caption, parse_mode="HTML")
            except Exception:
                await update.message.reply_text(caption, parse_mode="HTML")
        else:
            await update.message.reply_text("❌ Не удалось получить прогноз.")
    else:
        url = "https://api.openweathermap.org/data/2.5/weather"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params)
        
        if r.status_code == 200:
            data = r.json()
            temp = round(data['main']['temp'])
            feels_like = round(data['main']['feels_like'])
            humidity = data['main']['humidity']
            wind = data['wind']['speed']
            desc = data['weather'][0]['description'].capitalize()
            main_weather = data['weather'][0]['main']
            
            image_url = IMAGES.get(main_weather, IMAGES["Default"])
            joke = get_joke(main_weather)
            caption = (
                f"🌍 Город: <b>{data['name']}</b>\n\n"
                f"🌡 Температура: <b>{temp}°C</b> (ощущается как {feels_like}°C)\n"
                f"📝 На улице: {desc}\n"
                f"💧 Влажность: {humidity}%\n"
                f"💨 Ветер: {wind} м/с\n\n"
                f"{get_advice(temp)}\n\n"
                f"<i>{joke}</i>"
            )
            try:
                await update.message.reply_photo(photo=image_url, caption=caption, parse_mode="HTML")
            except Exception:
                await update.message.reply_text(caption, parse_mode="HTML")
        else:
            await update.message.reply_text("❌ Город не найден. Проверь название.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔮 Прогноз на завтра":
        await get_weather(update, context, city=context.user_data.get('last_city', 'Москва'), forecast=True)
    else:
        context.user_data['last_city'] = text
        await get_weather(update, context, city=text)

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    await get_weather(update, context, lat=loc.latitude, lon=loc.longitude)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📍 Моя геолокация", request_location=True)],
        [KeyboardButton("🔮 Прогноз на завтра")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Привет! 👋\nНапиши мне название города, и я пришлю фото погоды и подниму настроение 📸\nИли используй кнопки ниже:",
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
