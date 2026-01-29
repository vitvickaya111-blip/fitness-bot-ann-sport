from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import async_session, Payment, Subscription, User, get_all_clients, get_sales_stats, get_detailed_sales_stats, get_users_for_broadcast, get_today_bookings, mark_visit, get_recent_payments, get_recent_bookings
from utils.scheduler import schedule_menu_retry, schedule_video_funnel


class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    confirm_broadcast = State()


class PriceEditStates(StatesGroup):
    waiting_for_price = State()


class ScheduleEditStates(StatesGroup):
    waiting_for_text = State()
from keyboards.main import main_keyboard
from sqlalchemy import select
from datetime import datetime
import calendar
import os
import config

router = Router()


def is_admin(user_id: int) -> bool:
    """Проверка является ли пользователь админом"""
    return user_id in config.ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Админ-панель"""

    if not is_admin(message.from_user.id):
        await message.answer("❌ У тебя нет доступа к админ-панели")
        return

    text = """
🔧 АДМИН-ПАНЕЛЬ

Выбери действие: 👇
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="👥 Клиенты", callback_data="admin_clients")],
            [InlineKeyboardButton(text="✅ Отметка посещений", callback_data="admin_attendance")],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")]
        ]
    )

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "admin_stats")
async def admin_statistics(callback: CallbackQuery):
    """Статистика продаж"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    stats = await get_detailed_sales_stats()

    # Названия типов продуктов
    type_names = {
        'one_group': 'Абонемент (одна группа)',
        'all_groups': 'Абонемент (все группы)',
        'single': 'Разовое занятие',
        'menu': 'Меню на похудение',
        'menu_1200_week': 'Меню 1200 ккал (неделя)',
        'menu_1200_month': 'Меню 1200 ккал (месяц)',
        'menu_1500_week': 'Меню 1500 ккал (неделя)',
        'menu_1500_month': 'Меню 1500 ккал (месяц)',
        'menu_drying_week': 'Меню на сушку (неделя)',
        'menu_drying_month': 'Меню на сушку (месяц)',
        'plan': 'План тренировок',
        'video': 'Онлайн-тренировка',
        'mentoring': 'Наставничество',
        'other': 'Другое'
    }

    text = f"""
📊 СТАТИСТИКА ЗА ТЕКУЩИЙ МЕСЯЦ

💰 Общий доход: {stats['total_income']}₽
📈 Всего продаж: {stats['total_sales']}

👥 Всего клиентов: {stats['total_users']}
✅ С активным абонементом: {stats['active_subscriptions']}

📦 ПО ПРОДУКТАМ:
"""

    if stats['by_type']:
        for p_type, data in stats['by_type'].items():
            name = type_names.get(p_type, p_type)
            text += f"• {name}: {data['count']} шт. — {data['amount']}₽\n"
    else:
        text += "Пока нет продаж\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Покупки", callback_data="admin_purchases")],
            [InlineKeyboardButton(text="📝 Записи на тренировки", callback_data="admin_bookings_list")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_purchases")
async def admin_purchases(callback: CallbackQuery):
    """Последние покупки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    type_names = {
        'one_group': 'Абонемент (одна группа)',
        'all_groups': 'Абонемент (все группы)',
        'single': 'Разовое занятие',
        'menu': 'Меню на похудение',
        'menu_1200_week': 'Меню 1200 ккал (неделя)',
        'menu_1200_month': 'Меню 1200 ккал (месяц)',
        'menu_1500_week': 'Меню 1500 ккал (неделя)',
        'menu_1500_month': 'Меню 1500 ккал (месяц)',
        'menu_drying_week': 'Меню на сушку (неделя)',
        'menu_drying_month': 'Меню на сушку (месяц)',
        'plan': 'План тренировок',
        'video': 'Онлайн-тренировка',
        'mentoring': 'Наставничество',
    }

    payments = await get_recent_payments(15)

    if not payments:
        text = "🛒 ПОСЛЕДНИЕ ПОКУПКИ\n\nПока нет подтверждённых покупок."
    else:
        text = "🛒 ПОСЛЕДНИЕ ПОКУПКИ\n\n"
        for p in payments:
            username = f" (@{p['username']})" if p['username'] else ""
            product = type_names.get(p['payment_type'], p['payment_type'] or 'Другое')
            date_str = p['created_at'].strftime('%d.%m') if p['created_at'] else ''
            text += f"• {p['name']}{username} — {product} — {int(p['amount'])}₽ — {date_str}\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_stats")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_bookings_list")
