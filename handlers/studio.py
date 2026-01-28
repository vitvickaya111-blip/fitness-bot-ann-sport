import os

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, InputMediaPhoto

from keyboards import payment_methods
import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEDULE_IMAGES_DIR = os.path.join(BASE_DIR, 'images', 'schedule')
ABOUT_IMAGES_DIR = os.path.join(BASE_DIR, 'images', 'about')

router = Router()


@router.message(F.text == "🏢 Занятия в студии")
async def studio_services(message: Message):
    """Раздел занятий в студии"""

    text = """
🏢 ЗАНЯТИЯ В СТУДИИ

Приходи к нам на тренировки! 💪

Выбери что тебя интересует: 👇
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Записаться на тренировку", callback_data="book_start")],
            [InlineKeyboardButton(text="💎 Купить абонемент", callback_data="studio_subscription")],
            [InlineKeyboardButton(text="🎫 Разовое занятие — 350₽", callback_data="studio_single")],
            [InlineKeyboardButton(text="📅 Расписание тренировок", callback_data="studio_schedule")],
            [InlineKeyboardButton(text="📍 Как добраться", callback_data="studio_location")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
        ]
    )

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "studio_schedule")
async def show_schedule(callback: CallbackQuery):
    """Расписание тренировок — 2 фото + кнопки подробнее"""
    await callback.answer()
    await callback.message.delete()

    # Отправляем фото расписания альбомом
    schedule_1 = os.path.join(SCHEDULE_IMAGES_DIR, 'schedule_1.jpeg')
    schedule_2 = os.path.join(SCHEDULE_IMAGES_DIR, 'schedule_2.jpeg')
    strength = os.path.join(SCHEDULE_IMAGES_DIR, 'strength.jpeg')
    alena = os.path.join(SCHEDULE_IMAGES_DIR, 'alena.jpeg')

    media = [
        InputMediaPhoto(
            media=FSInputFile(schedule_1),
            caption="📅 РАСПИСАНИЕ ТРЕНИРОВОК\n\n📍 г.Новотроицк, пр.Комсомольский 3 (2 этаж)"
        ),
        InputMediaPhoto(media=FSInputFile(schedule_2)),
        InputMediaPhoto(media=FSInputFile(strength), caption="💪 Силовая — Тренер Анна"),
        InputMediaPhoto(media=FSInputFile(alena), caption="💪 Силовая — Тренер Алена"),
    ]
    await callback.message.answer_media_group(media=media)

    # Кнопки "Узнать больше о тренировке"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💪 Подробнее о Силовой", callback_data="info_strength")],
            [InlineKeyboardButton(text="🩰 Подробнее о Барре", callback_data="info_barre")],
            [InlineKeyboardButton(text="🧘 Подробнее о Пилатес", callback_data="info_pilates")],
            [InlineKeyboardButton(text="💎 Купить абонемент", callback_data="studio_subscription")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_studio")]
        ]
    )
    await callback.message.answer("Хочешь узнать больше о тренировке? 👇", reply_markup=keyboard)


@router.callback_query(F.data.startswith("info_"))
async def show_training_info(callback: CallbackQuery):
    """Показать фото конкретной тренировки"""
    await callback.answer()

    training_type = callback.data.split("_")[1]

    photos = {
        'strength': 'strength.jpeg',
        'barre': 'barre.jpeg',
        'pilates': 'pilates.jpeg',
    }

    filename = photos.get(training_type)
    if not filename:
        return

    photo_path = os.path.join(SCHEDULE_IMAGES_DIR, filename)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 Купить абонемент", callback_data="studio_subscription")],
            [InlineKeyboardButton(text="🎫 Разовое занятие — 350₽", callback_data="studio_single")],
            [InlineKeyboardButton(text="📅 Назад к расписанию", callback_data="studio_schedule")],
            [InlineKeyboardButton(text="⬅️ В меню студии", callback_data="back_studio")]
        ]
    )

    await callback.message.delete()
    await callback.message.answer_photo(
        photo=FSInputFile(photo_path),
        reply_markup=keyboard
    )


@router.callback_query(F.data == "studio_location")
async def show_location(callback: CallbackQuery):
    """Как добраться"""

    text = f"""
📍 КАК ДОБРАТЬСЯ

🏢 Адрес:
{config.STUDIO_ADDRESS}

🚗 На машине:
Есть парковка рядом

🚶 Пешком:
5 минут от остановки "Комсомольская"

🏢 Ориентир:
Второй этаж, вход с торца здания

