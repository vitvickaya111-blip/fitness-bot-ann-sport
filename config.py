import os
import json
from dotenv import load_dotenv

load_dotenv()

# Токены и ключи
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Поддержка нескольких админов
ADMIN_ID_STR = os.getenv('ADMIN_ID', '0')
if ',' in ADMIN_ID_STR:
    ADMIN_IDS = [int(id.strip()) for id in ADMIN_ID_STR.split(',')]
    ADMIN_ID = ADMIN_IDS[0]
else:
    ADMIN_ID = int(ADMIN_ID_STR)
    ADMIN_IDS = [ADMIN_ID]

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'an_sport_')
ADMIN_PHONE = os.getenv('ADMIN_PHONE', '+79619169150')

# Данные студии
CARD_NUMBER = os.getenv('CARD_NUMBER', '')
CARD_HOLDER = os.getenv('CARD_HOLDER', '')
STUDIO_ADDRESS = os.getenv('STUDIO_ADDRESS', '')
STUDIO_NAME = os.getenv('STUDIO_NAME', 'AN_SPORT')

# ЮKassa (для будущего)
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')

# Zoom (для будущего)
ZOOM_ACCOUNT_ID = os.getenv('ZOOM_ACCOUNT_ID')
ZOOM_CLIENT_ID = os.getenv('ZOOM_CLIENT_ID')
ZOOM_CLIENT_SECRET = os.getenv('ZOOM_CLIENT_SECRET')

# Цены
PRICES = {
    'menu_1200_week': 2000,
    'menu_1200_month': 5000,
    'menu_1500_week': 2000,
    'menu_1500_month': 5000,
    'menu_drying_week': 2000,
    'menu_drying_month': 5000,
    'menu': 2000,
    'plan': 5000,
    'video_call': 1000,
    'mentoring': 10000,
    'single': 350,
    'one_group': 3500,
    'all_groups': 6000,
    'renewal_one': 2700,
    'renewal_all': 4000,
}

PRICES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prices.json')


def load_prices():
    """Загрузить цены из JSON-файла поверх дефолтов"""
    if os.path.exists(PRICES_FILE):
        try:
            with open(PRICES_FILE, 'r') as f:
                saved = json.load(f)
            PRICES.update(saved)
        except (json.JSONDecodeError, IOError):
            pass


def save_prices():
    """Сохранить текущие цены в JSON-файл"""
    with open(PRICES_FILE, 'w') as f:
        json.dump(PRICES, f, ensure_ascii=False, indent=2)


load_prices()

# Расписание
SCHEDULE = {
    "monday": "🔘 *ПОНЕДЕЛЬНИК*\n\n🏃‍♀️ *Силовые тренировки*\n👩‍🏫 Тренер Анна:\n✅ Группа 1 — 8:30\n✅ Группа 2 — 17:10\n✅ Группа 3 — 18:10\n👩‍🏫 Тренер Алена:\n✅ 19:10\n✅ 20:10\n\n🧘‍♀️ *Пилатес*\n✅ 9:30 - Анна",
    "tuesday": "🔘 *ВТОРНИК*\n\n🏃‍♀️ *Барре*\n✅ 8:30 - Анна",
    "wednesday": "🔘 *СРЕДА*\n\n🏃‍♀️ *Силовые тренировки*\n👩‍🏫 Тренер Анна:\n✅ Группа 1 — 8:30\n✅ Группа 2 — 17:10\n✅ Группа 3 — 18:10\n👩‍🏫 Тренер Алена:\n✅ 19:10\n✅ 20:10\n\n🧘‍♀️ *Пилатес*\n✅ 9:30 - Анна",
    "thursday": "🔘 *ЧЕТВЕРГ*\n\n🏃‍♀️ *Барре*\n✅ 8:30 - Анна",
    "friday": "🔘 *ПЯТНИЦА*\n\n🏃‍♀️ *Силовые тренировки*\n👩‍🏫 Тренер Анна:\n✅ Группа 1 — 8:30\n✅ Группа 2, 3 — 17:10\n👩‍🏫 Тренер Алена:\n✅ 19:10\n\n🧘‍♀️ *Пилатес*\n✅ 9:30 - Анна",
    "saturday": "🔘 *СУББОТА*\n\n🏃‍♀️ *Барре*\n✅ 10:00 - Анна",
    "sunday": "🔘 *ВОСКРЕСЕНЬЕ*\n\n🌴 Выходной день\nВосстанавливаемся и набираемся сил! 💪",
}

SCHEDULE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schedule.json')


def load_schedule():
    """Загрузить расписание из JSON-файла поверх дефолтов"""
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            SCHEDULE.update(saved)
        except (json.JSONDecodeError, IOError):
            pass


def save_schedule():
    """Сохранить текущее расписание в JSON-файл"""
    with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
        json.dump(SCHEDULE, f, ensure_ascii=False, indent=2)


load_schedule()

# База данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite+aiosqlite:///{os.path.join(BASE_DIR, "bot.db")}')

# Канал
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', '@OFFICIAL_AN_SPORT')

# Лимиты
MAX_PEOPLE_PER_CLASS = 28
