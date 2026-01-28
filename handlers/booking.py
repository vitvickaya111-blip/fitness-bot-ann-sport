"""
Обработчики записи на тренировку — полный флоу:
Тип → Тренер (для Силовой) → День → Время → Подтверждение → Готово
"""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

from database import (
    get_trainings_by_filter,
    get_training_by_id,
    get_bookings_count,
    check_user_booking,
    create_booking,
    cancel_booking,
)
import config

router = Router()

DAYS_RU = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
DAYS_SHORT = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

# Маппинг коротких кодов типа тренировки
TYPE_MAP = {
    's': ('Силовая тренировка', '💪'),
    'p': ('Пилатес с роллом и досками Садху', '🧘'),
    'b': ('Барре', '🩰'),
}

TRAINER_MAP = {
    'a': 'Анна',
    'al': 'Алена',
}


# ─── 1. Старт записи: выбор типа тренировки ────────────────────────
@router.callback_query(F.data == "book_start")
async def book_start(callback: CallbackQuery):
    """Выбор типа тренировки"""
    await callback.answer()

    text = "📝 ЗАПИСЬ НА ТРЕНИРОВКУ\n\nВыбери тип тренировки:"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💪 Силовая", callback_data="bt:s")],
            [InlineKeyboardButton(text="🧘 Пилатес", callback_data="bt:p")],
            [InlineKeyboardButton(text="🩰 Барре", callback_data="bt:b")],
            [InlineKeyboardButton(text="ℹ️ Что за тренировки?", callback_data="book_info")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_studio")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


# ─── Инфо о тренировках ─────────────────────────────────────────────
@router.callback_query(F.data == "book_info")
async def book_info(callback: CallbackQuery):
    """Краткое описание каждого типа тренировки"""
    await callback.answer()

    text = (
        "ℹ️ ВИДЫ ТРЕНИРОВОК\n\n"
        "💪 Силовая\n"
        "Тренировка с отягощениями на все группы мышц. "
        "Развивает силу, выносливость и формирует рельеф тела.\n\n"
        "🧘 Пилатес\n"
        "Упражнения на укрепление глубоких мышц, улучшение осанки "
        "и гибкости. Подходит для любого уровня подготовки.\n\n"
        "🩰 Барре\n"
        "Микс балета, пилатеса и функционального тренинга. "
        "Подтягивает тело, развивает баланс и грацию.\n\n"
        "Выбери тренировку для записи 👇"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💪 Силовая", callback_data="bt:s")],
            [InlineKeyboardButton(text="🧘 Пилатес", callback_data="bt:p")],
            [InlineKeyboardButton(text="🩰 Барре", callback_data="bt:b")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="book_start")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


# ─── 2. Выбран тип: Силовая → тренер, иначе → день ─────────────────
@router.callback_query(F.data.startswith("bt:"))
async def book_type(callback: CallbackQuery):
    """Обработка выбора типа тренировки"""
    await callback.answer()

    type_code = callback.data.split(":")[1]  # s, p, b
    name, emoji = TYPE_MAP[type_code]

    if type_code == 's':
        # Силовая — выбор тренера
        text = f"{emoji} {name.upper()}\n\nВыбери тренера:"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👩‍🏫 Анна", callback_data="btr:s:a")],
                [InlineKeyboardButton(text="👩‍🏫 Алена", callback_data="btr:s:al")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="book_start")],
            ]
        )
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        # Пилатес / Барре — сразу выбор дня (тренер Анна)
        await _show_day_selection(callback, type_code, 'a')


# ─── 3. Выбран тренер (только Силовая) ──────────────────────────────
@router.callback_query(F.data.startswith("btr:"))
async def book_trainer(callback: CallbackQuery):
    """Обработка выбора тренера → переход к выбору дня"""
    await callback.answer()

    parts = callback.data.split(":")  # btr:s:a или btr:s:al
    type_code = parts[1]
    trainer_code = parts[2]

    await _show_day_selection(callback, type_code, trainer_code)


# ─── Хелпер: показ доступных дней ──────────────────────────────────
async def _show_day_selection(callback: CallbackQuery, type_code: str, trainer_code: str):
    """Показать доступные дни на 7 дней вперёд"""
    name, emoji = TYPE_MAP[type_code]
    trainer_name = TRAINER_MAP[trainer_code]

    # Ищем тренировки по фильтру
    trainings = await get_trainings_by_filter(name, trainer_name)

    if not trainings:
        await callback.message.edit_text(
            f"{emoji} {name} — тренер {trainer_name}\n\nТренировки не найдены.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="book_start")]]
            )
        )
        return

    # Собираем дни недели, в которые есть тренировки
    available_days = sorted(set(t.day_of_week for t in trainings))

    now = datetime.now()
    buttons = []

    for offset in range(7):
        date = now + timedelta(days=offset)
        dow = date.weekday()
        if dow not in available_days:
            continue

        # Для сегодня — проверяем, есть ли ещё не прошедшие слоты
        if offset == 0:
            has_future = False
            for t in trainings:
                if t.day_of_week == dow:
                    hour, minute = map(int, t.time.split(':'))
                    slot_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if now < slot_time:
                        has_future = True
                        break
            if not has_future:
                continue

        date_str = date.strftime('%Y%m%d')
        day_label = f"{DAYS_RU[dow]}, {date.strftime('%d.%m')}"
        if offset == 0:
            day_label += " (сегодня)"

        # callback_data: bd:{type}:{trainer}:{date}
        buttons.append([
            InlineKeyboardButton(
                text=day_label,
                callback_data=f"bd:{type_code}:{trainer_code}:{date_str}"
            )
        ])

    if not buttons:
        buttons.append([InlineKeyboardButton(
            text="Нет доступных дней",
            callback_data="book_start"
        )])

    # Кнопка "Назад"
    back_cb = f"bt:{type_code}" if type_code != 's' else "btr_back:s"
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_cb)])

    text = f"{emoji} {name} — тренер {trainer_name}\n\nВыбери день:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)


