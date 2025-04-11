from core.config import BOT_TO_ADD, get_manager_list_text
from utils.helpers import format_list_html # Імпортуємо хелпер

# --- Привітання ---
WELCOME_MESSAGE = f"""
👋 Привіт! Я допоможу тобі швидко створити групи для закладів.

Ти можеш:
🔹 Пройти покроковий процес
🔹 Або надіслати мені все одним повідомленням у форматі:

Користувачі:
1, 3, 5
Додаткові: @custom_user1 @custom_user2

Назви:
1. НАЗВА ЗАКЛАДУ | Адреса 1
2. НАЗВА ЗАКЛАДУ | Адреса 2

UID:
1. 12345
2. 67890

Вибери формат ⬇️
"""

# --- Покроковий режим ---
STEP_1_MANAGERS_PROMPT = get_manager_list_text() # Використовуємо функцію з конфігу

STEP_2_NAMES_PROMPT = """
📌 <b>Крок 2: Назви закладів</b>

Надішли назви закладів. Кожна назва з нового рядка.
Я можу автоматично їх пронумерувати.

<b>Приклад:</b>
DONER MARKET | вул. Лугова, 12
DONER MARKET | пр-т Перемоги, 24
"""

STEP_3_UIDS_PROMPT = """
📌 <b>Крок 3: UID закладів</b>

Надішли UID кожного закладу у <b>тому ж порядку</b>, що й назви.
Кожен UID з нового рядка.

<b>Приклад:</b>
48390
48391
"""

# --- Режим одного повідомлення ---
BULK_INPUT_PROMPT = """
📦 <b>Режим одного повідомлення</b>

Надішли мені всі дані одним повідомленням за наступним форматом:

<code>Користувачі:
1, 3, 5
Додаткові: @custom_user1 @custom_user2

Назви:
DONER MARKET | вул. Лугова, 12
DONER MARKET | пр-т Перемоги, 24

UID:
48390
48391</code>

<i>Просто скопіюй цей приклад і заміни на свої дані</i>
"""

# --- Підтвердження ---
def get_confirmation_message(managers: list[str], names: list[str], uids: list[str]) -> str:
    """Формує повідомлення для підтвердження даних."""
    managers_str = format_list_html(managers) if managers else "<i>Не вибрано</i>"
    names_str = format_list_html(names, numbered=True) if names else "<i>Не вказано</i>"
    uids_str = format_list_html(uids, numbered=True) if uids else "<i>Не вказано</i>"

    return f"""
✅ <b>Перевір дані перед створенням:</b>

👤 <b>Менеджери для додавання:</b>
{managers_str}
(Також буде доданий {BOT_TO_ADD})

🏢 <b>Заклади:</b>
{names_str}

🔑 <b>UID:</b>
{uids_str}

Все вірно?
"""

# --- Помилки ---
ERROR_UID_NAME_MISMATCH = "❌ <b>Помилка:</b> Кількість UID ({uid_count}) не збігається з кількістю назв закладів ({name_count}). Будь ласка, надішли правильну кількість UID."
ERROR_INVALID_MANAGER_INPUT = "❌ <b>Помилка:</b> Не вдалося розпізнати введених менеджерів. Перевір формат (номери через кому/пробіл, юзернейми через @)."
ERROR_INVALID_BULK_FORMAT = "❌ <b>Помилка:</b> Не вдалося розпарсити повідомлення. Переконайся, що воно містить секції 'Користувачі:', 'Назви:' та 'UID:' і відповідає формату."
ERROR_PARSING_BULK_SECTION = "❌ <b>Помилка</b> при обробці секції '{section}': {error}"
ERROR_TELETHON_CONNECTION = "❌ <b>Помилка:</b> Не вдалося підключитися до Telegram API (Telethon). Перевір API ID/Hash та наявність файлу сесії."
ERROR_GROUP_CREATION = "❌ <b>Помилка</b> при створенні групи '{group_name}': {error}"
ERROR_GENERAL = "❌ Сталася несподівана помилка. Спробуй ще раз пізніше."
ERROR_ACCESS_DENIED = "❌ Вибач, тобі не дозволено використовувати цього бота."


# --- Успішне виконання ---
INFO_CREATING_GROUPS_START = "⏳ Починаю створення груп..."
INFO_CREATING_GROUP_PROGRESS = "⚙️ Створюю групу {index}/{total}: '{name}'..."
INFO_GROUP_CREATED_SUCCESS = "✅ Група '{name}' (UID: {uid}) успішно створена!"
INFO_ALL_GROUPS_CREATED = "🎉 Всі групи успішно створені!"

# --- Інше ---
CANCEL_MESSAGE = "Дію скасовано. Починай заново командою /start."
RESTART_MESSAGE = "Добре, починаємо заново."
SELECT_MODE_PROMPT = "Вибери режим роботи:"