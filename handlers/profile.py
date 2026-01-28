from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from datetime import datetime

from database import get_user, get_active_subscription, get_user_payments, get_user_visits, get_user_active_bookings, async_session, Payment
import config

router = Router()


@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message):
    """Профиль пользователя"""

    user = await get_user(message.from_user.id)
    subscription = await get_active_subscription(message.from_user.id)

    if not user:
        await message.answer("❌ Ошибка: пользователь не найден")
        return

    # Формируем текст профиля
    text = f"""
👤 ТВОЙ ПРОФИЛЬ

📛 Имя: {user['name'] or 'Не указано'}
📅 С нами с: {user['reg_date'][:10] if user['reg_date'] else 'Неизвестно'}
"""

    # Если есть активный абонемент
    if subscription:
        end_date = datetime.strptime(subscription['end_date'], '%Y-%m-%d')
        days_left = (end_date - datetime.now()).days

        sub_names = {
            'one_group': 'В одну группу',
            'all_groups': 'Во все группы'
        }

        text += f"""
💎 ТЕКУЩИЙ АБОНЕМЕНТ:
• {sub_names.get(subscription['type'], subscription['type'])}
• Действует до: {subscription['end_date']}
• Осталось: {days_left} дн.
"""
    else:
        text += """
💎 Абонемент: Нет активного

🎯 Купи абонемент в разделе "Занятия в студии"!
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Записаться на тренировку", callback_data="book_start")],
            [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_bookings")],
            [InlineKeyboardButton(text="📜 История покупок", callback_data="purchase_history")],
            [InlineKeyboardButton(text="📞 Связаться с тренером", callback_data="contact_trainer")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
        ]
    )

    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


DAYS_RU = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']


@router.callback_query(F.data == "my_bookings")
async def my_bookings(callback: CallbackQuery):
    """Список активных записей пользователя"""
    await callback.answer()

    bookings = await get_user_active_bookings(callback.from_user.id)

    if not bookings:
        text = "📋 МОИ ЗАПИСИ\n\nУ тебя нет предстоящих записей."
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📝 Записаться на тренировку", callback_data="book_start")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_profile")]
            ]
        )
        await callback.message.edit_text(text, reply_markup=keyboard)
        return

    text = "📋 МОИ ЗАПИСИ\n\n"
    buttons = []

    for b in bookings:
        dow = b['booking_date'].weekday()
        date_str = b['booking_date'].strftime('%d.%m.%Y')
        text += (
            f"• {b['training_name']} — {b['trainer']}\n"
            f"  {DAYS_RU[dow]}, {date_str} в {b['training_time']}\n\n"
        )
        buttons.append([InlineKeyboardButton(
            text=f"❌ Отменить: {b['training_name']} {date_str} {b['training_time']}",
            callback_data=f"cancel_book:{b['booking_id']}"
        )])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_profile")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "contact_trainer")
async def contact_trainer(callback: CallbackQuery, bot: Bot):
    """Запрос на связь с тренером — отправляет заявку админу"""
    user = callback.from_user
    username_str = f"@{user.username}" if user.username else f"id:{user.id}"

    # Сообщение клиенту
    response_text = (
        "📞 ЗАПРОС ОТПРАВЛЕН\n\n"
        "Тренер получил твой запрос и свяжется с тобой в ближайшее время!"
    )
    try:
        await callback.message.edit_text(response_text)
    except Exception:
        await callback.message.answer(response_text)
    await callback.answer()

    # Заявка админу
    admin_text = (
        f"📞 ЗАПРОС НА СВЯЗЬ\n\n"
        f"👤 {user.full_name} ({username_str})\n"
        f"🆔 ID: {user.id}\n\n"
        f"Клиент хочет связаться с тренером."
    )
    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Связаться", url=f"tg://user?id={user.id}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"contact_reject_{user.id}")],
        ]
    )

    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text, reply_markup=admin_keyboard)
        except Exception:
            pass


@router.callback_query(F.data.startswith("contact_reject_"))
async def contact_reject(callback: CallbackQuery, bot: Bot):
    """Админ отклонил запрос на связь"""
    user_id = int(callback.data.split("_")[-1])

    await callback.message.edit_text(
        callback.message.text + "\n\n❌ Отклонено."
    )
    await callback.answer("Отклонено")

    try:
        await bot.send_message(
            user_id,
            "К сожалению, тренер сейчас не может связаться.\n"
            "Попробуй позже или напиши напрямую: " + config.ADMIN_PHONE
        )
    except Exception:
        pass


@router.callback_query(F.data == "purchase_history")
async def purchase_history(callback: CallbackQuery):
    """История покупок"""

    user_id = callback.from_user.id
    payments = await get_user_payments(user_id)
    visits = await get_user_visits(user_id)

    text = "📜 ИСТОРИЯ ПОКУПОК\n\n"

    # История платежей
    if payments:
        text += "💳 ПЛАТЕЖИ:\n"
        status_names = {
            'pending': '⏳ Ожидает',
            'confirmed': '✅ Подтверждён',
            'cancelled': '❌ Отменён'
        }
        type_names = {
            'one_group': 'Абонемент в одну группу',
            'all_groups': 'Абонемент во все группы',
            'single': 'Разовое занятие'
        }
        for p in payments[:10]:  # Показываем последние 10
            date_str = p['created_at'].strftime('%d.%m.%Y') if p['created_at'] else 'Н/Д'
            status = status_names.get(p['status'], p['status'])
            p_type = type_names.get(p['payment_type'], p['payment_type'] or 'Платёж')
            text += f"• {date_str} - {p_type} - {p['amount']}₽ {status}\n"
    else:
        text += "💳 Платежей пока нет\n"

    text += "\n"

    # История посещений
    if visits:
        text += "🏋️ ПОСЕЩЕНИЯ:\n"
        for v in visits[:10]:  # Показываем последние 10
            date_str = v['visit_date'].strftime('%d.%m.%Y') if v['visit_date'] else 'Н/Д'
            text += f"• {date_str} - {v['training_name']}\n"
    else:
        text += "🏋️ Посещений пока нет\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_profile")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "back_profile")
async def back_to_profile(callback: CallbackQuery):
    """Возврат в профиль"""

    user = await get_user(callback.from_user.id)
    subscription = await get_active_subscription(callback.from_user.id)

    text = f"""
👤 ТВОЙ ПРОФИЛЬ

📛 Имя: {user['name'] or 'Не указано'}
📅 С нами с: {user['reg_date'][:10] if user['reg_date'] else 'Неизвестно'}
"""

    if subscription:
        end_date = datetime.strptime(subscription['end_date'], '%Y-%m-%d')
        days_left = (end_date - datetime.now()).days

        sub_names = {
            'one_group': 'В одну группу',
            'all_groups': 'Во все группы'
        }

        text += f"""
💎 ТЕКУЩИЙ АБОНЕМЕНТ:
• {sub_names.get(subscription['type'], subscription['type'])}
• Действует до: {subscription['end_date']}
• Осталось: {days_left} дн.
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Записаться на тренировку", callback_data="book_start")],
            [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_bookings")],
            [InlineKeyboardButton(text="📜 История покупок", callback_data="purchase_history")],
            [InlineKeyboardButton(text="📞 Связаться с тренером", callback_data="contact_trainer")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()
