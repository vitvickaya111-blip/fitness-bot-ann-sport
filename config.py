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

DATA_DIR = os.environ.get('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
PRICES_FILE = os.path.join(DATA_DIR, 'prices.json')


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

# Расписание (структурированный формат)
SCHEDULE = {
    "monday": [
        {"type": "Силовая", "trainer": "Анна", "times": ["8:30", "17:10", "18:10"]},
        {"type": "Силовая", "trainer": "Алена", "times": ["19:10", "20:10"]},
        {"type": "Пилатес", "trainer": "Анна", "times": ["9:30"]},
    ],
    "tuesday": [
        {"type": "Барре", "trainer": "Анна", "times": ["8:30"]},
    ],
    "wednesday": [
        {"type": "Силовая", "trainer": "Анна", "times": ["8:30", "17:10", "18:10"]},
        {"type": "Силовая", "trainer": "Алена", "times": ["19:10", "20:10"]},
        {"type": "Пилатес", "trainer": "Анна", "times": ["9:30"]},
    ],
    "thursday": [
        {"type": "Барре", "trainer": "Анна", "times": ["8:30"]},
    ],
    "friday": [
        {"type": "Силовая", "trainer": "Анна", "times": ["8:30", "17:10"]},
        {"type": "Силовая", "trainer": "Алена", "times": ["18:10"]},
        {"type": "Пилатес", "trainer": "Анна", "times": ["9:30"]},
    ],
    "saturday": [
        {"type": "Барре", "trainer": "Анна", "times": ["10:00"]},
    ],
    "sunday": [],
}

DAY_TITLES = {
    "monday": "ПОНЕДЕЛЬНИК",
    "tuesday": "ВТОРНИК",
    "wednesday": "СРЕДА",
    "thursday": "ЧЕТВЕРГ",
    "friday": "ПЯТНИЦА",
    "saturday": "СУББОТА",
    "sunday": "ВОСКРЕСЕНЬЕ",
}

TRAINING_EMOJIS = {
    "Силовая": "🏃‍♀️",
    "Пилатес": "🧘‍♀️",
    "Барре": "🏃‍♀️",
}


def format_day_schedule(day):
    """Генерирует текстовое представление дня из структуры"""
    title = DAY_TITLES.get(day, day.upper())
    trainings = SCHEDULE.get(day, [])

    if not trainings:
        return f"🔘 *{title}*\n\n🌴 Выходной день\nВосстанавливаемся и набираемся сил! 💪"

    lines = [f"🔘 *{title}*\n"]

    # Группируем по типу тренировки
    grouped = {}
    for t in trainings:
        grouped.setdefault(t["type"], []).append(t)

    for training_type, entries in grouped.items():
        emoji = TRAINING_EMOJIS.get(training_type, "🏃‍♀️")
        lines.append(f"{emoji} *{training_type}*")

        if len(entries) == 1 and len(entries[0]["times"]) == 1:
            lines.append(f"✅ {entries[0]['times'][0]} - {entries[0]['trainer']}")
        else:
            for entry in entries:
                lines.append(f"👩‍🏫 Тренер {entry['trainer']}:")
                for time in entry["times"]:
                    lines.append(f"✅ {time}")

        lines.append("")

    return "\n".join(lines).rstrip()


def format_full_schedule():
    """Генерирует полное расписание для показа"""
    days_order = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    parts = ["📅 *РАСПИСАНИЕ ТРЕНИРОВОК*\n\n📍 г. Новотроицк, пр. Комсомольский 3 (2 этаж)\n"]
    for day in days_order:
        parts.append(format_day_schedule(day))
    parts.append("\n📞 Анна: @\\_an\\_sport\\_\n📞 Алена: +7 961 908 0598")
    return "\n━━━━━━━━━━━━━━━━━━━\n".join(parts)

SCHEDULE_FILE = os.path.join(DATA_DIR, 'schedule.json')


def load_schedule():
    """Загрузить расписание из JSON-файла поверх дефолтов"""
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            # Проверяем формат: если значение — строка, это старый формат, пропускаем
            for key, val in saved.items():
                if isinstance(val, list):
                    SCHEDULE[key] = val
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
