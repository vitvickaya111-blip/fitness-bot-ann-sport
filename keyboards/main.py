"""
Основные клавиатуры бота
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_keyboard():
    """Главное меню"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏢 Занятия в студии"), KeyboardButton(text="📱 Занятия онлайн")],
            [KeyboardButton(text="📋 Меню питания")],
            [KeyboardButton(text="💪 План тренировок")],
            [KeyboardButton(text="👥 Наставничество")],
            [KeyboardButton(text="👤 Мой профиль")],
            [KeyboardButton(text="⭐ Отзывы"), KeyboardButton(text="🔄 До и после")],
            [KeyboardButton(text="❓ Что взять с собой")],
            [KeyboardButton(text="🙋‍♀️ Обо мне"), KeyboardButton(text="ℹ️ О студии")]
        ],
        resize_keyboard=True
    )
    return keyboard