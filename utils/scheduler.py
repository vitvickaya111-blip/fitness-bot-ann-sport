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


def schedule_video_funnel(bot, user_id: int):
    """Запуск воронки после оплаты онлайн-тренировки"""
    import logging
    from datetime import datetime, timedelta

    logger = logging.getLogger(__name__)
    scheduler = get_scheduler()
    if not scheduler:
        logger.error(f"[FUNNEL] Планировщик не найден, воронка для {user_id} не запущена")
        return

    # Шаг 1: Через 24 часа — напоминание + cross-sell
    run_time_1 = datetime.now() + timedelta(hours=24)
    scheduler.add_job(
        _video_funnel_step1,
        trigger=DateTrigger(run_date=run_time_1),
        args=[bot, user_id],
        id=f'video_funnel_step1_{user_id}',
        replace_existing=True
    )

    # Шаг 2: Через 3 дня — предложение регулярных тренировок
    run_time_2 = datetime.now() + timedelta(days=3)
    scheduler.add_job(
        _video_funnel_step2,
        trigger=DateTrigger(run_date=run_time_2),
        args=[bot, user_id],
        id=f'video_funnel_step2_{user_id}',
        replace_existing=True
    )

    logger.info(f"[FUNNEL] Воронка онлайн-тренировки запущена для user_id={user_id}")


async def _video_funnel_step1(bot, user_id: int):
    """Шаг 1 воронки: через 24 часа после оплаты"""
    import logging
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    logger = logging.getLogger(__name__)
    try:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💪 План тренировок", callback_data="online_plan")],
                [InlineKeyboardButton(text="📋 Меню питания", callback_data="online_menu")],
            ]
        )
        await bot.send_message(
            user_id,
            "Привет! Как прошла тренировка? 😊\n\n"
            "Для лучшего результата важно сочетать тренировки "
            "с правильным питанием.\n\n"
            "Посмотри план тренировок для дома или меню питания — "
            "вместе они дают максимальный эффект! 👇",
            reply_markup=kb
        )
        logger.info(f"[FUNNEL] Шаг 1 отправлен user_id={user_id}")
    except Exception as e:
        logger.error(f"[FUNNEL] Ошибка шага 1 для user_id={user_id}: {e}")


async def _video_funnel_step2(bot, user_id: int):
    """Шаг 2 воронки: через 3 дня после оплаты"""
    import logging
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    logger = logging.getLogger(__name__)
    try:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💎 Абонемент в студию", callback_data="studio_subscription")],
                [InlineKeyboardButton(text="👥 Наставничество", callback_data="online_mentoring")],
                [InlineKeyboardButton(text="📹 Ещё онлайн-тренировка", callback_data="online_video")],
            ]
        )
        await bot.send_message(
            user_id,
            "Хочешь тренироваться регулярно? 💪\n\n"
            "С абонементом в студию — групповые тренировки каждый день, "
            "а с наставничеством получишь полное сопровождение: "
            "питание + тренировки + поддержку.\n\n"
            "Выбирай что подходит 👇",
            reply_markup=kb
        )
        logger.info(f"[FUNNEL] Шаг 2 отправлен user_id={user_id}")
    except Exception as e:
        logger.error(f"[FUNNEL] Ошибка шага 2 для user_id={user_id}: {e}")


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
