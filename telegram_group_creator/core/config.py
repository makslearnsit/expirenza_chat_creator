import os
import logging
from dotenv import load_dotenv
from telegram.helpers import escape_markdown

# Завантажуємо змінні середовища з .env файлу
load_dotenv()

logger = logging.getLogger(__name__)

# --- Telegram Bot API ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не знайдено у змінних середовища!")
    raise ValueError("Не вказано TELEGRAM_BOT_TOKEN")

# --- Telethon API ---
try:
    API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
    if not API_ID:
        raise ValueError("TELEGRAM_API_ID має бути цілим числом.")
except (ValueError, TypeError):
     logger.error("Некоректний TELEGRAM_API_ID у змінних середовища!")
     raise ValueError("Некоректний TELEGRAM_API_ID")

API_HASH = os.getenv("TELEGRAM_API_HASH")
if not API_HASH:
    logger.error("TELEGRAM_API_HASH не знайдено у змінних середовища!")
    raise ValueError("Не вказано TELEGRAM_API_HASH")

SESSION_NAME = os.getenv("TELETHON_SESSION_NAME", "bot_session")

# --- Bot Specific Settings ---
BOT_TO_ADD = "@ExpirenzaBoxBot" # Юзернейм бота, якого завжди додаємо

# Список менеджерів за замовчуванням
PREDEFINED_MANAGERS = {
    1: {"name": "Марго", "username": "@margo_knp"},
    2: {"name": "Наталія", "username": "@Natashulechka18"},
    3: {"name": "Влада", "username": "@vladysslavao"},
    4: {"name": "Карина", "username": "@tarasyukki"},
    5: {"name": "Марія", "username": "@lebidmariia"},
    6: {"name": "Аня", "username": "@AnnOlegivna"},
    7: {"name": "Макс", "username": "@Maksspustovit"},

}

# Список ID користувачів, яким дозволено користуватися ботом
ALLOWED_USER_IDS_STR = os.getenv("ALLOWED_USER_IDS", "")
try:
    ALLOWED_USER_IDS = {int(user_id.strip()) for user_id in ALLOWED_USER_IDS_STR.split(',') if user_id.strip()}
    if not ALLOWED_USER_IDS:
        logger.warning("Список дозволених користувачів (ALLOWED_USER_IDS) порожній або не заданий!")
except ValueError:
    logger.error("Некоректний формат ALLOWED_USER_IDS. Має бути список ID через кому.")
    ALLOWED_USER_IDS = set()


def get_manager_list_text() -> str:
    """Форматує список менеджерів для відображення користувачу."""
    lines = ["Обери менеджерів, яких треба додати до груп:"]
    for num, manager_data in PREDEFINED_MANAGERS.items():
        lines.append(f"{num}. {manager_data['name']} - {manager_data['username']}")
    lines.append("\nМожеш надіслати список номерів через кому або пробіли:")
    lines.append("Приклад: 1, 3, 5")
    lines.append("\nАбо додати додаткових користувачів через @:")
    lines.append("Приклад: 1, 3 @extra_user1 @extra_user2")
    lines.append(f"\nP.S. Бот {escape_markdown(BOT_TO_ADD)} буде доданий автоматично.")
    return "\n".join(lines)