async def admin_bookings_list_handler(callback: CallbackQuery):
    """Последние записи на тренировки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    bookings = await get_recent_bookings(15)

    if not bookings:
        text = "📝 ПОСЛЕДНИЕ ЗАПИСИ\n\nПока нет записей на тренировки."
    else:
        text = "📝 ПОСЛЕДНИЕ ЗАПИСИ\n\n"
        for b in bookings:
            username = f" (@{b['username']})" if b['username'] else ""
            date_str = b['created_at'].strftime('%d.%m') if b['created_at'] else ''
            text += f"• {b['name']}{username} → {b['training_name']} — {date_str}\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_stats")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_clients")
async def admin_clients_list(callback: CallbackQuery):
    """Список клиентов"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    clients = await get_all_clients()

    if not clients:
        text = "📋 Список клиентов пуст"
    else:
        text = f"👥 СПИСОК КЛИЕНТОВ ({len(clients)} чел.)\n\n"

        for client in clients[:10]:
            status = "✅" if client['sub_type'] else "❌"
            text += f"{status} {client['name'] or 'Без имени'} (@{client['username'] or 'нет'})\n"
            if client['end_date']:
                text += f"   Абонемент до: {client['end_date']}\n"
            text += "\n"

        if len(clients) > 10:
            text += f"... и ещё {len(clients) - 10} чел."

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_menu(callback: CallbackQuery):
    """Меню рассылки"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    # Получаем количество пользователей в каждом сегменте
    all_users = await get_users_for_broadcast('all')
    with_sub = await get_users_for_broadcast('with_sub')
    without_sub = await get_users_for_broadcast('without_sub')

    text = f"""
📢 РАССЫЛКА

Выбери аудиторию для рассылки:

👥 Всем клиентам: {len(all_users)} чел.
✅ С абонементом: {len(with_sub)} чел.
❌ Без абонемента: {len(without_sub)} чел.
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"👥 Всем ({len(all_users)})", callback_data="broadcast_all")],
            [InlineKeyboardButton(text=f"✅ С абонементом ({len(with_sub)})", callback_data="broadcast_with_sub")],
            [InlineKeyboardButton(text=f"❌ Без абонемента ({len(without_sub)})", callback_data="broadcast_without_sub")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("broadcast_"))
async def select_broadcast_segment(callback: CallbackQuery, state: FSMContext):
    """Выбор сегмента для рассылки"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    segment = callback.data.replace("broadcast_", "")

    segment_names = {
        'all': 'всем клиентам',
        'with_sub': 'клиентам с абонементом',
        'without_sub': 'клиентам без абонемента'
    }

    users = await get_users_for_broadcast(segment)

    if not users:
        await callback.answer("❌ Нет пользователей в этом сегменте", show_alert=True)
        return

    await state.update_data(segment=segment, user_count=len(users))
    await state.set_state(BroadcastStates.waiting_for_message)

    text = f"""
📢 РАССЫЛКА — {segment_names.get(segment, segment)}

👥 Получателей: {len(users)} чел.

✏️ Напиши текст сообщения для рассылки:

(Можно использовать форматирование: *жирный*, _курсив_)
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.message(BroadcastStates.waiting_for_message)
async def receive_broadcast_message(message: Message, state: FSMContext):
    """Получение текста рассылки"""

    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    segment = data.get('segment', 'all')
    user_count = data.get('user_count', 0)

    await state.update_data(broadcast_text=message.text)
    await state.set_state(BroadcastStates.confirm_broadcast)

    segment_names = {
        'all': 'всем клиентам',
        'with_sub': 'клиентам с абонементом',
        'without_sub': 'клиентам без абонемента'
    }

    text = f"""
📢 ПОДТВЕРЖДЕНИЕ РАССЫЛКИ

👥 Аудитория: {segment_names.get(segment, segment)}
📊 Получателей: {user_count} чел.

📝 Текст сообщения:
─────────────────
{message.text}
─────────────────

Отправить рассылку?
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_send_broadcast")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")]
        ]
    )

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "confirm_send_broadcast", BroadcastStates.confirm_broadcast)
async def send_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отправка рассылки"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    data = await state.get_data()
    segment = data.get('segment', 'all')
    broadcast_text = data.get('broadcast_text', '')

    users = await get_users_for_broadcast(segment)

    await callback.message.edit_text("⏳ Отправка рассылки...")

    success = 0
    failed = 0

    for user_id in users:
        try:
            await bot.send_message(user_id, broadcast_text, parse_mode="Markdown")
            success += 1
        except Exception as e:
            failed += 1
            print(f"Ошибка отправки {user_id}: {e}")

    await state.clear()

    text = f"""
