"""
Планировщик задач для автоматических уведомлений
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from utils.notifications import (
    send_expiring_notifications,
    send_inactive_notifications,
    send_comeback_notifications,
    send_training_reminders
)

_scheduler = None


def get_scheduler():
    """Получить экземпляр планировщика"""
    return _scheduler


def setup_scheduler(bot):
    """Настройка планировщика задач"""
    global _scheduler
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    # Уведомления об истекающих абонементах (каждый день в 10:00)
    scheduler.add_job(
        send_expiring_notifications,
        trigger=CronTrigger(hour=10, minute=0),
        args=[bot],
        id='expiring_notifications'
    )

    # Уведомления неактивным (каждое воскресенье в 11:00)
    scheduler.add_job(
        send_inactive_notifications,
        trigger=CronTrigger(day_of_week='sun', hour=11, minute=0),
        args=[bot],
        id='inactive_notifications'
    )

    # Уведомления возврата (каждый день в 12:00)
    scheduler.add_job(
        send_comeback_notifications,
        trigger=CronTrigger(hour=12, minute=0),
        args=[bot],
        id='comeback_notifications'
    )

    # Напоминания о тренировках (каждый час)
    scheduler.add_job(
        send_training_reminders,
        trigger=CronTrigger(minute=0),
        args=[bot],
        id='training_reminders'
    )

    scheduler.start()
    _scheduler = scheduler
    return scheduler


async def schedule_menu_retry(bot, user_id: int, file_path: str, caption: str, attempt: int = 1, max_attempts: int = 3):
    """Запланировать повторную отправку PDF меню через 5 минут"""
    import os
    import logging
    from datetime import datetime, timedelta
    from aiogram.types import FSInputFile
    import config

    logger = logging.getLogger(__name__)

    try:
        if os.path.exists(file_path):
            menu_file = FSInputFile(file_path)
            await bot.send_document(user_id, document=menu_file, caption=caption)
            logger.info(f"Меню отправлено пользователю {user_id} (попытка {attempt})")
            return
        else:
            raise FileNotFoundError(f"Файл не найден: {file_path}")
    except Exception as e:
        logger.error(f"Ошибка отправки меню пользователю {user_id} (попытка {attempt}): {e}")

        if attempt < max_attempts:
            scheduler = get_scheduler()
            if scheduler:
                run_time = datetime.now() + timedelta(minutes=5)
                scheduler.add_job(
                    schedule_menu_retry,
                    trigger=DateTrigger(run_date=run_time),
                    args=[bot, user_id, file_path, caption, attempt + 1, max_attempts],
                    id=f'menu_retry_{user_id}_{attempt + 1}',
                    replace_existing=True
                )
                logger.info(f"Повторная отправка меню для {user_id} запланирована (попытка {attempt + 1})")
        else:
            logger.error(f"Все {max_attempts} попыток отправки меню пользователю {user_id} провалились")
            for admin_id in config.ADMIN_IDS:
                try:
                    await bot.send_message(
                        admin_id,
                        f"⚠️ Не удалось отправить меню пользователю {user_id} после {max_attempts} попыток.\n"
                        f"Файл: {file_path}"
                    )
                except Exception:
                    pass
