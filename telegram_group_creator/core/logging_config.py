import logging
import sys

def setup_logging():
    """Налаштовує базову конфігурацію логування."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout,  # Вивід логів у консоль
        # filename='bot.log', # Розкоментуйте для запису у файл
        # filemode='a'
    )
    # Зменшуємо детальність логів від сторонніх бібліотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram.ext").setLevel(logging.INFO)
    logging.getLogger("telethon").setLevel(logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully.")