from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# --- Константи для callback_data ---
CALLBACK_STEP_BY_STEP = "mode_step_by_step"
CALLBACK_BULK = "mode_bulk"
CALLBACK_CONFIRM_CREATE = "confirm_create"
CALLBACK_GO_BACK = "go_back_start" # Або інша логіка повернення

def get_start_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору режиму на старті."""
    keyboard = [
        [
            InlineKeyboardButton("🧩 Покроково", callback_data=CALLBACK_STEP_BY_STEP),
            InlineKeyboardButton("📦 Одним повідомленням", callback_data=CALLBACK_BULK),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для підтвердження створення груп."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Створити групи", callback_data=CALLBACK_CONFIRM_CREATE),
            InlineKeyboardButton("✏️ Почати заново", callback_data=CALLBACK_GO_BACK),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Можна додати інші клавіатури за потреби