import os
import asyncio
import aiohttp
import urllib.parse  # Добавлено для безопасного кодирования городов в URL
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

load_dotenv()

# Токены (Для Amvera лучше перенести их в панель "Переменные" хостинга)
TOKEN = os.getenv("TOKEN", "8789941042:AAFYc_67SUw1xKSQ3ryHoOwJ-E48tIXaMaE")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "7d130988265d37ee60a3e3da9e784cca")

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
    # Очищаем от лишних пробелов и кодируем спецсимволы/кириллицу
    safe_city = urllib.parse.quote(city.strip())
    
    # ИСПРАВЛЕНО: Указан верный эндпоинт API прогноза (forecast) вместо обычного сайта
    url = f"openweathermap.org{safe_city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            print(f"Ошибка сетевого запроса: {e}")
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
        await callback.answer("Ошибка: данные о погоде не найдены.", show_alert=True)
        return

    forecast_list = data["list"]
    text = f"📅 Прогноз для: {data['city']['name']}\n\n"
    
    # Берем данные с шагом в 24 часа (каждая 8-я запись, так как шаг API равен 3 часам)
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
        # Извлекаем реальное название города из ответа API (на случай опечаток)
        real_city_name = data["city"]["name"]
        current = data["list"][0]
        temp = current["main"]["temp"]
        desc = current["weather"][0]["description"]
        await message.answer(f"📍 {real_city_name}:\n🌡 {temp:+.1f}°C, {desc}")
    else:
        await message.answer("❌ Город не найден. Попробуйте ввести название на русском или английском языке.")

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
