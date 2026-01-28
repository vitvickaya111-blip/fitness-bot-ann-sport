"""
Обработчик команды /start с согласием на обработку данных
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from keyboards.main import main_keyboard
from database import async_session, User, Subscription, Booking, Payment, Visit
from sqlalchemy import select, delete
from datetime import datetime
import config
import logging

logger = logging.getLogger(__name__)

router = Router()


async def check_channel_subscription(bot, user_id: int) -> bool:
    """Проверяет, подписан ли пользователь на канал"""
    try:
        member = await bot.get_chat_member(chat_id=config.CHANNEL_USERNAME, user_id=user_id)
        return member.status in ('member', 'administrator', 'creator')
    except Exception as e:
        logger.warning(f"Не удалось проверить подписку на канал: {e}")
        return True  # Если не удалось проверить — пропускаем


async def _continue_start(message: Message, from_user, state: FSMContext):
    """Основная логика /start после проверки канала"""
    user_id = from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

    if not user:
        text = f"""
Привет, {from_user.first_name}!

Я — бот фитнес-студии {config.STUDIO_NAME}.

Для работы со мной мне нужно сохранить:
- Твоё имя
- Username в Telegram
- Историю покупок
- Записи на тренировки

Это нужно, чтобы:
- Управлять твоим абонементом
- Напоминать о тренировках
- Показывать статистику

Твои данные в безопасности:
- Хранятся на защищённом сервере
- Не передаются третьим лицам
- Ты можешь удалить их командой /delete_my_data

Подробнее: /privacy

Нажимая "Принимаю", ты соглашаешься на обработку данных.
        """

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Принимаю", callback_data="accept_privacy")],
                [InlineKeyboardButton(text="Политика конфиденциальности", callback_data="show_privacy")],
                [InlineKeyboardButton(text="Не принимаю", callback_data="decline_privacy")]
            ]
        )

        await message.answer(text, reply_markup=keyboard)
    else:
        await show_main_menu(message)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start"""
    await state.clear()

    user_id = message.from_user.id

    # Предлагаем подписаться на канал (не обязательно)
    is_subscribed = await check_channel_subscription(message.bot, user_id)
    if not is_subscribed:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="Подписаться на канал",
                    url=f"https://t.me/{config.CHANNEL_USERNAME.lstrip('@')}"
                )],
                [InlineKeyboardButton(text="Я подписался", callback_data="check_subscription")],
                [InlineKeyboardButton(text="Продолжить без подписки", callback_data="skip_subscription")]
            ]
        )
        await message.answer(
            f"Подпишись на наш канал {config.CHANNEL_USERNAME}, чтобы быть в курсе новостей и акций!",
            reply_markup=keyboard
        )
        return

    await _continue_start(message, message.from_user, state)


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, state: FSMContext):
    """Проверка подписки на канал после нажатия кнопки"""
    is_subscribed = await check_channel_subscription(callback.bot, callback.from_user.id)
    if is_subscribed:
        await callback.message.delete()
        await callback.answer("Спасибо за подписку!")
        await _continue_start(callback.message, callback.from_user, state)
    else:
        await callback.answer("Вы ещё не подписались на канал!", show_alert=True)


@router.callback_query(F.data == "skip_subscription")
async def skip_subscription_callback(callback: CallbackQuery, state: FSMContext):
    """Продолжить без подписки на канал"""
    await callback.message.delete()
    await callback.answer()
    await _continue_start(callback.message, callback.from_user, state)


@router.callback_query(F.data == "accept_privacy")
async def accept_privacy_policy(callback: CallbackQuery):
    """Пользователь принял политику конфиденциальности"""

    # Добавляем пользователя в БД
    async with async_session() as session:
        # Проверяем ещё раз, что пользователя нет
        result = await session.execute(
            select(User).where(User.user_id == callback.from_user.id)
        )
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            new_user = User(
                user_id=callback.from_user.id,
                username=callback.from_user.username,
                name=callback.from_user.first_name
            )
            session.add(new_user)
            await session.commit()

    await callback.message.delete()
    await show_main_menu(callback.message)
    await callback.answer("Спасибо! Теперь ты можешь пользоваться ботом.")


