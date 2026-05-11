import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

load_dotenv()
# Убедись, что в файле .env есть строка TOKEN=твой_токен
TOKEN = os.getenv("TOKEN")


# --- ИСПРАВЛЕНО: Создаем объект bot ---
bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_main_kb():
    buttons = [
        [InlineKeyboardButton(text="Омск", callback_query_data="weather_Omsk")],
        [InlineKeyboardButton(text="Москва", callback_query_data="weather_Moscow")],
        [InlineKeyboardButton(text="Санкт-Петербург", callback_query_data="weather_Saint Petersburg")],
        [InlineKeyboardButton(text="⌨️ Ввести город вручную", callback_query_data="manual_input")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def get_forecast(city: str):
    # --- ИСПРАВЛЕНО: Полный и правильный URL ---
    url = f"http://openweathermap.org{city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
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
        await callback.answer("Ошибка: город не найден.")
        return

    forecast_list = data["list"]
    text = f"📅 Прогноз для: {data['city']['name']}\n\n"
    
    # Берем данные с шагом в 24 часа (каждая 8-я запись)
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
    if data:
        # Берем самую первую запись из списка (текущая или ближайшая погода)
        current = data["list"][0]
        temp = current["main"]["temp"]
        desc = current["weather"][0]["description"]
        await message.answer(f"📍 {message.text}:\n🌡 {temp:+.1f}°C, {desc}")
    else:
        await message.answer("❌ Город не найден. Попробуй еще раз.")

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
