import logging

from telegram import Update, ReplyKeyboardRemove
from telegram.constants import ParseMode


from telegram.ext import (
    ContextTypes, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackQueryHandler
)

from .states import (
    SELECTING_MODE, AWAITING_MANAGERS, AWAITING_NAMES, AWAITING_UIDS,
    CONFIRMATION, AWAITING_BULK_MESSAGE
)
from .keyboards import (
    get_start_keyboard, get_confirmation_keyboard,
    CALLBACK_STEP_BY_STEP, CALLBACK_BULK, CALLBACK_CONFIRM_CREATE, CALLBACK_GO_BACK
)
from .message_texts import (
    WELCOME_MESSAGE, STEP_1_MANAGERS_PROMPT, STEP_2_NAMES_PROMPT, STEP_3_UIDS_PROMPT,
    BULK_INPUT_PROMPT, get_confirmation_message, ERROR_UID_NAME_MISMATCH,
    ERROR_INVALID_MANAGER_INPUT, ERROR_INVALID_BULK_FORMAT, ERROR_PARSING_BULK_SECTION,
    INFO_CREATING_GROUPS_START, INFO_CREATING_GROUP_PROGRESS, INFO_GROUP_CREATED_SUCCESS,
    INFO_ALL_GROUPS_CREATED, CANCEL_MESSAGE, RESTART_MESSAGE, SELECT_MODE_PROMPT,
    ERROR_TELETHON_CONNECTION, ERROR_GROUP_CREATION, ERROR_GENERAL, ERROR_ACCESS_DENIED
)
from core.config import (
    API_ID, API_HASH, SESSION_NAME, BOT_TO_ADD, ALLOWED_USER_IDS
)
from core.parser import parse_managers, parse_names, parse_uids, parse_bulk_message
from core.telethon_client import create_telegram_group
from utils.helpers import format_list_html

logger = logging.getLogger(__name__)

# --- Access Control Decorator ---
def restricted(func):
    """Декоратор для перевірки, чи ID користувача є у списку дозволених."""
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USER_IDS:
            logger.warning(f"Unauthorized access attempt by user ID: {user_id}")
            await update.message.reply_text(ERROR_ACCESS_DENIED)
            return None # Або ConversationHandler.END, якщо використовується всередині діалогу
        logger.info(f"Authorized access granted for user ID: {user_id}")
        return await func(update, context, *args, **kwargs)
    return wrapped


# --- /start Command ---
@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробник команди /start. Починає діалог."""
    logger.info(f"User {update.effective_user.id} started the conversation.")
    context.user_data.clear() # Очищаємо дані попередньої сесії
    await update.message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=get_start_keyboard(),
        parse_mode=ParseMode.HTML # Використовуємо HTML для кращого форматування
    )
    return SELECTING_MODE

# --- Mode Selection Callback ---
async def select_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє вибір режиму (покроково / одним повідомленням)."""
    query = update.callback_query
    logger.info(f"Received callback query with data: {query.data}")
    await query.answer() # Важливо відповісти на запит
    mode = query.data

    if mode == CALLBACK_STEP_BY_STEP:
        logger.info("User selected step-by-step mode")
        await query.edit_message_text(
            STEP_1_MANAGERS_PROMPT,
            parse_mode=ParseMode.HTML
        )
        return AWAITING_MANAGERS
    elif mode == CALLBACK_BULK:
        logger.info("User selected bulk mode")
        await query.edit_message_text(
            BULK_INPUT_PROMPT,
            parse_mode=ParseMode.HTML
        )
        return AWAITING_BULK_MESSAGE
    elif mode == CALLBACK_GO_BACK: # Обробка кнопки "Почати заново"
        logger.info(f"User {update.effective_user.id} chose to restart.")
        await query.edit_message_text(RESTART_MESSAGE)
        await query.message.reply_text(
             WELCOME_MESSAGE,
             reply_markup=get_start_keyboard(),
             parse_mode=ParseMode.HTML
        )
        context.user_data.clear()
        return SELECTING_MODE
    else:
        logger.warning(f"Unexpected callback data received: {mode}")
        await query.edit_message_text(
            "Невідомий режим. Будь ласка, виберіть один з доступних режимів.",
            reply_markup=get_start_keyboard()
        )
        return SELECTING_MODE