📱 Контакты:
{config.ADMIN_PHONE}

До встречи! 💪
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Расписание", callback_data="studio_schedule")],
            [InlineKeyboardButton(text="💎 Купить абонемент", callback_data="studio_subscription")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_studio")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "studio_subscription")
async def subscription_menu(callback: CallbackQuery):
    """Меню абонементов"""

    text = """
💎 АБОНЕМЕНТ НА МЕСЯЦ

⚠️ Важно: Абонемент начинается с 1-го числа месяца!

Выбери вариант: 👇
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎯 В одну группу — 3500₽", callback_data="sub_one_group")],
            [InlineKeyboardButton(text="🌟 Во все группы — 6000₽", callback_data="sub_all_groups")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_studio")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "sub_one_group")
async def subscription_one_group(callback: CallbackQuery):
    """Абонемент в одну группу"""

    text = """
🎯 АБОНЕМЕНТ В ОДНУ ГРУППУ

💰 Цена: 3500₽

✨ Что входит:
✅ Безлимит в выбранной группе
✅ Тренировки 3 раза в неделю
✅ До 28 человек в группе

⚠️ Абонемент действует с 1-го числа месяца

Выбери группу: 👇
    """

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💪 Силовая (пн, ср, пт)", callback_data="group_strength")],
            [InlineKeyboardButton(text="🧘 Пилатес (пн, ср, пт)", callback_data="group_pilates")],
            [InlineKeyboardButton(text="🩰 Барре (вт, чт, сб)", callback_data="group_barre")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="studio_subscription")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("group_"))
async def select_specific_group(callback: CallbackQuery):
    """Выбор конкретной группы"""

    group_type = callback.data.split("_")[1]

    group_info = {
        'strength': {
            'emoji': '💪',
            'name': 'СИЛОВАЯ',
            'schedule': '👩‍🏫 Тренер Анна:\nПонедельник, Среда:\n  Группа 1 — 8:30\n  Группа 2 — 17:10\n  Группа 3 — 18:10\nПятница:\n  Группа 1 — 8:30\n  Группа 2, 3 — 17:10\n\n👩‍🏫 Тренер Алена:\nПонедельник — 19:10, 20:10\nСреда — 19:10, 20:10\nПятница — 19:10',
            'description': 'Работа с весами, укрепление мышц'
        },
        'pilates': {
            'emoji': '🧘',
            'name': 'ПИЛАТЕС + РАСТЯЖКА',
            'schedule': 'ПН, СР, ПТ: 9:30',
            'description': 'Укрепление кора, гибкость, МФР ролл'
        },
        'barre': {
            'emoji': '🩰',
            'name': 'БАРРЕ',
            'schedule': 'ВТ, ЧТ: 8:30, СБ: 10:00',
            'description': 'Тренировка в стиле балета'
        }
    }

    info = group_info[group_type]

    text = f"""
{info['emoji']} {info['name']}

💰 Цена: 3500₽

📅 Расписание:
{info['schedule']}

✨ Что включено:
{info['description']}

⚠️ Абонемент начинается с 1-го числа месяца
    """

    await callback.message.edit_text(
        text,
        reply_markup=payment_methods(config.PRICES['one_group'], 'one_group'),
    )
    await callback.answer()


@router.callback_query(F.data == "sub_all_groups")
async def subscription_all_groups(callback: CallbackQuery):
    """Абонемент во все группы"""

    text = """
🌟 АБОНЕМЕНТ ВО ВСЕ ГРУППЫ

💰 Цена: 6000₽

✨ Что входит:
✅ Безлимит на ВСЕ тренировки
✅ Можешь ходить каждый день

📅 Доступно:

💪 Силовая (тренер Анна):
ПН, СР: Группа 1 — 8:30, Группа 2 — 17:10, Группа 3 — 18:10
ПТ: Группа 1 — 8:30, Группа 2,3 — 17:10

💪 Силовая (тренер Алена):
ПН — 19:10, 20:10
СР — 19:10, 20:10
ПТ — 19:10

🧘 Пилатес + растяжка (тренер Анна):
ПН, СР, ПТ — 9:30

🩰 Барре (тренер Анна):
ВТ, ЧТ — 8:30
СБ — 10:00

⚠️ Абонемент действует с 1-го по последнее число месяца

🔥 Самый выгодный вариант!
    """

    await callback.message.edit_text(
        text,
        reply_markup=payment_methods(config.PRICES['all_groups'], 'all_groups'),
    )
    await callback.answer()


@router.callback_query(F.data == "studio_single")
async def single_visit_menu(callback: CallbackQuery):
    """Разовое посещение"""

    text = """
🎫 РАЗОВОЕ ЗАНЯТИЕ

Попробуй любую тренировку! 🌟

💰 Цена: 350₽

⚠️ Важно: Нужна предварительная запись с оплатой

Выбери тренировку: 👇
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💪 Силовая", callback_data="training_strength")],
            [InlineKeyboardButton(text="🧘 Пилатес + растяжка", callback_data="training_pilates")],
            [InlineKeyboardButton(text="🩰 Барре (балет)", callback_data="training_barre")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_studio")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("training_"))
async def select_training_type(callback: CallbackQuery):
    """Выбор типа тренировки"""

    training_type = callback.data.split("_")[1]

    training_info = {
        'strength': {
            'emoji': '💪',
            'name': 'СИЛОВАЯ ТРЕНИРОВКА',
            'description': 'Работа с весами, укрепление всех групп мышц'
        },
        'pilates': {
            'emoji': '🧘',
            'name': 'ПИЛАТЕС + РАСТЯЖКА',
            'description': 'Укрепление кора, гибкость, работа с МФР роллом'
        },
        'barre': {
            'emoji': '🩰',
            'name': 'БАРРЕ',
            'description': 'Многофункциональная тренировка в стиле балета'
        }
    }

    info = training_info[training_type]

    text = f"""
{info['emoji']} {info['name']}

💰 Цена: 350₽

✨ Что включено:
{info['description']}

📲 После оплаты свяжусь с тобой для согласования времени!
    """

    await callback.message.edit_text(
        text,
        reply_markup=payment_methods(config.PRICES['single'], 'single'),
    )
    await callback.answer()


@router.message(F.text == "🙋‍♀️ Обо мне")
async def about_me(message: Message):
    """Раздел Обо мне — альбом фото"""

    about_photos = [
        ('about.jpeg', "🙋‍♀️ Обо мне\n\nМеня зовут Анна — тренер групповых и персональных тренировок."),
        ('photo_2026-01-27 12.19.28.jpeg', None),
        ('photo_2026-01-27 12.19.32.jpeg', None),
        ('photo_2026-01-27 12.19.35.jpeg', None),
        ('photo_2026-01-27 12.19.39.jpeg', None),
    ]

    media = []
    for filename, caption in about_photos:
        path = os.path.join(ABOUT_IMAGES_DIR, filename)
        if os.path.isfile(path):
            media.append(InputMediaPhoto(media=FSInputFile(path), caption=caption))

    if media:
        await message.answer_media_group(media=media)
    else:
        await message.answer("🙋‍♀️ Фото пока не добавлены.")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📱 Связаться со мной", callback_data="contact_trainer")],
            [InlineKeyboardButton(text="📅 Расписание тренировок", callback_data="studio_schedule")],
            [InlineKeyboardButton(text="💎 Купить абонемент", callback_data="studio_subscription")],
        ]
    )
    await message.answer("Что дальше? 👇", reply_markup=keyboard)


