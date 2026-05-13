import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

# Вставь свой токен от @BotFather внутрь кавычек (пример: "123456:ABCde...")
TOKEN = "7d130988265d37ee60a3e3da9e784cca"
WEATHER_API_KEY = "7d130988265d37ee60a3e3da9e784cca"

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_main_kb():
    buttons = [
        [InlineKeyboardButton(text="Омск", callback_data="weather_Omsk")],
        [InlineKeyboardButton(text="Москва", callback_data="weather_Moscow")],
        [InlineKeyboardButton(text="Санкт-Петербург", callback_data="weather_Saint Petersburg")],
        [InlineKeyboardButton(text="⌨️ Ввести город вручную", callback_data="manual_input")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def get_forecast(city: str):
    url = "openweathermap.org"
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except Exception as e:
        print(f"Ошибка запроса погоды: {e}")
        return None

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Выбери город из списка или напиши название города:", 
                         reply_markup=get_main_kb())

@dp.callback_query(F.data.startswith("weather_"))
async def city_forecast(callback: CallbackQuery):
    city = callback.data.split("_")[1]
    data = await get_forecast(city)
    
    if not data:
        await callback.answer("⚠️ Не удалось получить прогноз погоды. Проверьте город.")
        return

    forecast_list = data["list"]
    text = f"📅 Прогноз для: {data['city']['name']}\n\n"
    
    for i in range(0, len(forecast_list), 8):
        day_data = forecast_list[i]
        date = day_data["dt_txt"].split(" ")[0]
        temp = day_data["main"]["temp"]
        desc = day_data["weather"][0]["description"]
        text += f"🔹 {date}: {temp:+.1f}°C, {desc}\n"

    await callback.message.edit_text(text, reply_markup=get_main_kb())
    await callback.answer()

@dp.callback_query(F.data == "manual_input")
async def manual_step(callback: CallbackQuery):
    await callback.message.answer("Просто напиши название города в чат (например: Тюмень):")
    await callback.answer()

@dp.message()
async def handle_text(message: Message):
    data = await get_forecast(message.text)
    if data and data.get("list"):
        current = data["list"][0]
        temp = current["main"]["temp"]
        desc = current["weather"][0]["description"]
        await message.answer(f"📍 {data['city']['name']}:\n🌡 {temp:+.1f}°C, {desc}")
    else:
        await message.answer("⚠️ Город не найден или сервис погоды недоступен.")

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