# --- Step-by-Step: Handling Managers ---
async def handle_managers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє введення менеджерів."""
    user_input = update.message.text
    logger.debug(f"Received manager input from {update.effective_user.id}: {user_input}")
    managers, errors = parse_managers(user_input)

    if errors:
        logger.warning(f"Invalid manager input from {update.effective_user.id}: {errors}")
        error_message = ERROR_INVALID_MANAGER_INPUT + "\n\n" + "\n".join(errors)
        await update.message.reply_text(error_message, parse_mode=ParseMode.HTML)
        # Залишаємося в тому ж стані, щоб користувач спробував ще раз
        await update.message.reply_text(STEP_1_MANAGERS_PROMPT, parse_mode=ParseMode.HTML)
        return AWAITING_MANAGERS

    context.user_data['managers'] = managers
    logger.info(f"User {update.effective_user.id} selected managers: {managers}")
    await update.message.reply_text(STEP_2_NAMES_PROMPT, parse_mode=ParseMode.HTML) # Change to HTML
    return AWAITING_NAMES

# --- Step-by-Step: Handling Names ---
async def handle_names(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє введення назв закладів."""
    user_input = update.message.text
    logger.debug(f"Received names input from {update.effective_user.id}: {user_input}")
    names = parse_names(user_input)

    if not names:
        logger.warning(f"Empty names input from {update.effective_user.id}")
        await update.message.reply_text("Будь ласка, введіть хоча б одну назву закладу.")
        return AWAITING_NAMES # Залишаємося тут

    context.user_data['names'] = names
    logger.info(f"User {update.effective_user.id} provided names: {names}")
    await update.message.reply_text(STEP_3_UIDS_PROMPT, parse_mode=ParseMode.HTML)
    return AWAITING_UIDS