# Кнопка "Назад" к выбору тренера Силовой
@router.callback_query(F.data == "btr_back:s")
async def back_to_trainer(callback: CallbackQuery):
    """Назад к выбору тренера"""
    await callback.answer()

    text = "💪 СИЛОВАЯ\n\nВыбери тренера:"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👩‍🏫 Анна", callback_data="btr:s:a")],
            [InlineKeyboardButton(text="👩‍🏫 Алена", callback_data="btr:s:al")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="book_start")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard)


# ─── 4. Выбран день: показываем временные слоты ─────────────────────
@router.callback_query(F.data.startswith("bd:"))
async def book_day(callback: CallbackQuery):
    """Показать доступные слоты на выбранный день"""
    await callback.answer()

    parts = callback.data.split(":")  # bd:s:a:20260128
    type_code = parts[1]
    trainer_code = parts[2]
    date_str = parts[3]

    name, emoji = TYPE_MAP[type_code]
    trainer_name = TRAINER_MAP[trainer_code]

    date = datetime.strptime(date_str, '%Y%m%d')
    dow = date.weekday()

    trainings = await get_trainings_by_filter(name, trainer_name, dow)

    now = datetime.now()
    buttons = []

    for t in trainings:
        hour, minute = map(int, t.time.split(':'))
        slot_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Не показывать прошедшие слоты сегодня
        if date.date() == now.date() and now >= slot_time:
            continue

        # Считаем занятые места
        booked = await get_bookings_count(t.id, date)
        free = t.max_participants - booked

        if free <= 0:
            slot_label = f"🔴 {t.time} — мест нет"
            # Не добавляем кнопку для полных слотов
            continue
        elif free <= 5:
            slot_label = f"🟡 {t.time} — осталось {free} мест"
        else:
            slot_label = f"🟢 {t.time} — {free} мест"

        buttons.append([
            InlineKeyboardButton(
                text=slot_label,
                callback_data=f"btm:{t.id}:{date_str}"
            )
        ])

    if not buttons:
        buttons.append([InlineKeyboardButton(
            text="Нет доступных слотов",
            callback_data=f"bd:{type_code}:{trainer_code}:{date_str}"
        )])

    buttons.append([InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data=f"bback_day:{type_code}:{trainer_code}"
    )])

    day_label = f"{DAYS_RU[dow]}, {date.strftime('%d.%m.%Y')}"
    text = f"{emoji} {name} — {trainer_name}\n📅 {day_label}\n\nВыбери время:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)


# Кнопка "Назад" из выбора времени к выбору дня
@router.callback_query(F.data.startswith("bback_day:"))
async def back_to_day_selection(callback: CallbackQuery):
    """Назад к выбору дня"""
    await callback.answer()
    parts = callback.data.split(":")  # bback_day:s:a
    type_code = parts[1]
    trainer_code = parts[2]
    await _show_day_selection(callback, type_code, trainer_code)


# ─── 5. Выбрано время: экран подтверждения ──────────────────────────
@router.callback_query(F.data.startswith("btm:"))
async def book_time(callback: CallbackQuery):
    """Экран подтверждения записи"""
    await callback.answer()

    parts = callback.data.split(":")  # btm:3:20260128
    training_id = int(parts[1])
    date_str = parts[2]

    date = datetime.strptime(date_str, '%Y%m%d')
    training = await get_training_by_id(training_id)

    if not training:
        await callback.message.edit_text(
            "Тренировка не найдена.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="book_start")]]
            )
        )
        return

    # Проверка двойной записи
    user_id = callback.from_user.id
    existing = await check_user_booking(user_id, training_id, date)
    if existing:
        await callback.message.edit_text(
            "Ты уже записан(а) на эту тренировку!\n\nВыбери другое время или день.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="book_start")]]
            )
        )
        return

    # Проверка мест
    booked = await get_bookings_count(training_id, date)
    free = training.max_participants - booked
    if free <= 0:
        await callback.message.edit_text(
            "К сожалению, все места заняты.\n\nВыбери другое время.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="book_start")]]
            )
        )
        return

    dow = date.weekday()
    type_code = next((k for k, v in TYPE_MAP.items() if v[0] == training.name), 's')
    trainer_code = next((k for k, v in TRAINER_MAP.items() if v == training.trainer), 'a')

    text = (
        f"📝 ПОДТВЕРДИ ЗАПИСЬ\n\n"
        f"{TYPE_MAP.get(type_code, ('', ''))[1]} {training.name}\n"
        f"👩‍🏫 Тренер: {training.trainer}\n"
        f"📅 {DAYS_RU[dow]}, {date.strftime('%d.%m.%Y')}\n"
        f"🕐 {training.time}\n"
        f"👥 Свободно мест: {free}/{training.max_participants}\n\n"
        f"Записаться?"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить запись", callback_data=f"bconf:{training_id}:{date_str}")],
            [InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"bd:{type_code}:{trainer_code}:{date_str}"
            )],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


