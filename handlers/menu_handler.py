from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup

router = Router()

@router.callback_query(F.data == "get_menu_file_id")
async def upload_menu_to_get_file_id(callback: CallbackQuery):
    """Временная функция - загружает PDF и получает file_id"""
    try:
        # Отправляем PDF файл
        menu_file = FSInputFile("menu.pdf")
        message = await callback.message.answer_document(document=menu_file)

        # Получаем file_id
        file_id = message.document.file_id

        # Выводим в консоль
        print("\n" + "="*50)
        print("MENU FILE_ID (скопируй это):")
        print(file_id)
        print("="*50 + "\n")

        # Отправляем пользователю
        await callback.message.answer(
            f"PDF загружен!\n\n"
            f"File ID выведен в консоль терминала.\n"
            f"Скопируй его оттуда!"
        )
        await callback.answer()

    except FileNotFoundError:
        await callback.message.answer("Файл menu.pdf не найден в папке проекта!")
        await callback.answer()
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
        await callback.answer()


@router.callback_query(F.data == "show_menu")
async def show_menu(callback: CallbackQuery):
    """Отправляет меню пользователю (ЗАМЕНИ FILE_ID ПОСЛЕ ПОЛУЧЕНИЯ!)"""

    # ПОСЛЕ ПОЛУЧЕНИЯ FILE_ID ВСТАВЬ ЕГО СЮДА:
    MENU_FILE_ID = "ВСТАВЬ_СЮДА_FILE_ID_КОТОРЫЙ_ПОЛУЧИШЬ"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="studio_back")]
    ])

    menu_caption = """
*Меню студии AN_SPORT*

Здесь ты найдешь:
- Описание всех тренировок
- Стоимость абонементов
- Условия посещения

Вопросы? Пиши @_an_sport_
"""

    if MENU_FILE_ID == "ВСТАВЬ_СЮДА_FILE_ID_КОТОРЫЙ_ПОЛУЧИШЬ":
        await callback.message.answer(
            "Меню пока не настроено. Администратор должен получить file_id."
        )
    else:
        await callback.message.answer_document(
            document=MENU_FILE_ID,
            caption=menu_caption,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

    await callback.answer()
