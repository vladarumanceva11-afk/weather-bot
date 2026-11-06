import httpx
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "9246784802:AAHxP96JoEXmjE_nmsWU12Pgm_TmV-LWghM"
WEATHER_API_KEY = "faedfd8d0fe879aab4f6d34c818ccb55"

def get_weather_icon(main_weather):
    icons = {
        "Clear": "☀️",
        "Clouds": "☁️",
        "Rain": "🌧",
        "Snow": "❄️",
        "Thunderstorm": "⛈",
        "Drizzle": "🌦",
        "Mist": "🌫"
    }
    return icons.get(main_weather, "🌤")

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
            # Берем данные на завтра (примерно через 24 часа)
            tomorrow = data['list'][8] 
            temp = round(tomorrow['main']['temp'])
            desc = tomorrow['weather'][0]['description'].capitalize()
            icon = get_weather_icon(tomorrow['weather'][0]['main'])
            
            text = (
                f"{icon} <b>Прогноз на завтра</b>\n\n"
                f"🌡 Температура: <b>{temp}°C</b>\n"
                f"📝 Ожидается: {desc}\n\n"
                f"{get_advice(temp)}"
            )
            await update.message.reply_text(text, parse_mode="HTML")
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
            icon = get_weather_icon(data['weather'][0]['main'])
            
            text = (
                f"{icon} Город: <b>{data['name']}</b>\n\n"
                f"🌡 Температура: <b>{temp}°C</b> (ощущается как {feels_like}°C)\n"
                f"📝 На улице: {desc}\n"
                f"💧 Влажность: {humidity}%\n"
                f"💨 Ветер: {wind} м/с\n\n"
                f"{get_advice(temp)}"
            )
            await update.message.reply_text(text, parse_mode="HTML")
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
        "Привет! 👋\nНапиши мне название города, и я скажу погоду 🌤\nИли используй кнопки ниже:",
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