@router.callback_query(F.data == "decline_privacy")
async def decline_privacy_policy(callback: CallbackQuery):
    """Пользователь отклонил политику"""

    text = """
Без согласия на обработку данных я не могу работать.

Бот хранит только необходимые данные:
- Имя и username (чтобы знать с кем общаюсь)
- Покупки (чтобы следить за абонементом)
- Записи на тренировки

Если передумаешь — нажми /start снова.
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Прочитать политику", callback_data="show_privacy")],
            [InlineKeyboardButton(text="Принимаю", callback_data="accept_privacy")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "show_privacy")
async def show_privacy_inline(callback: CallbackQuery):
    """Показать политику конфиденциальности (inline)"""

    text = f"""
ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ

1. КАКИЕ ДАННЫЕ МЫ СОБИРАЕМ:
- Ваше имя в Telegram
- Ваш username (@username)
- История покупок абонементов
- История посещений тренировок
- Дата регистрации

2. ЗАЧЕМ МЫ ИХ СОБИРАЕМ:
- Для управления абонементами
- Для напоминаний о тренировках
- Для показа статистики посещений
- Для связи с вами

3. КАК МЫ ХРАНИМ ДАННЫЕ:
- Данные хранятся на защищённом сервере
- Доступ имеет только администратор студии
- Данные НЕ передаются третьим лицам
- Данные НЕ используются для рекламы

4. ВАШИ ПРАВА:
- Удалить данные: /delete_my_data
- Экспортировать данные: /export_my_data
- Отозвать согласие в любой момент

5. КОНТАКТЫ:
По вопросам обработки данных пишите администратору студии через бота.

