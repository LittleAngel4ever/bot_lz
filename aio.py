import asyncio
import os
from datetime import datetime
import pandas as pd
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from secret import token

# ==== НАСТРОЙКИ ====
TELEGRAM_TOKEN = token
url1 = "https://wttr.in/Baranovichi?format=j1"
url2 = "https://catfact.ninja/fact"
url3 = "https://open.er-api.com/v6/latest/RUB"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ===== ЛОГЕР =====
def logging(api: str):
    def decorator(func):
        async def wrapper(message: types.Message, *args, **kwargs):
            result = await func(message, *args, **kwargs)
            user_id = message.from_user.id
            api_answer = str(result)
            logs = "log.csv"
            time_act = str(datetime.now().time())
            day_act = str(datetime.now().date())
            if os.path.isfile(logs):
                file_df = pd.read_csv(logs)
                unic_id = len(file_df)
            else:
                unic_id = 0
            data = {
                "Unic_ID": [unic_id],
                "User_id": [user_id],
                "Motion": ["Button"],
                "API": [api],
                "Date": [day_act],
                "Time": [time_act],
                "API_answer": [api_answer],
            }
            df = pd.DataFrame(data)
            if os.path.isfile(logs):
                df.to_csv(logs, mode="a", header=False, index=False)
            else:
                df.to_csv(logs, index=False)

            return result

        return wrapper
    return decorator

# ==== ФУНКЦИИ API ====
def weather(url: str):
    try:
        req = requests.get(url).json()
        today = req["weather"][0]
        date = today["date"]
        avgtemp = today["avgtempC"]
        desc = today["hourly"][4]["weatherDesc"][0]["value"]
        return f"{date}: Средняя температура: {avgtemp}°C, {desc}"
    except Exception as exception:
        return f"Ошибка получения погоды: {exception}"

def cats(url: str):
    response = requests.get(url)
    return response.json()["fact"]

def news(url: str):
    try:
        response = requests.get(url)
        data = response.json()

        if "rates" in data and "USD" in data["rates"]:
            rub_to_usd = data["rates"]["USD"]
            answer = f"Курс: 1 RUB = {rub_to_usd:.6f} USD"
        else:
            answer = "Не удалось получить данные о курсе валют."
        
        return answer

    except Exception as e:
        print(f"[Ошибка курса валют] {e}")
        return  "Ошибка при получении курса валют."

# ===== Работа БОТА =====
start_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Старт")]], resize_keyboard=True
)
choice_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Погода в городе"), KeyboardButton(text="Факт про котов"), KeyboardButton(text="Новости")]
    ],
    resize_keyboard=True,
)

@dp.message(Command(commands = ["start"]))
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать!", reply_markup=start_kb)

@dp.message()
@logging(api = "Keyboard Input", motion = "Text")
async def handle_messages(message: types.Message):
    if message.text == "Старт":
        await message.answer("Кого ты выберешь?", reply_markup=choice_kb)
    elif message.text == "Погода в городе":
        return await handle_weather(message)
    elif message.text == "Факт про котов":
        return await handle_cats(message)
    elif message.text == "Новости":
        return await handle_news(message)
    else:
        await message.answer(f"Вы написали: {message.text}, я не знаю такой команды")

@logging(api="weather")
async def handle_weather(message: types.Message):
    result = weather(url1)
    await message.answer(result)
    return result

@logging(api="Cats fact")
async def handle_cats(message: types.Message):
    result = f"Fun fact about cats: {cats(url2)}"
    await message.answer(result)
    return result

@logging(api="news")
async def handle_news(message: types.Message):
    result = news(url3)
    await message.answer(result)
    return result

# ==== ЗАПУСК ====
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())