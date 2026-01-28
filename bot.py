import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

import config
from database import init_db, seed_trainings
from utils.scheduler import setup_scheduler

# Импорт обработчиков
from handlers import start, online, studio, profile, payment, admin, booking

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def on_startup():
    """Действия при запуске"""
    logger.info("Инициализация базы данных...")
    await init_db()
    logger.info("Заполнение расписания тренировок...")
    await seed_trainings()

    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="privacy", description="Политика конфиденциальности"),
        BotCommand(command="delete_my_data", description="Удалить мои данные"),
        BotCommand(command="export_my_data", description="Экспорт моих данных"),
    ])

    logger.info("Запуск планировщика задач...")
    setup_scheduler(bot)

    logger.info("Бот запущен и готов к работе!")
    logger.info(f"Название студии: {config.STUDIO_NAME}")


async def on_shutdown():
    """Действия при остановке"""
    logger.info("Остановка бота...")
    await bot.session.close()


async def main():
    """Главная функция"""
    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(online.router)
    dp.include_router(studio.router)
    dp.include_router(profile.router)
    dp.include_router(booking.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)

    # Запуск бота
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
