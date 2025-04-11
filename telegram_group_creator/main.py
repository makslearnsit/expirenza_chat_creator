import logging
from telegram.ext import Application, CommandHandler
from telegram.error import InvalidToken

from core.config import BOT_TOKEN
from core.logging_config import setup_logging
from bot_logic.handlers import get_conversation_handler, cancel # Імпортуємо cancel для окремого додавання

# Налаштовуємо логування на самому початку
setup_logging()
logger = logging.getLogger(__name__)

def main() -> None:
    """Запускає Telegram бота."""
    logger.info("Starting bot...")

    if not BOT_TOKEN:
        logger.critical("Bot token not found. Exiting.")
        return

    try:
        # Створюємо Application
        application = Application.builder().token(BOT_TOKEN).build()

        # --- Реєстрація обробників ---
        # 1. Conversation Handler для основного воркфлоу
        conv_handler = get_conversation_handler()
        application.add_handler(conv_handler)

        # 2. Додатково реєструємо /cancel, щоб він працював навіть поза діалогом
        # (хоча fallback у ConversationHandler вже має його обробляти)
        application.add_handler(CommandHandler('cancel', cancel))

        # Можна додати інші обробники тут (наприклад, /help)

        logger.info("Bot handlers registered. Starting polling...")
        # Запускаємо бота
        application.run_polling()

    except InvalidToken:
        logger.critical(f"Invalid Telegram Bot Token provided. Please check your .env file.")
    except ImportError as e:
         logger.critical(f"Missing dependencies: {e}. Run 'pip install -r requirements.txt'")
    except Exception as e:
        logger.exception(f"An unexpected error occurred during bot initialization or runtime: {e}")

if __name__ == '__main__':
    main()