"""
Обработчики онлайн-тренировок
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.inline import online_menu_keyboard, subscription_keyboard, schedule_keyboard, payment_methods, payment_confirm_keyboard
from database import async_session, Training, Booking, Subscription
from schedule_data import SCHEDULE_TEXT
from sqlalchemy import select
from datetime import datetime, timedelta
import config

router = Router()


@router.message(F.text.in_({"📱 Онлайн-тренировки", "📱 Занятия онлайн"}))
async def online_menu(message: Message):
    """Меню онлайн-тренировок"""
    text = """
📱 ОНЛАЙН-ТРЕНИРОВКИ

Занимайся из любой точки мира! 🌍

Выбери что тебе нужно: 👇
    """
    await message.answer(text, reply_markup=online_menu_keyboard())


@router.message(F.text == "📋 Меню питания")
async def menu_from_main(message: Message):
    """Меню питания из главного меню"""
    text = (
        "📋 МЕНЮ ПИТАНИЯ\n\n"
        "Выбери подходящий вариант:\n\n"
        "🥗 Меню на похудение 1200 ккал\n"
        "Для быстрого снижения веса. Подходит при малоподвижном образе жизни.\n\n"
        "🥗 Меню на похудение 1500 ккал\n"
        "Комфортное похудение. Подходит при умеренной активности и тренировках.\n\n"
        "🔥 Меню на сушку\n"
        "Для тех, кто хочет снизить процент жира и подчеркнуть рельеф мышц."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🥗 Похудение 1200 ккал", callback_data="online_menu_1200")],
            [InlineKeyboardButton(text="🥗 Похудение 1500 ккал", callback_data="online_menu_1500")],
            [InlineKeyboardButton(text="🔥 Меню на сушку", callback_data="online_menu_drying")],
        ]
    )
    await message.answer(text, reply_markup=keyboard)


@router.message(F.text == "💪 План тренировок")
async def plan_from_main(message: Message):
    """План тренировок из главного меню"""
    text = (
        f"💪 ПЛАН ТРЕНИРОВОК\n\n"
        f"💰 Цена: {config.PRICES['plan']}₽\n\n"
        f"✨ Что входит:\n"
        f"✅ Индивидуальная программа тренировок\n"
        f"✅ Подбор упражнений под твои цели\n"
        f"✅ Видео с техникой выполнения\n"
        f"✅ Корректировка через 2 недели\n"
        f"✅ Поддержка в течение месяца\n\n"
        f"📲 После оплаты пришлю план в течение 24 часов!"
    )
    await message.answer(
        text,
        reply_markup=payment_methods(config.PRICES['plan'], 'plan')
    )


@router.message(F.text == "📹 Онлайн-тренировка")
async def video_from_main(message: Message):
    """Онлайн-тренировка из главного меню"""
    text = (
        f"📹 ОНЛАЙН-ТРЕНИРОВКА\n\n"
        f"Персональная тренировка со мной по видеосвязи в реальном времени.\n\n"
        f"💰 Цена: {config.PRICES['video_call']}₽ (60 минут)\n\n"
        f"✨ Что получишь:\n"
        f"✅ Индивидуальная программа\n"
        f"✅ Контроль техники\n"
        f"✅ Ответы на вопросы\n\n"
        f"После оплаты я свяжусь с тобой для согласования времени."
    )
    await message.answer(
        text,
        reply_markup=payment_methods(config.PRICES['video_call'], 'video')
    )


@router.message(F.text == "👥 Наставничество")
async def mentoring_from_main(message: Message):
    """Наставничество из главного меню"""
    text = (
        f"👥 НАСТАВНИЧЕСТВО\n\n"
        f"💰 Цена: {config.PRICES['mentoring']}₽\n\n"
        f"✨ Что входит:\n"
        f"✅ Индивидуальный план питания\n"
        f"✅ Персональная программа тренировок\n"
        f"✅ Еженедельные созвоны\n"
        f"✅ Ежедневная поддержка в чате\n"
        f"✅ Контроль прогресса\n"
        f"✅ Корректировка программы\n\n"
        f"📅 Длительность: 1 месяц\n\n"
        f"🔥 Самый эффективный формат для результата!"
    )
    await message.answer(
        text,
        reply_markup=payment_methods(config.PRICES['mentoring'], 'mentoring')
    )


@router.callback_query(F.data == "online_schedule")
async def online_schedule(callback: CallbackQuery):
    """Расписание онлайн-тренировок"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="online_back")]
        ]
    )

    await callback.message.edit_text(SCHEDULE_TEXT, reply_markup=keyboard, parse_mode='Markdown')
    await callback.answer()