# ─── 6. Подтверждение: создание записи + уведомление админу ────────
@router.callback_query(F.data.startswith("bconf:"))
async def book_confirm(callback: CallbackQuery, bot: Bot):
    """Создание записи и уведомление админов"""
    await callback.answer()

    parts = callback.data.split(":")  # bconf:3:20260128
    training_id = int(parts[1])
    date_str = parts[2]

    date = datetime.strptime(date_str, '%Y%m%d')
    user_id = callback.from_user.id

    training = await get_training_by_id(training_id)
    if not training:
        await callback.message.edit_text("Тренировка не найдена.")
        return

    # Повторная проверка двойной записи
    existing = await check_user_booking(user_id, training_id, date)
    if existing:
        await callback.message.edit_text(
            "Ты уже записан(а) на эту тренировку!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="📝 Записаться на другую", callback_data="book_start")]]
            )
        )
        return

    # Повторная проверка мест
    booked = await get_bookings_count(training_id, date)
    if booked >= training.max_participants:
        await callback.message.edit_text(
            "К сожалению, все места уже заняты.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="📝 Записаться на другую", callback_data="book_start")]]
            )
        )
        return

    # Создаём запись
    hour, minute = map(int, training.time.split(':'))
    booking_datetime = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    await create_booking(user_id, training_id, booking_datetime)

    dow = date.weekday()

    # Сообщение клиенту
    text = (
        f"✅ ЗАПИСЬ ПОДТВЕРЖДЕНА!\n\n"
        f"{training.name} — {training.trainer}\n"
        f"📅 {DAYS_RU[dow]}, {date.strftime('%d.%m.%Y')}\n"
        f"🕐 {training.time}\n\n"
        f"📍 Адрес: {config.STUDIO_ADDRESS}\n\n"
        f"До встречи на тренировке! 💪"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Записаться ещё", callback_data="book_start")],
            [InlineKeyboardButton(text="⬅️ В меню студии", callback_data="back_studio")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)

    # Уведомление админам
    user = callback.from_user
    username_str = f"@{user.username}" if user.username else f"id:{user.id}"
    admin_text = (
        f"📝 НОВАЯ ЗАПИСЬ НА ТРЕНИРОВКУ\n\n"
        f"👤 {user.full_name} ({username_str})\n"
        f"🏋️ {training.name} — {training.trainer}\n"
        f"📅 {DAYS_RU[dow]}, {date.strftime('%d.%m.%Y')}\n"
        f"🕐 {training.time}\n"
        f"👥 Записано: {booked + 1}/{training.max_participants}"
    )

    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text)
        except Exception:
            pass


# ─── Отмена записи ────────────────────────────────────────────────
@router.callback_query(F.data.startswith("cancel_book:"))
async def cancel_book(callback: CallbackQuery, bot: Bot):
    """Отмена записи пользователем"""
    await callback.answer()

    booking_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    result = await cancel_booking(booking_id, user_id)

    if not result:
        await callback.message.edit_text(
            "❌ Запись не найдена или уже отменена.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="⬅️ В профиль", callback_data="back_profile")]]
            )
        )
        return

    dow = result['booking_date'].weekday()
    date_str = result['booking_date'].strftime('%d.%m.%Y')

    text = (
        f"✅ Запись отменена!\n\n"
        f"{result['training_name']} — {result['trainer']}\n"
        f"📅 {DAYS_RU[dow]}, {date_str}\n"
        f"🕐 {result['training_time']}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_bookings")],
            [InlineKeyboardButton(text="⬅️ В профиль", callback_data="back_profile")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)

    # Уведомление админам
    user = callback.from_user
    username_str = f"@{user.username}" if user.username else f"id:{user.id}"
    admin_text = (
        f"❌ ОТМЕНА ЗАПИСИ\n\n"
        f"👤 {user.full_name} ({username_str})\n"
        f"🏋️ {result['training_name']} — {result['trainer']}\n"
        f"📅 {DAYS_RU[dow]}, {date_str}\n"
        f"🕐 {result['training_time']}"
    )

    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text)
        except Exception:
            pass
