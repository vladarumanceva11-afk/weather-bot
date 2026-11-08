import httpx
import random
import json
import os
from datetime import datetime, time
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, PreCheckoutQueryHandler

TELEGRAM_TOKEN = "9246784802:AAHxP96JoEXmjE_nmsWU12Pgm_TmV-LWghM"
WEATHER_API_KEY = "faedfd8d0fe879aab4f6d34c818ccb55"
CHANNEL_USERNAME = "@murchashaya_pogoda"

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

SKINS = {
    "default": {"name": "Дворовый", "price": 0, "image": "https://images.unsplash.com/photo-1519052537078-e6302a4968d4?w=600"},
    "gentleman": {"name": "Джентльмен", "price": 500, "image": "https://images.unsplash.com/photo-1533738363-b7f9aef128ce?w=600"},
    "astronaut": {"name": "Космонавт", "price": 1500, "image": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600"},
    "mafia": {"name": "Мафиози", "price": 5000, "image": "https://images.unsplash.com/photo-1518791841217-8f162f1e1131?w=600"},
    "emperor": {"name": "Император 👑", "price": 10000, "image": "https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=600"}
}

FACTS = ["Скорость звука 343 м/с.", "Давление 760 мм рт. ст.", "Температура max +56.7°C.", "Облака весят 500 тонн.", "Радуга — это свет.", "В Антарктиде 90% льда.", "Молния 30 000°C.", "Сухой континент — Австралия."]
EVENING_PHRASES = ["Вечер — время выдохнуть.", "Пусть вечер пройдет спокойно.", "Лучший способ перезагрузиться — выспаться.", "Спокойствие — это роскошь.", "Закончи работу.", "Даже рабочая неделя заканчивается."]
CAT_PHRASES = {"Clear": ["Солнце светит. ☀️🐈", "Отличная погода. 🦋🐾"], "Clouds": ["Пасмурно. 😴☁️", "Серое небо. 🐱💤"], "Rain": ["Дождь. 🌧🐾", "Погода для сериала. 🍵🐱"], "Snow": ["Холодно. ❄️🧣🐈", "Снег. ⛄️🐱"], "Default": ["Я медитирую. 🐾", "Погода философская. 🐱✨"]}
PREDICTIONS = ["🔮 Тебе повезёт!", "🔮 Отличный день!", "🔮 Тебя ждет приятное!", "🔮 Погладь кота!", "🔮 Верь в себя!"]
WEATHER_TIPS = {"Clear": "Носи головной убор! 🧢", "Clouds": "Иди гулять! 🍂", "Rain": "Возьми зонт! ☔️", "Snow": "Одевайся слоями! 🧣", "Default": "Пей воду! 😊"}
DAILY_BONUSES = ["Держи рыбку! 🐟", "Вот клубок! 🧶", "Статус 'Лучший хозяин'! 🏆", "Хвост виляет! 🐾", "Мурчание! 😽"]

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

def get_name(user):
    return user.first_name if user.first_name else "Хозяин"

async def check_sub(user_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return True

async def add_exp(user_id, username, amount=1):
    db = load_data()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": username, "last_bonus": 0, "coins": 0, "skin": "default"}
    
    db[uid]["coins"] = db[uid].get("coins", 0) + amount 
    db[uid]["name"] = username
    db[uid]["exp"] += amount
    lvl = db[uid]["level"]
    if lvl < 3 and db[uid]["exp"] >= LEVEL_UP_EXP[lvl]:
        db[uid]["level"] += 1
        db[uid]["exp"] = 0
    save_data(db)
    return db[uid]["level"], db[uid]["exp"], lvl != db[uid]["level"]

def level_name(lvl):
    return ["🐣 Котенок", "🐱 Подросток", "🐈 Взрослый Кот", "👑 Король дивана"][lvl]

def cat_phrase(weather, lvl):
    if lvl == 3: return "Я король. Принеси рыбу. 👑🐾"
    return random.choice(CAT_PHRASES.get(weather, CAT_PHRASES["Default"]))

def advice(temp):
    if temp <= 0: return "Наденьте пуховик! 🧥"
    if temp <= 10: return "Наденьте куртку. 🧥"
    if temp <= 18: return "Возьмите кофту. 🧥"
    if temp <= 25: return "Можно в футболке. 👕"
    return "Пейте воду! 🩳"

async def send_fact(context: ContextTypes.DEFAULT_TYPE):
    fact = random.choice(FACTS)
    text = f"🌅 <b>Доброе утро.</b>\n\n<b>Факт дня:</b>\n<i>{fact}</i>\n\nХорошего дня."
    try:
        await context.bot.send_photo(chat_id=CHANNEL_USERNAME, photo="https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600", caption=text, parse_mode="HTML")
    except:
        pass

async def send_evening(context: ContextTypes.DEFAULT_TYPE):
    phrase = random.choice(EVENING_PHRASES)
    text = f"🌙 <b>Добрый вечер.</b>\n\n<i>{phrase}</i>\n\nСпокойной ночи."
    try:
        await context.bot.send_photo(chat_id=CHANNEL_USERNAME, photo="https://images.unsplash.com/photo-1519052537078-e6302a4968d4?w=600", caption=text, parse_mode="HTML")
    except:
        pass

async def show_wardrobe(update: Update):
    uid = str(update.effective_user.id)
    db = load_data()
    if uid not in db:
        db[uid] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": get_name(update.effective_user), "last_bonus": 0, "coins": 0, "skin": "default"}
        save_data(db)
    
    coins = db[uid].get("coins", 0)
    curr_skin = db[uid].get("skin", "default")
    kb = []
    
    for sid, sdata in SKINS.items():
        if sid == curr_skin:
            kb.append([InlineKeyboardButton(f"✅ {sdata['name']} (Надето)", callback_data="noop")])
        else:
            kb.append([InlineKeyboardButton(f"{sdata['name']} - {sdata['price']} 🐟", callback_data=f"buy_{sid}")])
            
    kb.append([InlineKeyboardButton("💎 Купить 500 рыбок за 50 Stars", callback_data="buy_stars")])
    markup = InlineKeyboardMarkup(kb)
    
    await update.message.reply_text(
        f"🎨 <b>Гардероб котика</b>\n\nУ тебя на счету: <b>{coins} 🐟</b>\nВыбери, что надеть:",
        reply_markup=markup,
        parse_mode="HTML"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    if q.data == "buy_stars":
        await context.bot.send_invoice(
            chat_id=q.message.chat_id,
            title="💎 500 рыбок",
            description="Пополни баланс для покупки шубок!",
            payload="buy_500_fish",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("Пакет рыбок", 50)]
        )
        return

    if q.data.startswith("buy_"):
        sid = q.data.replace("buy_", "")
        uid = str(update.effective_user.id)
        db = load_data()
        if uid not in db: return
        
        price = SKINS[sid]["price"]
        coins = db[uid].get("coins", 0)
        
        if coins >= price:
            db[uid]["coins"] -= price
            db[uid]["skin"] = sid
            save_data(db)
            await q.edit_message_text(f"✅ Ты купил шубку «{SKINS[sid]['name']}»! (Остаток: {db[uid]['coins']} 🐟)")
        else:
            await q.edit_message_text(f"❌ Недостаточно рыбок! Нужно {price} 🐟.")
        return
    
    if q.data == "noop":
        await q.answer("Эта шубка уже надета!")
        return

    if q.data == "check_sub":
        if await check_sub(update.effective_user.id, context):
            await q.edit_message_text("✅ Спасибо за подписку! Напиши город.")
        else:
            await q.edit_message_text("❌ Ты ещё не подписался.")

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.pre_checkout_query
    if q.invoice_payload == "buy_500_fish":
        await q.answer(ok=True)
    else:
        await q.answer(ok=False, error_message="Ошибка.")

async def success_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db = load_data()
    if uid in db:
        db[uid]["coins"] = db[uid].get("coins", 0) + 500
        save_data(db)
    await update.message.reply_text("💎 <b>Оплата прошла!</b>\nБаланс пополнен на 500 рыбок 🐟.", parse_mode="HTML")

async def daily_bonus(update: Update):
    uid = str(update.effective_user.id)
    name = get_name(update.effective_user)
    db = load_data()
    if uid not in db:
        db[uid] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": name, "last_bonus": 0, "coins": 0, "skin": "default"}
    
    last_bonus = db[uid].get("last_bonus", 0)
    now = datetime.now().timestamp()
    if now - last_bonus < 86400:
        time_left = 86400 - (now - last_bonus)
        await update.message.reply_text(f"Бонус уже получен. Жди {int(time_left // 3600)} ч. 🕰")
        return
        
    db[uid]["last_bonus"] = now
    save_data(db)
    await add_exp(uid, name, 3)
    
    text = f"🎁 <b>Бонус!</b>\n\n{random.choice(DAILY_BONUSES)}\n\n✨ +3 опыта и +3 рыбки 🐟"
    try:
        skin = db[uid].get("skin", "default")
        await update.message.reply_photo(photo=SKINS[skin]["image"], caption=text, parse_mode="HTML")
    except:
        await update.message.reply_text(text, parse_mode="HTML")

async def show_top(update: Update):
    db = load_data()
    if not db:
        await update.message.reply_text("Топ пуст.")
        return
    sorted_users = sorted(db.items(), key=lambda x: (x[1].get('level', 0), x[1].get('exp', 0), x[1].get('total_fed', 0)), reverse=True)
    text = "🏆 <b>Топ игроков:</b>\n\n"
    for i, (uid, data) in enumerate(sorted_users[:5], 1):
        text += f"{i}. <b>{data.get('name')}</b> — {level_name(data.get('level', 0))}, 🐟 {data.get('total_fed', 0)}\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def feed_cat(update: Update):
    uid = str(update.effective_user.id)
    name = get_name(update.effective_user)
    db = load_data()
    if uid not in db:
        db[uid] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": name, "last_bonus": 0, "coins": 0, "skin": "default"}
    
    if datetime.now().timestamp() - db[uid].get("last_fed", 0) < 300:
        await update.message.reply_text("Я уже сыт. 😸")
        return
        
    db[uid]["last_fed"] = datetime.now().timestamp()
    db[uid]["total_fed"] = db[uid].get("total_fed", 0) + 1
    save_data(db)
    
    await add_exp(uid, name, 2)
    
    text = "😻 <b>Спасибо. Было вкусно.</b>\n💤\n\n✨ +2 опыта и +2 рыбки 🐟"
    try:
        skin = db[uid].get("skin", "default")
        await update.message.reply_photo(photo=SKINS[skin]["image"], caption=text, parse_mode="HTML")
    except:
        await update.message.reply_text(text, parse_mode="HTML")

async def show_stats(update: Update):
    uid = str(update.effective_user.id)
    db = load_data()
    if uid not in db:
        db[uid] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": get_name(update.effective_user), "last_bonus": 0, "coins": 0, "skin": "default"}
        save_data(db)
        
    data = db[uid]
    lvl = data["level"]
    next_exp = LEVEL_UP_EXP.get(lvl, "MAX")
    text = f"📊 <b>Статистика:</b>\n\n👤 Имя: <b>{data.get('name')}</b>\n🐱 Уровень: {level_name(lvl)}\n✨ Опыт: {data['exp']}/{next_exp}\n🐟 Рыбок: {data.get('coins', 0)}\n🐾 Кормлений: {data.get('total_fed', 0)}"
    await update.message.reply_text(text, parse_mode="HTML")

async def get_weather(update: Update, city=None):
    params = {"appid": WEATHER_API_KEY, "q": city, "units": "metric", "lang": "ru"}
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.openweathermap.org/data/2.5/weather", params=params)
        
    if r.status_code == 200:
        data = r.json()
        temp = round(data['main']['temp'])
        desc = data['weather'][0]['description'].capitalize()
        weather = data['weather'][0]['main']
        
        uid = str(update.effective_user.id)
        name = get_name(update.effective_user)
        lvl, exp, leveled_up = await add_exp(uid, name, 1)
        
        db = load_data()
        skin = db[uid].get("skin", "default")
        img = SKINS[skin]["image"]
        
        passed = datetime.now().timestamp() - db[uid].get("last_fed", 0)
        hungry = "\n\n😿 <b>Я голоден.</b>" if passed > 7200 else ""
        phrase = "Покорми меня..." if passed > 7200 else cat_phrase(weather, lvl)
        lvl_text = f"\n\n🎉 <b>Новый уровень: {level_name(lvl)}!</b>" if leveled_up else ""
        exp_text = f"✨ Опыт: {exp}/{LEVEL_UP_EXP.get(lvl, 'MAX')}" if lvl < 3 else "✨ Опыт: MAX"
        
        text = (
            f"🌍 <b>{data['name']}</b>: {temp}°C, {desc}\n"
            f"{advice(temp)}\n"
            f"{WEATHER_TIPS.get(weather, WEATHER_TIPS['Default'])}\n\n"
            f"🐱 <b>(Ур. {lvl} - {level_name(lvl)}):</b>\n"
            f"<i>{phrase}</i>{hungry}{lvl_text}\n\n{exp_text}\n🐟 Рыбок: {db[uid].get('coins', 0)}"
        )
        
        try:
            await update.message.reply_photo(photo=img, caption=text, parse_mode="HTML")
        except:
            await update.message.reply_text(text, parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Город не найден.")

async def prediction(update: Update):
    await add_exp(update.effective_user.id, get_name(update.effective_user), 1)
    text = f"🐱 <b>Кот-предсказатель:</b>\n\n<i>{random.choice(PREDICTIONS)}</i>"
    try:
        uid = str(update.effective_user.id)
        db = load_data()
        skin = db[uid].get("skin", "default")
        await update.message.reply_photo(photo=SKINS[skin]["image"], caption=text, parse_mode="HTML")
    except:
        await update.message.reply_text(text, parse_mode="HTML")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    
    if not await check_sub(update.effective_user.id, context):
        kb = [[InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")], [InlineKeyboardButton("✅ Я подписался", callback_data="check_sub")]]
        await update.message.reply_text("Подпишись на канал. 👇", reply_markup=InlineKeyboardMarkup(kb))
        return

    if any(w in text for w in ["привет", "здравствуй", "хай", "добрый день"]):
        await update.message.reply_text(f"Приветствую, {get_name(update.effective_user)}. Чем займемся? 🐱")
    elif "как дела" in text:
        await update.message.reply_text("Всё в порядке. 😸")
    elif "спасибо" in text or "благодарю" in text:
        await update.message.reply_text("Не за что. 😽")
    elif "пока" in text or "до свидания" in text:
        await update.message.reply_text("До встречи. 🐾")
    elif "покормить" in text: await feed_cat(update)
    elif "предсказание" in text: await prediction(update)
    elif "статистика" in text: await show_stats(update)
    elif "топ" in text: await show_top(update)
    elif "бонус" in text: await daily_bonus(update)
    elif "гардероб" in text or "шубка" in text: await show_wardrobe(update)
    elif "погода" in text: await update.message.reply_text("Какой город?")
    elif "ещё" in text or "меню" in text:
        kb = [[KeyboardButton("🔮 Предсказание"), KeyboardButton("📊 Статистика")], [KeyboardButton("🎨 Гардероб"), KeyboardButton("🏆 Топ игроков")], [KeyboardButton("⬅️ Назад")]]
        await update.message.reply_text("Опции:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    elif "назад" in text:
        kb = [[KeyboardButton("🌍 Погода"), KeyboardButton("🐟 Покормить котика")], [KeyboardButton("🎁 Ежедневный бонус"), KeyboardButton("🎮 Ещё")]]
        await update.message.reply_text("Главное меню:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    elif text.startswith("🐱") or "мяу" in text: 
        await update.message.reply_text("Мурр. 😽")
    else:
        context.user_data['last_city'] = update.message.text
        await get_weather(update, city=update.message.text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db = load_data()
    if uid not in db:
        db[uid] = {"level": 0, "exp": 0, "last_fed": 0, "total_fed": 0, "name": get_name(update.effective_user), "last_bonus": 0, "coins": 0, "skin": "default"}
        save_data(db)

    if not await check_sub(uid, context):
        kb = [[InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")], [InlineKeyboardButton("✅ Я подписался", callback_data="check_sub")]]
        await update.message.reply_text("Привет. Подпишись на канал. 👇", reply_markup=InlineKeyboardMarkup(kb))
        return

    kb = [[KeyboardButton("🌍 Погода"), KeyboardButton("🐟 Покормить котика")], [KeyboardButton("🎁 Ежедневный бонус"), KeyboardButton("🎮 Ещё")]]
    await update.message.reply_text("Приветствую. 👋 Напиши город или выбери кнопку.", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, success_payment))
    
    job = app.job_queue
    job.run_daily(send_fact, time=time(hour=5, minute=0))
    job.run_daily(send_evening, time=time(hour=17, minute=0))
    
    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
