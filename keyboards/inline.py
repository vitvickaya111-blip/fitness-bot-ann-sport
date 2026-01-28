"""
Inline клавиатуры
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import config


def online_menu_keyboard():
    """Меню онлайн-тренировок"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Меню питания", callback_data="online_menu")],
            [InlineKeyboardButton(text="💪 План тренировок — 5000₽", callback_data="online_plan")],
            [InlineKeyboardButton(text="📹 Онлайн-тренировка — 1000₽", callback_data="online_video")],
            [InlineKeyboardButton(text="👥 Наставничество — 10000₽", callback_data="online_mentoring")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
        ]
    )
    return keyboard


def studio_menu_keyboard():
    """Меню студии"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Расписание", callback_data="studio_schedule")],
            [InlineKeyboardButton(text="Купить абонемент", callback_data="buy_studio")],
            [InlineKeyboardButton(text="Разовое занятие", callback_data="single_training")],
            [InlineKeyboardButton(text="Как добраться", callback_data="studio_location")],
            [InlineKeyboardButton(text="📋 Меню студии", callback_data="show_menu")],
            [InlineKeyboardButton(text="🔧 Получить Menu File ID", callback_data="get_menu_file_id")]
        ]
    )
    return keyboard


def profile_keyboard(has_subscription: bool = False):
    """Меню личного кабинета"""
    buttons = [
        [InlineKeyboardButton(text="Мой абонемент", callback_data="my_subscription")],
        [InlineKeyboardButton(text="История посещений", callback_data="visit_history")],
    ]
    if has_subscription:
        buttons.append([InlineKeyboardButton(text="Продлить абонемент", callback_data="renew_subscription")])
    buttons.append([InlineKeyboardButton(text="Связаться с тренером", callback_data="contact_trainer")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def subscription_keyboard(subscription_type: str = "online"):
    """Клавиатура выбора абонемента"""
    prefix = "online" if subscription_type == "online" else "studio"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"В одну группу — {config.PRICES['one_group']}₽",
                callback_data=f"{prefix}_one_group"
            )],
            [InlineKeyboardButton(
                text=f"Во все группы — {config.PRICES['all_groups']}₽",
                callback_data=f"{prefix}_all_groups"
            )],
            [InlineKeyboardButton(text="Назад", callback_data=f"{prefix}_back")]
        ]
    )
    return keyboard


def payment_keyboard(payment_id: int):
    """Клавиатура подтверждения оплаты"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Я оплатил(а)",
                callback_data=f"payment_done_{payment_id}"
            )],
            [InlineKeyboardButton(
                text="Отмена",
                callback_data="payment_cancel"
            )]
        ]
    )
    return keyboard


def admin_payment_keyboard(payment_id: int):
    """Клавиатура подтверждения оплаты для админа"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подтвердить",
                    callback_data=f"admin_confirm_{payment_id}"
                ),
                InlineKeyboardButton(
                    text="Отклонить",
                    callback_data=f"admin_reject_{payment_id}"
                )
            ]
        ]
    )
    return keyboard


def schedule_keyboard(trainings: list, date_str: str):
    """Клавиатура расписания с тренировками"""
    buttons = []
    for training in trainings:
        buttons.append([InlineKeyboardButton(
            text=f"{training['time']} — {training['name']}",
            callback_data=f"book_{training['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="schedule_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def booking_confirm_keyboard(training_id: int):
    """Клавиатура подтверждения записи"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Записаться",
                callback_data=f"confirm_book_{training_id}"
            )],
            [InlineKeyboardButton(
                text="Отмена",
                callback_data="booking_cancel"
            )]
        ]
    )
    return keyboard


def renewal_keyboard():
    """Клавиатура продления абонемента"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"В одну группу — {config.PRICES['renewal_one']}₽",
                callback_data="renew_one_group"
            )],
            [InlineKeyboardButton(
                text=f"Во все группы — {config.PRICES['renewal_all']}₽",
                callback_data="renew_all_groups"
            )],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_profile")]
        ]
    )
    return keyboard


def comeback_keyboard():
    """Клавиатура для возвращающихся клиентов (скидка)"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"В одну группу — {config.PRICES['renewal_one']}₽",
                callback_data="comeback_one_group"
            )],
            [InlineKeyboardButton(
                text=f"Во все группы — {config.PRICES['renewal_all']}₽",
                callback_data="comeback_all_groups"
            )],
            [InlineKeyboardButton(text="← В меню", callback_data="back_to_main")]
        ]
    )
    return keyboard


def payment_methods(amount: int, product_type: str = "purchase"):
    """Клавиатура с реквизитами для оплаты"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить по реквизитам", callback_data=f"pay_card_{product_type}_{amount}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_online")]
        ]
    )
    return keyboard


def payment_confirm_keyboard(amount: int, product_type: str = "purchase"):
    """Клавиатура подтверждения оплаты (после показа реквизитов)"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Я оплатил(а)",
                callback_data=f"paid_{product_type}_{amount}"
            )],
            [InlineKeyboardButton(
                text="Отмена",
                callback_data="online_back"
            )]
        ]
    )
    return keyboard