# --- Step-by-Step: Handling UIDs ---
async def handle_uids(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє введення UID та переходить до підтвердження."""
    user_input = update.message.text
    logger.debug(f"Received UIDs input from {update.effective_user.id}: {user_input}")
    uids = parse_uids(user_input)
    names = context.user_data.get('names', [])

    if not uids:
         logger.warning(f"Empty UIDs input from {update.effective_user.id}")
         await update.message.reply_text("Будь ласка, введіть хоча б один UID.")
         return AWAITING_UIDS # Залишаємося тут

    if len(uids) != len(names):
        logger.warning(f"UID/Name count mismatch for user {update.effective_user.id}. Names: {len(names)}, UIDs: {len(uids)}")
        error_msg = ERROR_UID_NAME_MISMATCH.format(uid_count=len(uids), name_count=len(names))
        await update.message.reply_text(error_msg, parse_mode=ParseMode.HTML)
        # Запитуємо UID знову
        await update.message.reply_text(STEP_3_UIDS_PROMPT, parse_mode=ParseMode.HTML)
        return AWAITING_UIDS

    context.user_data['uids'] = uids
    logger.info(f"User {update.effective_user.id} provided UIDs: {uids}")

    # Перехід до підтвердження
    managers = context.user_data.get('managers', [])
    confirmation_text = get_confirmation_message(managers, names, uids)
    await update.message.reply_text(
        confirmation_text,
        reply_markup=get_confirmation_keyboard(),
        parse_mode=ParseMode.HTML # Використовуємо HTML тут
    )
    return CONFIRMATION


# --- Bulk Message Handling ---
async def handle_bulk_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє одне повідомлення з усіма даними."""
    user_input = update.message.text
    user_id = update.effective_user.id
    logger.debug(f"Received bulk message input from {user_id}:\n{user_input}")

    try:
        parsed_data = parse_bulk_message(user_input)
        context.user_data['managers'] = parsed_data['managers']
        context.user_data['names'] = parsed_data['names']
        context.user_data['uids'] = parsed_data['uids']
        logger.info(f"Successfully parsed bulk message from {user_id}.")

        # Перехід до підтвердження
        confirmation_text = get_confirmation_message(
            parsed_data['managers'], parsed_data['names'], parsed_data['uids']
        )
        await update.message.reply_text(
            confirmation_text,
            reply_markup=get_confirmation_keyboard(),
            parse_mode=ParseMode.HTML
        )
        return CONFIRMATION

    except ValueError as e:
        error_message = str(e)
        logger.warning(f"Failed to parse bulk message from {user_id}: {error_message}")
        # Повідомляємо користувача про помилку парсингу
        full_error_message = f"{ERROR_INVALID_BULK_FORMAT}\n\n<i>Деталі: {error_message}</i>"
        await update.message.reply_text(full_error_message, parse_mode=ParseMode.HTML)
        # Просимо спробувати ще раз
        await update.message.reply_text(BULK_INPUT_PROMPT, parse_mode=ParseMode.HTML)
        return AWAITING_BULK_MESSAGE # Залишаємося у стані очікування

# --- Confirmation Callback & Group Creation Trigger ---
async def confirm_creation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє кнопку підтвердження та запускає створення груп."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data == CALLBACK_CONFIRM_CREATE:
        logger.info(f"User {user_id} confirmed group creation.")
        managers = context.user_data.get('managers', [])
        names = context.user_data.get('names', [])
        uids = context.user_data.get('uids', [])

        if not names or not uids or len(names) != len(uids):
             logger.error(f"Data inconsistency before creation for user {user_id}. Data: {context.user_data}")
             await query.edit_message_text("Помилка даних. Будь ласка, почніть заново з /start.")
             context.user_data.clear()
             return ConversationHandler.END

        await query.edit_message_text(INFO_CREATING_GROUPS_START, parse_mode=ParseMode.HTML)

        total_groups = len(names)
        created_count = 0
        errors = []

        # --- Запуск Telethon логіки ---
        try:
            # Перевірка наявності сесії - базова
            session_file = f"{SESSION_NAME}.session"
            import os
            if not os.path.exists(session_file):
                logger.error(f"Telethon session file '{session_file}' not found!")
                raise ConnectionError(f"Файл сесії '{session_file}' не знайдено. Запустіть процес автентифікації Telethon.")

            for i, (name, uid) in enumerate(zip(names, uids)):
                progress_message = INFO_CREATING_GROUP_PROGRESS.format(index=i+1, total=total_groups, name=name)
                await context.bot.send_message(chat_id=user_id, text=progress_message, parse_mode=ParseMode.HTML)

                success, group_info, error_msg = await create_telegram_group(
                    api_id=API_ID,
                    api_hash=API_HASH,
                    session_name=SESSION_NAME,
                    group_name=name,
                    manager_usernames=managers,
                    bot_username=BOT_TO_ADD,
                    uid_code=uid
                )

                if success:
                    created_count += 1
                    success_msg = INFO_GROUP_CREATED_SUCCESS.format(name=name, uid=uid)
                    # Можна додати посилання на групу, якщо group_info - це ID
                    if isinstance(group_info, int):
                         # Посилання на приватну групу створити складно без invite link
                         # Поки що просто ID
                         success_msg += f" (ID: <code>{group_info}</code>)" # Use HTML code tag instead of backticks
                    await context.bot.send_message(chat_id=user_id, text=success_msg, parse_mode=ParseMode.HTML)
                    logger.info(f"Group '{name}' created successfully for user {user_id}. Info: {group_info}")
                else:
                    error_log = ERROR_GROUP_CREATION.format(group_name=name, error=error_msg)
                    logger.error(f"Failed to create group '{name}' for user {user_id}: {error_msg}")
                    errors.append(f"Помилка для '{name}': {error_msg}")
                    await context.bot.send_message(chat_id=user_id, text=error_log, parse_mode=ParseMode.HTML)

        except ConnectionError as e:
             logger.error(f"Telethon connection/authentication error for user {user_id}: {e}")
             await context.bot.send_message(chat_id=user_id, text=f"{ERROR_TELETHON_CONNECTION}\n<i>{e}</i>", parse_mode=ParseMode.HTML)
             # Завершуємо діалог при помилці підключення
             context.user_data.clear()
             return ConversationHandler.END
        except Exception as e:
             logger.exception(f"Unexpected error during group creation loop for user {user_id}: {e}")
             await context.bot.send_message(chat_id=user_id, text=f"{ERROR_GENERAL}\n<i>{e}</i>", parse_mode=ParseMode.HTML)
             # Завершуємо діалог
             context.user_data.clear()
             return ConversationHandler.END


        # --- Фінальне повідомлення ---
        final_message = f"Завершено. Створено {created_count} з {total_groups} груп."
        if errors:
             final_message += "\n\nВиникли наступні помилки:\n"
             final_message += format_list_html(errors) # Використовуємо хелпер
        elif created_count == total_groups and total_groups > 0:
            final_message = INFO_ALL_GROUPS_CREATED

        await context.bot.send_message(chat_id=user_id, text=final_message, parse_mode=ParseMode.HTML)

        context.user_data.clear() # Очистка даних після завершення
        return ConversationHandler.END

    elif query.data == CALLBACK_GO_BACK:
        logger.info(f"User {user_id} chose to restart from confirmation.")
        await query.edit_message_text(RESTART_MESSAGE)
         # Повертаємо користувача до вибору режиму
        await query.message.reply_text(
             WELCOME_MESSAGE,
             reply_markup=get_start_keyboard(),
             parse_mode=ParseMode.HTML
        )
        context.user_data.clear()
        return SELECTING_MODE
    else:
        logger.warning(f"Received unknown callback data in confirmation state: {query.data}")
        await query.edit_message_text("Невідома опція.")
        return CONFIRMATION

# --- /cancel Command ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Скасовує поточну операцію (виходить з ConversationHandler)."""
    user = update.effective_user
    logger.info(f"User {user.id} canceled the conversation.")
    context.user_data.clear()
    await update.message.reply_text(
        CANCEL_MESSAGE, reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# --- Обробник неочікуваних текстових повідомлень ---
async def unexpected_message_in_mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє текстові повідомлення у стані вибору режиму."""
    logger.info(f"User {update.effective_user.id} sent text message in mode selection state: {update.message.text}")
    await update.message.reply_text(
        "Будь ласка, вибери режим роботи, натиснувши на одну з кнопок нижче.",
        reply_markup=get_start_keyboard(),
        parse_mode=ParseMode.HTML
    )
    return SELECTING_MODE

# --- Conversation Handler Setup ---
def get_conversation_handler() -> ConversationHandler:
    """Створює та повертає ConversationHandler."""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_MODE: [
                CallbackQueryHandler(select_mode_callback, pattern=f"^{CALLBACK_STEP_BY_STEP}$|^{CALLBACK_BULK}$|^{CALLBACK_GO_BACK}$"),
                # Додаємо обробник для текстових повідомлень, якщо користувач пише замість натискання кнопки
                MessageHandler(filters.TEXT & ~filters.COMMAND, unexpected_message_in_mode_selection)
            ],
            AWAITING_MANAGERS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_managers)
            ],
            AWAITING_NAMES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_names)
            ],
            AWAITING_UIDS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_uids)
            ],
             AWAITING_BULK_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bulk_message)
            ],
            CONFIRMATION: [
                 CallbackQueryHandler(confirm_creation_callback, pattern=f"^{CALLBACK_CONFIRM_CREATE}$|^{CALLBACK_GO_BACK}$"),
                 # Додаємо обробник текстових повідомлень на етапі підтвердження
                 MessageHandler(filters.TEXT & ~filters.COMMAND, unexpected_message_in_mode_selection)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        # Додаємо параметр per_chat=True для правильної обробки CallbackQueryHandler
        per_chat=True,
        # Дозволяємо повторний вхід у діалог
        allow_reentry=True
    )
    return conv_handler

# TODO: Додати функцію unexpected_message_in_mode_selection, якщо потрібно обробляти текст замість кнопок на першому кроці