@router.message(F.text == "ℹ️ О студии")
async def about_studio(message: Message):
    """Раздел О студии"""

    text = f"""
ℹ️ О СТУДИИ {config.STUDIO_NAME}

Фитнес-студия групповых и персональных тренировок.

📍 Адрес:
{config.STUDIO_ADDRESS}

🏋️‍♀️ Направления:
💪 Силовые тренировки (ПН, СР, ПТ)
🧘 Пилатес + растяжка с МФР роллом (ПН, СР, ПТ)
🩰 Барре — тренировка в стиле балета (ВТ, ЧТ, СБ)

👩‍🏫 Тренеры:
• Анна — силовая, пилатес, барре
• Алена — силовая (вечерние группы)

⏰ Время работы:
ПН-ПТ: с 8:30 до 21:00
СБ: с 10:00

👥 До 28 человек в группе
✨ Запись обязательна!

📱 Канал: {config.CHANNEL_USERNAME}
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Расписание", callback_data="studio_schedule")],
            [InlineKeyboardButton(text="💎 Купить абонемент", callback_data="studio_subscription")],
            [InlineKeyboardButton(text="📍 Как добраться", callback_data="studio_location")],
            [InlineKeyboardButton(text="📱 Связаться", callback_data="contact_trainer")],
        ]
    )

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "back_studio")
async def back_to_studio(callback: CallbackQuery):
    """Возврат в меню студии"""

    text = """