✅ РАССЫЛКА ЗАВЕРШЕНА

📊 Статистика:
• Успешно: {success}
• Ошибки: {failed}
• Всего: {len(users)}
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ В админку", callback_data="back_admin")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    """Отмена рассылки"""

    await state.clear()

    text = """
🔧 АДМИН-ПАНЕЛЬ

Выбери действие: 👇
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="👥 Клиенты", callback_data="admin_clients")],
            [InlineKeyboardButton(text="✅ Отметка посещений", callback_data="admin_attendance")],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer("Рассылка отменена")


PRICE_NAMES = {
    'single': 'Разовое занятие',
    'one_group': 'Абонемент (одна группа)',
    'all_groups': 'Абонемент (все группы)',
    'renewal_one': 'Продление (одна группа)',
    'renewal_all': 'Продление (все группы)',
    'menu': 'Меню на похудение',
    'menu_1200_week': 'Меню 1200 ккал (неделя)',
    'menu_1200_month': 'Меню 1200 ккал (месяц)',
    'menu_1500_week': 'Меню 1500 ккал (неделя)',
    'menu_1500_month': 'Меню 1500 ккал (месяц)',
    'menu_drying_week': 'Меню на сушку (неделя)',
    'menu_drying_month': 'Меню на сушку (месяц)',
    'plan': 'План тренировок',
    'video_call': 'Онлайн-тренировка',
    'mentoring': 'Наставничество',
}


