"""
Модуль уведомлений
"""
from aiogram import Bot
from database import async_session, User, Subscription, Visit, Booking, Training
from sqlalchemy import select
from datetime import datetime, timedelta
import config


async def send_to_channel(bot: Bot, text: str, reply_markup=None):
    """Отправить сообщение в канал"""
    try:
        await bot.send_message(
            chat_id=config.CHANNEL_USERNAME,
            text=text,
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Ошибка отправки в канал {config.CHANNEL_USERNAME}: {e}")


async def get_users_for_notification(notification_type: str) -> list:
    """Получение списка пользователей для уведомлений"""
    async with async_session() as session:
        if notification_type == 'expiring':
            # Абонементы, истекающие через 3 дня
            target_date = datetime.utcnow() + timedelta(days=3)
            result = await session.execute(
                select(Subscription, User)
                .join(User, Subscription.user_id == User.user_id)
                .where(
                    Subscription.is_active == True,
                    Subscription.end_date <= target_date,
                    Subscription.end_date > datetime.utcnow()
                )
            )
            rows = result.all()
            return [
                {
                    'user_id': row.User.user_id,
                    'name': row.User.name,
                    'end_date': row.Subscription.end_date.strftime('%d.%m.%Y')
                }
                for row in rows
            ]

        elif notification_type == 'inactive':
            # Пользователи, не посещавшие 7 дней
            target_date = datetime.utcnow() - timedelta(days=7)
            result = await session.execute(
                select(User, Visit)
                .outerjoin(Visit, User.user_id == Visit.user_id)
                .where(User.is_active == True)
            )
            rows = result.all()

            inactive_users = []
            user_last_visits = {}

            for row in rows:
                user_id = row.User.user_id
                if user_id not in user_last_visits:
                    user_last_visits[user_id] = {
                        'user': row.User,
                        'last_visit': None
                    }
                if row.Visit and (
                    user_last_visits[user_id]['last_visit'] is None or
                    row.Visit.visit_date > user_last_visits[user_id]['last_visit']
                ):
                    user_last_visits[user_id]['last_visit'] = row.Visit.visit_date

            for user_id, data in user_last_visits.items():
                if data['last_visit'] and data['last_visit'] < target_date:
                    inactive_users.append({
                        'user_id': user_id,
                        'name': data['user'].name,
                        'last_visit_date': data['last_visit'].strftime('%d.%m.%Y')
                    })

            return inactive_users

        elif notification_type == 'expired':
            # Абонементы, истёкшие 7 дней назад
            target_date = datetime.utcnow() - timedelta(days=7)
            result = await session.execute(
                select(Subscription, User)
                .join(User, Subscription.user_id == User.user_id)
                .where(
                    Subscription.is_active == False,
                    Subscription.end_date <= target_date,
                    Subscription.end_date > target_date - timedelta(days=1)
                )
            )
            rows = result.all()
            return [
                {
                    'user_id': row.User.user_id,
                    'name': row.User.name
                }
                for row in rows
            ]

    return []


async def send_expiring_notifications(bot: Bot):
    """Уведомления об истекающих абонементах"""
    users = await get_users_for_notification('expiring')

    for user in users:
        text = f"""
Привет, {user['name']}!

Твой абонемент заканчивается через 3 дня ({user['end_date']}).

Продли сейчас со СКИДКОЙ:
- В одну группу: {config.PRICES['renewal_one']}₽ вместо {config.PRICES['one_group']}₽
- Во все группы: {config.PRICES['renewal_all']}₽ вместо {config.PRICES['all_groups']}₽

Скидка только до конца месяца!
        """

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"Продлить в одну группу ({config.PRICES['renewal_one']}₽)",
                    callback_data="renew_one_group"
                )],
                [InlineKeyboardButton(
                    text=f"Продлить во все группы ({config.PRICES['renewal_all']}₽)",
                    callback_data="renew_all_groups"
                )]
            ]
        )

        try:
            await bot.send_message(user['user_id'], text, reply_markup=keyboard)
        except Exception as e:
            print(f"Ошибка отправки уведомления пользователю {user['user_id']}: {e}")


async def send_inactive_notifications(bot: Bot):
    """Уведомления неактивным клиентам (не был 7 дней)"""
    users = await get_users_for_notification('inactive')

    for user in users:
        text = f"""
Привет, {user['name']}!

Заметила, что ты давно не была на тренировках (последний раз — {user['last_visit_date']}).

Всё хорошо? Может, не подходит расписание?

Напиши, если нужна помощь!
        """

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Записаться на тренировку", callback_data="book_training")]
            ]
        )

        try:
            await bot.send_message(user['user_id'], text, reply_markup=keyboard)
        except Exception as e:
            print(f"Ошибка отправки уведомления пользователю {user['user_id']}: {e}")


async def send_comeback_notifications(bot: Bot):
    """Уведомления возврата (абонемент истёк 7 дней назад)"""
    users = await get_users_for_notification('expired')

    for user in users:
        text = f"""
Соскучились!

Прошла неделя с окончания твоего абонемента.

Возвращайся со скидкой!

- В одну группу: {config.PRICES['renewal_one']}₽ вместо {config.PRICES['one_group']}₽
- Во все группы: {config.PRICES['renewal_all']}₽ вместо {config.PRICES['all_groups']}₽

Предложение действует 3 дня!
        """

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"В одну группу ({config.PRICES['renewal_one']}₽)",
                    callback_data="comeback_one_group"
                )],
                [InlineKeyboardButton(
                    text=f"Во все группы ({config.PRICES['renewal_all']}₽)",
                    callback_data="comeback_all_groups"
                )]
            ]
        )

        try:
            await bot.send_message(user['user_id'], text, reply_markup=keyboard)
        except Exception as e:
            print(f"Ошибка отправки уведомления пользователю {user['user_id']}: {e}")


async def send_training_reminders(bot: Bot):
    """Напоминания о тренировках (за 2 часа)"""
    now = datetime.now()
    reminder_time = now + timedelta(hours=2)

    # Временное окно: от 1 ч 50 мин до 2 ч 10 мин до тренировки
    window_start = now + timedelta(hours=1, minutes=50)
    window_end = now + timedelta(hours=2, minutes=10)

    async with async_session() as session:
        # Получаем записи на ближайшие тренировки
        result = await session.execute(
            select(Booking, Training, User)
            .join(Training, Booking.training_id == Training.id)
            .join(User, Booking.user_id == User.user_id)
            .where(
                Booking.status == 'active',
                Booking.booking_date >= window_start,
                Booking.booking_date <= window_end
            )
        )
        rows = result.all()

    for row in rows:
        booking = row.Booking
        training = row.Training
        user = row.User

        training_type_text = "онлайн" if training.training_type == "online" else "в студии"
        text = f"""
Привет, {user.name}!

Напоминаю о тренировке через 2 часа:

{training.name}
Время: {booking.booking_date.strftime('%H:%M')}
Формат: {training_type_text}
"""

        if training.training_type == "online":
            text += "\nСсылка на Zoom будет отправлена за 10 минут до начала."
        else:
            text += f"\nАдрес: {config.STUDIO_ADDRESS}"

        text += "\n\nЖдём тебя!"

        try:
            await bot.send_message(user.user_id, text)
        except Exception as e:
            print(f"Ошибка отправки напоминания пользователю {user.user_id}: {e}")