@router.callback_query(F.data == "buy_online")
async def buy_online(callback: CallbackQuery):
    """Покупка онлайн абонемента"""
    text = """
АБОНЕМЕНТЫ НА ОНЛАЙН-ТРЕНИРОВКИ

Выбери подходящий вариант:
    """
    await callback.message.edit_text(text, reply_markup=subscription_keyboard("online"))
    await callback.answer()


@router.callback_query(F.data == "my_online_bookings")
async def my_online_bookings(callback: CallbackQuery):
    """Мои записи на онлайн-тренировки"""
    user_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(Booking).where(
                Booking.user_id == user_id,
                Booking.status == 'active'
            )
        )
        bookings = result.scalars().all()

    if not bookings:
        await callback.message.edit_text(
            "У тебя пока нет активных записей на онлайн-тренировки.",
            reply_markup=online_menu_keyboard()
        )
    else:
        text = "Твои записи на онлайн-тренировки:\n\n"
        for booking in bookings:
            text += f"- {booking.booking_date.strftime('%d.%m %H:%M')}\n"
        await callback.message.edit_text(text, reply_markup=online_menu_keyboard())

    await callback.answer()


@router.callback_query(F.data == "online_back")
async def online_back(callback: CallbackQuery):
    """Назад в меню онлайн"""
    await online_menu(callback.message)
    await callback.answer()


@router.callback_query(F.data == "online_video")
async def online_video_handler(callback: CallbackQuery):
    """Онлайн-тренировка по видеосвязи"""
    text = f"""
Онлайн-тренировка

Персональная тренировка со мной по видеосвязи в реальном времени.

Цена: {config.PRICES['video_call']}₽ (60 минут)

Что получишь:
- Индивидуальная программа
- Контроль техники
- Ответы на вопросы

После оплаты я свяжусь с тобой для согласования времени и пришлю ссылку на Zoom.
    """
    await callback.message.edit_text(
        text,
        reply_markup=payment_methods(config.PRICES['video_call'], 'video')
    )
    await callback.answer()