@router.callback_query(F.data == "admin_settings")
async def admin_settings(callback: CallbackQuery):
    """Настройки бота — список цен с кнопками редактирования"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    text = "⚙️ НАСТРОЙКИ\n\nВыбери раздел:\n"

    buttons = [
        [InlineKeyboardButton(text="📅 Расписание", callback_data="admin_schedule")],
    ]

    for key, name in PRICE_NAMES.items():
        price = config.PRICES.get(key, 0)
        buttons.append([InlineKeyboardButton(
            text=f"💰 {name}: {price}₽",
            callback_data=f"price_edit:{key}"
        )])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("price_edit:"))
async def price_edit_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования цены"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    key = callback.data.split(":")[1]
    name = PRICE_NAMES.get(key, key)
    current = config.PRICES.get(key, 0)

    await state.set_state(PriceEditStates.waiting_for_price)
    await state.update_data(price_key=key)

    text = (
        f"✏️ Изменение цены\n\n"
        f"📦 {name}\n"
        f"💰 Текущая цена: {current}₽\n\n"
        f"Введи новую цену (число):"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_settings")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.message(PriceEditStates.waiting_for_price)
async def price_edit_receive(message: Message, state: FSMContext):
    """Получение новой цены"""

    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    try:
        new_price = int(text)
        if new_price < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи корректное положительное число.")
        return

    data = await state.get_data()
    key = data['price_key']
    name = PRICE_NAMES.get(key, key)
    old_price = config.PRICES.get(key, 0)

    config.PRICES[key] = new_price
    config.save_prices()

    await state.clear()

    await message.answer(
        f"✅ Цена обновлена!\n\n"
        f"📦 {name}\n"
        f"💰 {old_price}₽ → {new_price}₽"
    )


DAY_NAMES = {
    'monday': 'Понедельник',
    'tuesday': 'Вторник',
    'wednesday': 'Среда',
    'thursday': 'Четверг',
    'friday': 'Пятница',
    'saturday': 'Суббота',
    'sunday': 'Воскресенье',
}


@router.callback_query(F.data == "admin_schedule")
async def admin_schedule(callback: CallbackQuery):
    """Меню редактирования расписания"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    text = "📅 РАСПИСАНИЕ\n\nВыбери день для редактирования:\n"

    buttons = []
    for key, name in DAY_NAMES.items():
        buttons.append([InlineKeyboardButton(
            text=f"📅 {name}",
            callback_data=f"sched_edit:{key}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_settings")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("sched_edit:"))
async def schedule_edit_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования расписания для дня"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    day = callback.data.split(":")[1]
    name = DAY_NAMES.get(day, day)
    current = config.SCHEDULE.get(day, "(пусто)")

    await state.set_state(ScheduleEditStates.waiting_for_text)
    await state.update_data(schedule_day=day)

    text = (
        f"✏️ Редактирование: {name}\n\n"
        f"📋 Текущий текст:\n{current}\n\n"
        f"Введи новый текст расписания для этого дня:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_schedule")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.message(ScheduleEditStates.waiting_for_text)
async def schedule_edit_receive(message: Message, state: FSMContext):
    """Получение нового текста расписания"""
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    day = data['schedule_day']
    name = DAY_NAMES.get(day, day)

    config.SCHEDULE[day] = message.text.strip()
    config.save_schedule()

    await state.clear()

    await message.answer(
        f"✅ Расписание обновлено!\n\n"
        f"📅 {name}\n"
        f"📋 Новый текст:\n{config.SCHEDULE[day]}"
    )


@router.callback_query(F.data == "back_admin")
async def back_to_admin(callback: CallbackQuery):
    """Возврат в админку"""

    text = """
🔧 АДМИН-ПАНЕЛЬ

Выбери действие: 👇
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="👥 Клиенты", callback_data="admin_clients")],
            [InlineKeyboardButton(text="✅ Отметка посещений", callback_data="admin_attendance")],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm_payment(callback: CallbackQuery):
    """Подтверждение оплаты админом"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return

    payment_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            await callback.answer("Платёж не найден")
            return

        payment.status = 'confirmed'
        payment.confirmed_at = datetime.utcnow()

        # Создаём абонемент если это абонемент
        if payment.amount in [3500, 6000]:
            sub_type = "one_group" if payment.amount == 3500 else "all_groups"

            now = datetime.utcnow()
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_day = calendar.monthrange(now.year, now.month)[1]
            end_date = now.replace(day=last_day, hour=23, minute=59, second=59)

            subscription = Subscription(
                user_id=payment.user_id,
                subscription_type=sub_type,
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )
            session.add(subscription)

        await session.commit()

    # Уведомляем пользователя с персонализированным cross-sell
    try:
        if payment.payment_type in ('one_group', 'all_groups'):
            cross_sell_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📝 Записаться на тренировку", callback_data="book_start")],
                    [InlineKeyboardButton(text="📋 Меню питания", callback_data="online_menu")],
                    [InlineKeyboardButton(text="💪 План тренировок", callback_data="online_plan")],
                ]
            )
            await callback.bot.send_message(
                payment.user_id,
                "✅ Абонемент активирован, спасибо!\n\n"
                "Запишись на ближайшую тренировку. Для лучшего результата "
                "может пригодиться меню питания или план тренировок 👇",
                reply_markup=cross_sell_kb
            )

        elif payment.payment_type == 'single':
            cross_sell_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📝 Записаться на тренировку", callback_data="book_start")],
                    [InlineKeyboardButton(text="💎 Узнать про абонемент", callback_data="studio_subscription")],
                ]
            )
            await callback.bot.send_message(
                payment.user_id,
                "✅ Оплата разового занятия подтверждена, спасибо!\n\n"
                "Запишись на тренировку 👇\n"
                "Посмотри, если интересно — с абонементом выгоднее",
                reply_markup=cross_sell_kb
            )

        elif payment.payment_type == 'plan':
            cross_sell_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📋 Меню питания", callback_data="online_menu")],
                    [InlineKeyboardButton(text="💎 Абонемент", callback_data="studio_subscription")],
                ]
            )
            await callback.bot.send_message(
                payment.user_id,
                "✅ Оплата плана подтверждена, спасибо!\n\n"
                "Скоро свяжусь с тобой и составим план под тебя.\n"
                "Для лучшего результата может пригодиться меню питания 👇",
                reply_markup=cross_sell_kb
            )

        elif payment.payment_type == 'video':
            cross_sell_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📋 Меню питания", callback_data="online_menu")],
                    [InlineKeyboardButton(text="💪 План тренировок", callback_data="online_plan")],
                    [InlineKeyboardButton(text="👥 Наставничество", callback_data="online_mentoring")],
                ]
            )
            await callback.bot.send_message(
                payment.user_id,
                "✅ Оплата онлайн-тренировки подтверждена, спасибо!\n\n"
                "Скоро свяжусь с тобой и согласуем удобное время.\n\n"
                "А пока посмотри, если интересно 👇",
                reply_markup=cross_sell_kb
            )
            # Запускаем воронку follow-up сообщений
            schedule_video_funnel(callback.bot, payment.user_id)

        elif payment.payment_type == 'mentoring':
            cross_sell_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📋 Меню питания", callback_data="online_menu")],
                    [InlineKeyboardButton(text="🔄 До и после", callback_data="before_after")],
                    [InlineKeyboardButton(text="🙋‍♀️ Обо мне", callback_data="about_me")],
                ]
            )
            await callback.bot.send_message(
                payment.user_id,
                "✅ Оплата наставничества подтверждена, спасибо!\n\n"
                "Скоро свяжусь с тобой для начала работы.\n\n"
                "А пока посмотри, может пригодиться 👇",
                reply_markup=cross_sell_kb
            )

        elif payment.payment_type and payment.payment_type.startswith('menu'):
            # Для меню — базовое подтверждение, cross-sell после PDF
            await callback.bot.send_message(
                payment.user_id,
                "✅ Оплата меню подтверждена, спасибо!\n\n"
                "Отправляю файл..."
            )

        else:
            await callback.bot.send_message(
                payment.user_id,
                "✅ Твоя оплата подтверждена! Спасибо!",
            )

    except Exception as e:
        import logging
        logging.error(f"Ошибка уведомления пользователя: {e}")

    # Доставка продукта
    base_dir = os.path.dirname(os.path.dirname(__file__))
    menu_files = {
            'menu': {
                'path': os.path.join(base_dir, "Меню на похудение .pdf"),
                'caption': "📋 Вот твоё меню на похудение! Если будут вопросы — пиши!"
            },
            'menu_1200_week': {
                'path': os.path.join(base_dir, "меню_1200", "Питание_1200ккал_НЕДЕЛЯ.pdf"),
                'caption': "📋 Вот твоё меню на 1200 ккал (неделя)! Если будут вопросы — пиши!"
            },
            'menu_1200_month': {
                'path': os.path.join(base_dir, "меню_1200_месяц", "Меню_1200ккал_НА_МЕСЯЦ.pdf"),
                'caption': "📋 Вот твоё меню на 1200 ккал (месяц)! Если будут вопросы — пиши!"
            },
            'menu_1500_week': {
                'path': os.path.join(base_dir, "меню_1500_неделя", "Меню_1500ккал_НЕДЕЛЯ.pdf"),
                'caption': "📋 Вот твоё меню на 1500 ккал (неделя)! Если будут вопросы — пиши!"
            },
            'menu_1500_month': {
                'path': os.path.join(base_dir, "меню_1500_месяц", "Меню_1500ккал_НА_МЕСЯЦ.pdf"),
                'caption': "📋 Вот твоё меню на 1500 ккал (месяц)! Если будут вопросы — пиши!"
            },
            'menu_drying_week': {
                'path': os.path.join(base_dir, "меню_сушка_неделя", "Меню_СУШКА_НА_НЕДЕЛЮ.pdf"),
                'caption': "📋 Вот твоё меню на сушку (неделя)! Если будут вопросы — пиши!"
            },
            'menu_drying_month': {
                'path': os.path.join(base_dir, "меню_сушка_месяц", "Меню_СУШКА_НА_МЕСЯЦ.pdf"),
                'caption': "📋 Вот твоё меню на сушку (месяц)! Если будут вопросы — пиши!"
            },
        }

    try:
        menu_info = menu_files.get(payment.payment_type)
        if menu_info:
            if menu_info['path'] and os.path.exists(menu_info['path']):
                menu_file = FSInputFile(menu_info['path'])
                await callback.bot.send_document(
                    payment.user_id,
                    document=menu_file,
                    caption=menu_info['caption']
                )
            else:
                await callback.bot.send_message(
                    payment.user_id,
                    menu_info['caption']
                )
    except Exception as e:
        import logging
        logging.error(f"Ошибка доставки продукта: {e}")
        # Запланировать повторную отправку
        menu_info = menu_files.get(payment.payment_type)
        if menu_info and menu_info['path']:
            import asyncio
            asyncio.create_task(
                schedule_menu_retry(callback.bot, payment.user_id, menu_info['path'], menu_info['caption'])
            )

    # Cross-sell после доставки меню
    if payment.payment_type and payment.payment_type.startswith('menu'):
        try:
            menu_cross_sell_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="💪 План тренировок", callback_data="online_plan")],
                    [InlineKeyboardButton(text="👥 Наставничество", callback_data="online_mentoring")],
                ]
            )
            await callback.bot.send_message(
                payment.user_id,
                "Для лучшего результата питание хорошо дополнить тренировками 👇",
                reply_markup=menu_cross_sell_kb
            )
        except Exception as e:
            import logging
            logging.error(f"Ошибка отправки cross-sell после меню: {e}")

    await callback.message.edit_text(
        f"✅ Оплата #{payment_id} подтверждена ({payment.amount}₽)."
    )
    await callback.answer("Подтверждено!")


