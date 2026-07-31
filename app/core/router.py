from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from app.config import settings

# Создаем корневой роутер
main_router = Router()

@main_router.message(CommandStart())
async def cmd_start(message: Message):
    # Пока просто заглушка, чтобы проверить, что бот жив
    await message.answer(
        f"👋 Привет! Я ядро системы записи booking_core.\n"
        f"Мой текущий BUSINESS_ID: {settings.BUSINESS_ID}\n"
        f"Скоро здесь появится логика бронирования!"
    )