🏢 ЗАНЯТИЯ В СТУДИИ

Приходи к нам на тренировки! 💪

Выбери что тебя интересует: 👇
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Записаться на тренировку", callback_data="book_start")],
            [InlineKeyboardButton(text="💎 Купить абонемент", callback_data="studio_subscription")],
            [InlineKeyboardButton(text="🎫 Разовое занятие — 350₽", callback_data="studio_single")],
            [InlineKeyboardButton(text="📅 Расписание тренировок", callback_data="studio_schedule")],
            [InlineKeyboardButton(text="📍 Как добраться", callback_data="studio_location")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
        ]
    )

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


REVIEWS_IMAGES_DIR = os.path.join(BASE_DIR, 'images', 'reviews')


@router.message(F.text == "⭐ Отзывы")
async def show_reviews(message: Message):
    """Отзывы клиентов"""

    photos = []
    if os.path.isdir(REVIEWS_IMAGES_DIR):
        files = sorted(os.listdir(REVIEWS_IMAGES_DIR))
        for filename in files:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                photos.append(os.path.join(REVIEWS_IMAGES_DIR, filename))

    if photos:
        media = []
        for i, photo_path in enumerate(photos):
            caption = "⭐ ОТЗЫВЫ НАШИХ КЛИЕНТОВ" if i == 0 else None
            media.append(InputMediaPhoto(media=FSInputFile(photo_path), caption=caption))
        await message.answer_media_group(media=media)
    else:
        await message.answer(
            "⭐ ОТЗЫВЫ НАШИХ КЛИЕНТОВ\n\n"
            "Фото до/после скоро будут добавлены!\n\n"
            "Более 100 человек уже изменили своё тело благодаря грамотному питанию "
            "и эффективным тренировкам."
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 Купить абонемент", callback_data="studio_subscription")],
            [InlineKeyboardButton(text="📅 Расписание", callback_data="studio_schedule")],
            [InlineKeyboardButton(text="📱 Связаться со мной", callback_data="contact_trainer")],
        ]
    )
    await message.answer("Хочешь такой же результат? 💪", reply_markup=keyboard)


@router.message(F.text == "❓ Что взять с собой")
async def what_to_bring(message: Message):
    """Что взять с собой на тренировку"""

    text = f"""
❓ ЧТО ВЗЯТЬ С СОБОЙ НА ТРЕНИРОВКУ

🎒 Обязательно:
👟 Кроссовки (чистая сменная обувь)
👕 Спортивная форма
🧴 Полотенце
💧 Вода

⚠️ ВАЖНО:
Если у тебя есть противопоказания по здоровью (проблемы с сердцем, суставами, спиной, беременность и др.) — обязательно сообщи об этом тренеру ДО начала тренировки!

Тренер подберёт нагрузку индивидуально и подскажет безопасные варианты упражнений.

🏢 Адрес: {config.STUDIO_ADDRESS}

До встречи на тренировке! 💪
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Расписание", callback_data="studio_schedule")],
            [InlineKeyboardButton(text="💎 Купить абонемент", callback_data="studio_subscription")],
            [InlineKeyboardButton(text="📱 Связаться со мной", callback_data="contact_trainer")],
        ]
    )

    await message.answer(text, reply_markup=keyboard)


BEFORE_AFTER_DIR = os.path.join(BASE_DIR, 'images', 'before_after')


@router.message(F.text == "🔄 До и после")
async def show_before_after(message: Message):
    """Фото до и после"""

    photos = []
    if os.path.isdir(BEFORE_AFTER_DIR):
        files = sorted(os.listdir(BEFORE_AFTER_DIR))
        for filename in files:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                photos.append(os.path.join(BEFORE_AFTER_DIR, filename))

    if photos:
        media = []
        for i, photo_path in enumerate(photos[:10]):
            caption = "🔄 ДО И ПОСЛЕ\n\nРезультаты наших клиентов говорят сами за себя!" if i == 0 else None
            media.append(InputMediaPhoto(media=FSInputFile(photo_path), caption=caption))
        await message.answer_media_group(media=media)
    else:
        await message.answer("🔄 Фото до/после скоро будут добавлены!")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 Купить абонемент", callback_data="studio_subscription")],
            [InlineKeyboardButton(text="📅 Расписание", callback_data="studio_schedule")],
            [InlineKeyboardButton(text="📱 Связаться со мной", callback_data="contact_trainer")],
        ]
    )
    await message.answer("Хочешь такой же результат? 💪", reply_markup=keyboard)
