import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TELEGRAM_TOKEN = "9246784802:AAHxP96JoEXmjE_nmsWU12Pgm_TmV-LWghM"
WEATHER_API_KEY = "faedfd8d0fe879aab4f6d34c818ccb55"

async def get_weather(update: Update, context):
    city = update.message.text
    params = {"appid": WEATHER_API_KEY, "q": city, "units": "metric", "lang": "ru"}
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.openweathermap.org/data/2.5/weather", params=params)
    if r.status_code == 200:
        data = r.json()
        temp = round(data['main']['temp'])
        await update.message.reply_text(f"В {data['name']}: {temp} градусов")
    else:
        await update.message.reply_text("Город не найден")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Привет! Напиши город")))
    app.add_handler(MessageHandler(filters.TEXT, get_weather))
    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