@router.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_payment(callback: CallbackQuery):
    """Отклонение оплаты админом"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return

    payment_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = 'rejected'
            await session.commit()

            try:
                await callback.bot.send_message(
                    payment.user_id,
                    "К сожалению, оплата не прошла 😔\n\n"
                    "Не переживай — такое бывает! Попробуй оплатить ещё раз, "
                    "и если что-то не получится, мы обязательно поможем 🤗",
                    reply_markup=main_keyboard(),
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка уведомления пользователя: {e}")

    await callback.message.edit_text(f"❌ Оплата #{payment_id} отклонена.")
    await callback.answer("Отклонено")


# ─── Отметка посещений ─────────────────────────────────────────────
@router.callback_query(F.data == "admin_attendance")
async def admin_attendance(callback: CallbackQuery):
    """Список сегодняшних тренировок с записями"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    trainings = await get_today_bookings()

    if not trainings:
        text = "✅ ОТМЕТКА ПОСЕЩЕНИЙ\n\nНа сегодня записей нет."
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin")]]
        )
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        return

    today_str = datetime.now().strftime('%d.%m.%Y')
    text = f"✅ ОТМЕТКА ПОСЕЩЕНИЙ — {today_str}\n\n"

    buttons = []
    for t in trainings:
        text += f"🕐 {t['time']} — {t['training_name']} ({t['trainer']}): {len(t['clients'])} чел.\n"
        buttons.append([InlineKeyboardButton(
            text=f"{t['time']} {t['training_name']} ({len(t['clients'])})",
            callback_data=f"att_show:{t['training_id']}:{today_str}"
        )])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("att_show:"))