@router.callback_query(F.data == "online_menu")
async def online_menu_handler(callback: CallbackQuery):
    """Выбор типа меню питания"""

    text = """
📋 МЕНЮ ПИТАНИЯ

Выбери подходящий вариант:

🥗 Меню на похудение 1200 ккал
Для быстрого снижения веса. Подходит при малоподвижном образе жизни.

🥗 Меню на похудение 1500 ккал
Комфортное похудение. Подходит при умеренной активности и тренировках.

🔥 Меню на сушку
Для тех, кто хочет снизить процент жира и подчеркнуть рельеф мышц.
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🥗 Похудение 1200 ккал", callback_data="online_menu_1200")],
            [InlineKeyboardButton(text="🥗 Похудение 1500 ккал", callback_data="online_menu_1500")],
            [InlineKeyboardButton(text="🔥 Меню на сушку", callback_data="online_menu_drying")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_online")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


MENU_TYPES = {
    '1200': {
        'title': '🥗 МЕНЮ НА ПОХУДЕНИЕ — 1200 ККАЛ',
        'short': 'Похудение 1200 ккал',
        'desc': "Для быстрого снижения веса. Подходит при малоподвижном образе жизни.",
    },
    '1500': {
        'title': '🥗 МЕНЮ НА ПОХУДЕНИЕ — 1500 ККАЛ',
        'short': 'Похудение 1500 ккал',
        'desc': "Комфортное похудение при умеренной активности и тренировках.",
    },
    'drying': {
        'title': '🔥 МЕНЮ НА СУШКУ',
        'short': 'Меню на сушку',
        'desc': "Снижение процента жира и рельеф мышц. Высокобелковый рацион.",
    },
}


@router.callback_query(F.data.in_({"online_menu_1200", "online_menu_1500", "online_menu_drying"}))
async def online_menu_period(callback: CallbackQuery):
    """Выбор периода меню — неделя или месяц"""
    menu_code = callback.data.replace("online_menu_", "")  # 1200 / 1500 / drying
    info = MENU_TYPES[menu_code]

    price_week = config.PRICES[f'menu_{menu_code}_week']
    price_month = config.PRICES[f'menu_{menu_code}_month']

    text = (
        f"{info['title']}\n\n"
        f"{info['desc']}\n\n"
        f"✅ Сбалансированное БЖУ\n"
        f"✅ Список продуктов\n"
        f"✅ Рецепты на каждый день\n\n"
        f"Выбери период:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"📅 На неделю — {price_week}₽",
                callback_data=f"menubuy_{menu_code}_week_{price_week}"
            )],
            [InlineKeyboardButton(
                text=f"📆 На месяц — {price_month}₽",
                callback_data=f"menubuy_{menu_code}_month_{price_month}"
            )],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="online_menu")],
        ]
    )

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("menubuy_"))
async def online_menu_buy(callback: CallbackQuery):
    """Оплата выбранного меню"""
    # menubuy_1200_week_5000
    parts = callback.data.split("_")
    menu_code = parts[1]       # 1200 / 1500 / drying
    period = parts[2]          # week / month
    price = int(parts[3])

    info = MENU_TYPES[menu_code]
    period_text = "на неделю" if period == "week" else "на месяц"
    product_key = f"menu_{menu_code}_{period}"

    text = (
        f"{info['title']} ({period_text})\n\n"
        f"💰 Цена: {price}₽\n\n"
        f"📲 После оплаты пришлю меню в течение 24 часов!"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить по реквизитам", callback_data=f"pay_card_{product_key}_{price}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"online_menu_{menu_code}")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "online_plan")
async def online_plan_handler(callback: CallbackQuery):
    """План тренировок"""

    text = f"""
💪 ПЛАН ТРЕНИРОВОК

💰 Цена: {config.PRICES['plan']}₽

✨ Что входит:
✅ Индивидуальная программа тренировок
✅ Подбор упражнений под твои цели
✅ Видео с техникой выполнения
✅ Корректировка через 2 недели
✅ Поддержка в течение месяца

📲 После оплаты пришлю план в течение 24 часов!
    """

    await callback.message.edit_text(
        text,
        reply_markup=payment_methods(config.PRICES['plan'], 'plan'),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "online_mentoring")
async def online_mentoring_handler(callback: CallbackQuery):
    """Наставничество"""

    text = f"""
👥 НАСТАВНИЧЕСТВО

💰 Цена: {config.PRICES['mentoring']}₽

✨ Что входит:
✅ Индивидуальный план питания
✅ Персональная программа тренировок
✅ Еженедельные созвоны
✅ Ежедневная поддержка в чате
✅ Контроль прогресса
✅ Корректировка программы

📅 Длительность: 1 месяц

🔥 Самый эффективный формат для результата!
    """

    await callback.message.edit_text(
        text,
        reply_markup=payment_methods(config.PRICES['mentoring'], 'mentoring'),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_online")
async def back_to_online(callback: CallbackQuery):
    """Возврат в меню онлайн-тренировок"""

    text = """
📱 ОНЛАЙН-ТРЕНИРОВКИ

Занимайся из любой точки мира! 🌍

Выбери что тебе нужно: 👇
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Меню питания", callback_data="online_menu")],
            [InlineKeyboardButton(text="💪 План тренировок — 5000₽", callback_data="online_plan")],
            [InlineKeyboardButton(text="📹 Онлайн-тренировка — 1000₽", callback_data="online_video")],
            [InlineKeyboardButton(text="👥 Наставничество — 10000₽", callback_data="online_mentoring")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()
