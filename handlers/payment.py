import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, update

from database import async_session, Payment
from keyboards.main import main_keyboard
import config

logger = logging.getLogger(__name__)
router = Router()


async def create_payment(user_id: int, amount: float, payment_type: str = "purchase") -> int:
    """Создание записи о платеже, возвращает payment_id.
    Отменяет предыдущие pending-платежи этого пользователя."""
    async with async_session() as session:
        # Отменяем старые pending-платежи, чтобы не было дублей
        await session.execute(
            update(Payment).where(
                Payment.user_id == user_id,
                Payment.status == 'pending'
            ).values(status='cancelled')
        )

        payment = Payment(
            user_id=user_id,
            amount=amount,
            payment_type=payment_type,
            status='pending'
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return payment.id


@router.callback_query(F.data.startswith("pay_card_"))
async def pay_by_card(callback: CallbackQuery):
    """Оплата по реквизитам — сразу создаём pending-платёж"""

    # Формат: pay_card_{product_type}_{amount}
    parts = callback.data.split("_")
    amount = int(parts[-1])
    product_type = "_".join(parts[2:-1])  # всё между "pay_card_" и суммой
    user_id = callback.from_user.id

    # Сразу создаём pending-платёж
    payment_id = await create_payment(user_id, amount, payment_type=product_type)

    # Определяем что купили (для уведомления админу)
    purchase_names = {
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
        'single': 'Разовое занятие',
        'one_group': 'Абонемент в одну группу',
        'all_groups': 'Абонемент во все группы',
        'renewal_one': 'Продление (одна группа)',
        'renewal_all': 'Продление (все группы)',
    }
    purchase_type = purchase_names.get(product_type, product_type)

    text = f"""
💳 ОПЛАТА ПО РЕКВИЗИТАМ

💰 Сумма: {amount}₽

Переведи на карту:

💳 Номер карты:
{config.CARD_NUMBER}

📛 Получатель:
{config.CARD_HOLDER}

📲 После перевода отправь сюда скриншот чека — я подтвержу оплату в течение часа.

✨ Спасибо за покупку!
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

    # Уведомление ВСЕМ админам
    from bot import bot

    admin_text = f"""
🔔 НОВАЯ ОПЛАТА!

👤 Пользователь: @{callback.from_user.username or callback.from_user.first_name}
📛 Имя: {callback.from_user.first_name}
💰 Сумма: {amount}₽
🛒 Покупка: {purchase_type}
🆔 ID: {callback.from_user.id}

⏳ Ожидаем скриншот чека...
    """

    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text)
        except Exception as e:
            print(f"Не удалось отправить админу {admin_id}: {e}")


@router.message(F.photo, F.chat.type == "private")
async def receive_payment_screenshot(message: Message):
    """Пользователь прислал скриншот оплаты (фото) — только в личных сообщениях"""
    from bot import bot

    logger.info(f"[SCREENSHOT] Получено фото от user_id={message.from_user.id} (@{message.from_user.username})")

    # Находим последний pending-платёж пользователя
    async with async_session() as session:
        result = await session.execute(
            select(Payment).where(
                Payment.user_id == message.from_user.id,
                Payment.status == 'pending'
            ).order_by(Payment.created_at.desc())
        )
        payment = result.scalars().first()

    # Если нет pending-платежа — просим выбрать покупку заново
    if not payment:
        logger.warning(f"[SCREENSHOT] Нет pending-платежа для user_id={message.from_user.id}")
        await message.answer(
            "⚠️ Нет активной покупки.\n\n"
            "Сначала выбери товар и нажми «Оплатить по реквизитам», "
            "а потом отправь скриншот чека.",
            reply_markup=main_keyboard()
        )
        return

    logger.info(f"[SCREENSHOT] Найден платёж id={payment.id}, amount={payment.amount}, type={payment.payment_type}")

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_confirm_{payment.id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_{payment.id}")
            ]
        ]
    )

    admin_text = (
        f"📸 Скриншот от @{message.from_user.username or message.from_user.first_name} "
        f"(ID: {message.from_user.id})\n"
        f"💰 Сумма: {int(payment.amount)}₽"
    )

    logger.info(f"[SCREENSHOT] Отправляю админам: {config.ADMIN_IDS}")
    for admin_id in config.ADMIN_IDS:
        try:
            await message.forward(admin_id)
            await bot.send_message(
                admin_id,
                admin_text,
                reply_markup=admin_keyboard
            )
            logger.info(f"[SCREENSHOT] Успешно отправлено админу {admin_id}")
        except Exception as e:
            logger.error(f"[SCREENSHOT] Ошибка отправки админу {admin_id}: {e}")

    await message.answer(
        "✅ Скриншот получен!\n\n"
        "Я проверю оплату и активирую покупку в течение часа.\n"
        "Спасибо!",
        reply_markup=main_keyboard()
    )


@router.message(F.document, F.chat.type == "private")
async def receive_payment_document(message: Message):
    """Пользователь прислал документ (файл чека) — только в личных сообщениях"""
    from bot import bot

    # Находим последний pending-платёж пользователя
    async with async_session() as session:
        result = await session.execute(
            select(Payment).where(
                Payment.user_id == message.from_user.id,
                Payment.status == 'pending'
            ).order_by(Payment.created_at.desc())
        )
        payment = result.scalars().first()

    # Если нет pending-платежа — просим выбрать покупку заново
    if not payment:
        await message.answer(
            "⚠️ Нет активной покупки.\n\n"
            "Сначала выбери товар и нажми «Оплатить по реквизитам», "
            "а потом отправь скриншот чека.",
            reply_markup=main_keyboard()
        )
        return

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_confirm_{payment.id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_{payment.id}")
            ]
        ]
    )

    admin_text = (
        f"📎 Документ от @{message.from_user.username or message.from_user.first_name} "
        f"(ID: {message.from_user.id})\n"
        f"💰 Сумма: {int(payment.amount)}₽"
    )

    for admin_id in config.ADMIN_IDS:
        try:
            await message.forward(admin_id)
            await bot.send_message(
                admin_id,
                admin_text,
                reply_markup=admin_keyboard
            )
        except Exception as e:
            print(f"Не удалось переслать админу {admin_id}: {e}")

    await message.answer(
        "✅ Документ получен!\n\n"
        "Я проверю оплату и активирую покупку в течение часа.\n"
        "Спасибо!",
        reply_markup=main_keyboard()
    )
