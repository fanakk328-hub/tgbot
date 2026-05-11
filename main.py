import os
import asyncio
from dotenv import load_dotenv
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
load_dotenv()
TOKEN = os.getenv("TOKEN")
WEATHER_API_KEY = "7d130988265d37ee60a3e3da9e784cca"


dp = Dispatcher()

# Функция для создания клавиатуры
def get_main_kb():
    buttons = [
        [InlineKeyboardButton(text="Омск", callback_query_data="weather_Omsk")],
        [InlineKeyboardButton(text="Москва", callback_query_data="weather_Moscow")],
        [InlineKeyboardButton(text="Санкт-Петербург", callback_query_data="weather_Saint Petersburg")],
        [InlineKeyboardButton(text="⌨️ Ввести город вручную", callback_query_data="manual_input")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def get_forecast(city: str):
    # Используем /forecast для получения данных на 5 дней (стандарт бесплатного API)
    url = f"http://openweathermap.org{city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Выбери город из списка или нажми кнопку для ввода:", 
                         reply_markup=get_main_kb())

@dp.callback_query(F.data.startswith("weather_"))
async def city_forecast(callback: CallbackQuery):
    city = callback.data.split("_")[1]
    data = await get_forecast(city)
    
    if not data:
        await callback.answer("Ошибка получения данных.")
        return

    # Фильтруем данные, чтобы получить прогноз на полдень каждого дня
    forecast_list = data["list"]
    text = f"📅 Прогноз на ближайшие дни для: {data['city']['name']}\n\n"
    
    # Выбираем по одной записи на каждый день (каждая 8-я запись, т.к. шаг 3 часа)
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
    await callback.message.answer("Просто напиши название города в чат:")
    await callback.answer()

@dp.message()
async def handle_text(message: Message):
    # Обычный поиск по тексту (как в прошлом примере)
    data = await get_forecast(message.text)
    if data:
        temp = data["list"][0]["main"]["temp"]
        desc = data["list"][0]["weather"][0]["description"]
        await message.answer(f"Сейчас в {message.text}: {temp}°C, {desc}")
    else:
        await message.answer("Город не найден.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