Дата последнего обновления: 21.01.2026
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Принимаю", callback_data="accept_privacy")],
            [InlineKeyboardButton(text="Не принимаю", callback_data="decline_privacy")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.message(Command("privacy"))
async def show_privacy_command(message: Message):
    """Показать политику конфиденциальности (команда)"""

    text = f"""
ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ

1. КАКИЕ ДАННЫЕ МЫ СОБИРАЕМ:
- Ваше имя в Telegram
- Ваш username (@username)
- История покупок абонементов
- История посещений тренировок
- Дата регистрации

2. ЗАЧЕМ МЫ ИХ СОБИРАЕМ:
- Для управления абонементами
- Для напоминаний о тренировках
- Для показа статистики посещений
- Для связи с вами

3. КАК МЫ ХРАНИМ ДАННЫЕ:
- Данные хранятся на защищённом сервере
- Доступ имеет только администратор студии
- Данные НЕ передаются третьим лицам
- Данные НЕ используются для рекламы

4. ВАШИ ПРАВА:
- Удалить данные: /delete_my_data
- Экспортировать данные: /export_my_data
- Отозвать согласие в любой момент

5. КОНТАКТЫ:
По вопросам обработки данных пишите администратору студии через бота.

Дата последнего обновления: 21.01.2026

Вернуться в меню: /start
    """

    await message.answer(text)


@router.message(Command("delete_my_data"))
async def request_data_deletion(message: Message):
    """Запрос на удаление персональных данных"""

    text = """
УДАЛЕНИЕ ПЕРСОНАЛЬНЫХ ДАННЫХ

Вы уверены, что хотите удалить все свои данные?

Будут удалены:
- Ваш профиль
- История покупок
- История тренировок
- Все записи
- Статистика

Это действие НЕОБРАТИМО!

После удаления вы не сможете:
- Пользоваться абонементом
- Видеть историю покупок
- Записываться на тренировки

Если хотите снова пользоваться ботом — нужно будет начать заново (/start).
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да, удалить всё", callback_data="confirm_delete_data")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel_delete_data")]
        ]
    )

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "confirm_delete_data")
async def confirm_data_deletion(callback: CallbackQuery):
    """Подтверждение удаления данных"""

    user_id = callback.from_user.id

    # Удаляем из БД
    async with async_session() as session:
        # Удаляем все связанные данные
        await session.execute(delete(Visit).where(Visit.user_id == user_id))
        await session.execute(delete(Booking).where(Booking.user_id == user_id))
        await session.execute(delete(Payment).where(Payment.user_id == user_id))
        await session.execute(delete(Subscription).where(Subscription.user_id == user_id))
        await session.execute(delete(User).where(User.user_id == user_id))
        await session.commit()

    text = """
Все ваши данные удалены из системы.

Если захотите вернуться — нажмите /start

До встречи!
    """

    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data == "cancel_delete_data")
async def cancel_data_deletion(callback: CallbackQuery):
    """Отмена удаления данных"""

    await callback.message.delete()
    await show_main_menu(callback.message)
    await callback.answer("Удаление отменено")


@router.message(Command("export_my_data"))
async def export_user_data_command(message: Message):
    """Экспорт персональных данных пользователя"""

    user_id = message.from_user.id

    async with async_session() as session:
        # Получаем профиль
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("Данные не найдены. Используй /start для регистрации.")
            return

        # Получаем абонементы
        subs_result = await session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscriptions = subs_result.scalars().all()

        # Получаем платежи
        payments_result = await session.execute(
            select(Payment).where(Payment.user_id == user_id)
        )
        payments = payments_result.scalars().all()

        # Получаем бронирования
        bookings_result = await session.execute(
            select(Booking).where(Booking.user_id == user_id)
        )
        bookings = bookings_result.scalars().all()

        # Получаем посещения
        visits_result = await session.execute(
            select(Visit).where(Visit.user_id == user_id)
        )
        visits = visits_result.scalars().all()

    # Формируем текстовое представление
    subscriptions_text = ""
    if subscriptions:
        for sub in subscriptions:
            status = "Активен" if sub.is_active else "Истёк"
            end_date = sub.end_date.strftime('%d.%m.%Y') if sub.end_date else "—"
            subscriptions_text += f"- {sub.subscription_type} до {end_date} ({status})\n"
    else:
        subscriptions_text = "Нет данных\n"

    payments_text = ""
    total_spent = 0
    if payments:
        for pay in payments:
            date = pay.created_at.strftime('%d.%m.%Y') if pay.created_at else "—"
            payments_text += f"- {date}: {pay.amount}₽ ({pay.status})\n"
            if pay.status == 'confirmed':
                total_spent += pay.amount
    else:
        payments_text = "Нет данных\n"

    bookings_text = ""
    if bookings:
        for book in bookings:
            date = book.booking_date.strftime('%d.%m.%Y %H:%M') if book.booking_date else "—"
            bookings_text += f"- {date} ({book.status})\n"
    else:
        bookings_text = "Нет данных\n"

    visits_text = ""
    if visits:
        for visit in visits:
            date = visit.visit_date.strftime('%d.%m.%Y %H:%M') if visit.visit_date else "—"
            visits_text += f"- {date}\n"
    else:
        visits_text = "Нет данных\n"

    reg_date = user.created_at.strftime('%d.%m.%Y') if user.created_at else "—"
    export_date = datetime.now().strftime("%d.%m.%Y %H:%M")

    text = f"""
ВАШИ ПЕРСОНАЛЬНЫЕ ДАННЫЕ

ПРОФИЛЬ:
- ID: {user.user_id}
- Имя: {user.name}
- Username: @{user.username or '—'}
- Дата регистрации: {reg_date}

АБОНЕМЕНТЫ:
{subscriptions_text}
ПЛАТЕЖИ:
{payments_text}
ЗАПИСИ НА ТРЕНИРОВКИ:
{bookings_text}
ПОСЕЩЕНИЯ:
{visits_text}
СТАТИСТИКА:
- Всего потрачено: {total_spent}₽
- Всего записей: {len(bookings)}
- Всего посещений: {len(visits)}

Дата экспорта: {export_date}

Эти данные предоставлены в соответствии с законом о защите персональных данных.
    """

    await message.answer(text)


async def show_main_menu(message: Message):
    """Показать главное меню"""

    welcome_text = f"""
Привет!

Я — бот фитнес-студии {config.STUDIO_NAME}.

Здесь ты можешь:
- Купить абонемент
- Записаться на тренировку
- Заказать онлайн-тренировку

Что тебя интересует?
    """

    await message.answer(welcome_text, reply_markup=main_keyboard())


@router.callback_query(F.data == "back_main")
async def back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.delete()
    await show_main_menu(callback.message)
    await callback.answer()