async def att_show_training(callback: CallbackQuery):
    """Список записавшихся на конкретную тренировку"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    parts = callback.data.split(":")
    training_id = int(parts[1])
    date_str = parts[2]

    trainings = await get_today_bookings()
    training_data = next((t for t in trainings if t['training_id'] == training_id), None)

    if not training_data:
        await callback.message.edit_text(
            "Записей на эту тренировку нет.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_attendance")]]
            )
        )
        await callback.answer()
        return

    text = (
        f"✅ {training_data['time']} — {training_data['training_name']} ({training_data['trainer']})\n"
        f"📅 {date_str}\n\n"
        f"Записано: {len(training_data['clients'])} чел.\n\n"
    )

    buttons = []
    for i, client in enumerate(training_data['clients'], 1):
        name = client['name'] or 'Без имени'
        username = f"@{client['username']}" if client['username'] else ''
        text += f"{i}. {name} {username}\n"
        buttons.append([InlineKeyboardButton(
            text=f"✅ Отметить: {name}",
            callback_data=f"att_mark:{client['booking_id']}:{client['user_id']}:{training_id}"
        )])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_attendance")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("att_mark:"))
async def att_mark_visit(callback: CallbackQuery):
    """Отметить посещение клиента"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    parts = callback.data.split(":")
    booking_id = int(parts[1])
    user_id = int(parts[2])
    training_id = int(parts[3])

    success = await mark_visit(booking_id, user_id, training_id)

    if success:
        await callback.answer("✅ Посещение отмечено!", show_alert=True)
    else:
        await callback.answer("❌ Запись не найдена или уже отмечена", show_alert=True)

    # Обновляем список — возвращаемся к списку тренировок
    today_str = datetime.now().strftime('%d.%m.%Y')
    trainings = await get_today_bookings()

    if not trainings:
        text = "✅ ОТМЕТКА ПОСЕЩЕНИЙ\n\nВсе посещения отмечены!"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin")]]
        )
    else:
        text = f"✅ ОТМЕТКА ПОСЕЩЕНИЙ — {today_str}\n\n"
        buttons = []
        for t in trainings:
            text += f"🕐 {t['time']} — {t['training_name']} ({t['trainer']}): {len(t['clients'])} чел.\n"
            buttons.append([InlineKeyboardButton(
                text=f"{t['time']} {t['training_name']} ({len(t['clients'])})",
                callback_data=f"att_show:{t['training_id']}:{today_str}"
            )])
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=keyboard)
