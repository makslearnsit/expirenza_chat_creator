import logging
from telethon import TelegramClient, functions, types
from telethon.errors import (
    UserNotParticipantError, UserAlreadyParticipantError,
    FloodWaitError, ChatAdminRequiredError, UserPrivacyRestrictedError,
    UsernameNotOccupiedError, PeerFloodError, UserBannedInChannelError
)
from telethon.tl.types import ChatAdminRights
import asyncio

logger = logging.getLogger(__name__)

# Базові права адміна для менеджерів та бота
ADMIN_RIGHTS = ChatAdminRights(
    change_info=True,
    post_messages=True,
    edit_messages=True,
    delete_messages=True,
    ban_users=True,
    invite_users=True,
    pin_messages=True,
    manage_call=True,
    # Можна додати інші права за потреби
)

# Права для вимкнення обмежень за замовчуванням (щоб історія була видима)
# Ми хочемо, щоб ВСІ права були НЕ заборонені (false), особливо view_messages
DEFAULT_BANNED_RIGHTS_VISIBLE_HISTORY = types.ChatBannedRights(
    until_date=None,  # Назавжди
    view_messages=False, # <-- Головне: НЕ забороняти перегляд повідомлень
    send_messages=False,
    send_media=False,
    send_stickers=False,
    send_gifs=False,
    send_games=False,
    send_inline=False,
    embed_links=False,
    send_polls=False,
    change_info=False,
    invite_users=False,
    pin_messages=False
)


async def create_telegram_group(
    api_id: int,
    api_hash: str,
    session_name: str,
    group_name: str,
    manager_usernames: list[str],
    bot_username: str,
    uid_code: str
) -> tuple[bool, str | int | None, str | None]:
    """
    Створює групу в Telegram, додає учасників, видає адмінки та надсилає UID.

    Args:
        api_id: API ID користувача.
        api_hash: API Hash користувача.
        session_name: Назва файлу сесії Telethon.
        group_name: Назва групи для створення.
        manager_usernames: Список юзернеймів менеджерів для додавання та адмінки.
        bot_username: Юзернейм бота для додавання та адмінки.
        uid_code: Код (UID) для відправки в створену групу.

    Returns:
        Кортеж (success: bool, group_id: int | str | None, error_message: str | None)
        group_id може бути ID чату або посиланням, якщо вдалося отримати.
    """
    # Format the group name with standard template
    formatted_group_name = f"(1) {group_name} + Expirenza Box"
    
    client = TelegramClient(session_name, api_id, api_hash, system_version="4.16.30-vxCUSTOM") # Вказуємо версію системи для стабільності
    created_group_id = None
    added_users_entities = []
    bot_entity = None
    is_supergroup = False  # Flag to track if we're dealing with a supergroup

    try:
        logger.info(f"Connecting to Telegram via Telethon (session: {session_name})...")
        await client.connect()
        if not await client.is_user_authorized():
            logger.error(f"Telethon session '{session_name}' is not authorized. Run authentication flow first.")
            # Важливо: Користувач має пройти автентифікацію вручну через консоль
            # або окремий скрипт перед першим запуском бота, щоб створити .session файл.
            # Можна додати тут запит коду/паролю, але це ускладнить логіку бота.
            # await client.start() # Потребуватиме введення в консолі, де запущений бот
            raise ConnectionError("User not authorized")

        logger.info("Telethon connection successful.")

        # --- 1. Resolve bot username ---
        try:
            logger.info(f"Resolving bot entity: {bot_username}")
            bot_entity = await client.get_entity(bot_username)
            logger.info(f"Bot entity resolved: ID={bot_entity.id}")
        except UsernameNotOccupiedError:
            logger.error(f"Bot username {bot_username} not found.")
            return False, None, f"Бот {bot_username} не знайдений."
        except ValueError as e:
             logger.error(f"Invalid bot username format '{bot_username}': {e}")
             return False, None, f"Некоректний формат юзернейму бота: {bot_username}."
        except Exception as e:
            logger.exception(f"Failed to resolve bot {bot_username}: {e}")
            return False, None, f"Помилка пошуку бота {bot_username}: {e}"

        # --- 2. Resolve manager usernames ---
        manager_entities = []
        all_users_to_add = [bot_entity]
        
        for username in manager_usernames:
            try:
                logger.info(f"Resolving manager entity: {username}")
                manager = await client.get_entity(username)
                logger.info(f"Manager entity resolved: {username} -> ID={manager.id}")
                manager_entities.append(manager)
                all_users_to_add.append(manager)
            except UsernameNotOccupiedError:
                logger.warning(f"Manager username {username} not found, skipping.")
                continue
            except Exception as e:
                logger.warning(f"Error resolving manager {username}: {e}")
                continue

        # --- 3. Create Group ---
        # Telethon рекомендує додавати хоча б одного користувача при створенні
        # Додаємо бота одразу при створенні, якщо можливо
        try:
            # Ініціалізуємо змінну перед використанням
            created_group_id = None
            
            logger.info(f"Creating group '{formatted_group_name}' with initial user ID: {all_users_to_add[0].id}")
            # Створюємо з першим знайденим користувачем (зазвичай ботом)
            try:
                # Create a supergroup (channel) instead of a regular chat
                result = await client(functions.channels.CreateChannelRequest(
                    title=formatted_group_name,
                    about="",
                    megagroup=True  # This makes it a supergroup
                ))
                
                is_supergroup = True
                logger.info(f"Chat creation result type: {type(result).__name__}")
                
                # Extract the channel ID from the result
                if hasattr(result, 'chats') and result.chats:
                    created_chat = result.chats[0]
                    created_group_id = created_chat.id
                    logger.info(f"Got supergroup ID {created_group_id} from result.chats[0]")
            except Exception as create_error:
                # If creating a supergroup fails, try creating a regular chat
                logger.warning(f"Error during CreateChannelRequest: {create_error}, falling back to CreateChatRequest")
                result = await client(functions.messages.CreateChatRequest(
                    users=[all_users_to_add[0]],  # Add at least one user immediately
                    title=formatted_group_name
                ))
                
                logger.info(f"Regular chat creation result type: {type(result).__name__}")
                
                # Safely try to get chat_id from the result
                try:
                    if hasattr(result, 'chats') and result.chats:
                        created_chat = result.chats[0]
                        created_group_id = created_chat.id
                        logger.info(f"Got chat ID {created_group_id} from result.chats[0]")
                except Exception as attr_error:
                    logger.warning(f"Could not extract chat_id from result: {attr_error}")
            
            # Wait for the group to appear in the dialogs
            await asyncio.sleep(3)  # Give it more time
            
            # If we still don't have a group ID, look for it in dialogs by name
            if not created_group_id:
                logger.info(f"Searching for newly created group '{formatted_group_name}' in recent dialogs...")
                dialogs = await client.get_dialogs(limit=20)  # Increase the limit
                for dialog in dialogs:
                    if dialog.title == formatted_group_name:
                        created_group_id = dialog.id
                        is_supergroup = dialog.is_channel
                        logger.info(f"Found chat ID {created_group_id} from recent dialogs, is_supergroup={is_supergroup}")
                        break
            
            # If we still don't have an ID, this is an error
            if not created_group_id:
                logger.error(f"Could not find newly created chat '{formatted_group_name}' in recent dialogs")
                raise ValueError(f"Failed to get chat ID for {formatted_group_name}")
            
            logger.info(f"Group '{formatted_group_name}' created with ID: {created_group_id}")

        except FloodWaitError as e:
            logger.error(f"Flood wait error during group creation: waiting for {e.seconds} seconds.")
            await asyncio.sleep(e.seconds + 1)
            # Can try again or return an error
            return False, None, f"Перевищено ліміт запитів при створенні групи. Спробуйте пізніше (через {e.seconds}с)."
        except Exception as e:
            logger.exception(f"Failed to create group '{formatted_group_name}': {e}")
            return False, None, f"Не вдалося створити групу '{formatted_group_name}': {e}"

        # --- 4. Set History Visible (if applicable) ---
        if is_supergroup:
            try:
                logger.info(f"Making history visible for supergroup ID: {created_group_id}")
                await client(functions.channels.EditChatDefaultBannedRights(
                    channel=created_group_id,
                    banned_rights=DEFAULT_BANNED_RIGHTS_VISIBLE_HISTORY
                ))
                logger.info(f"History visibility set for supergroup {created_group_id}.")
                await asyncio.sleep(1)  # Small pause
            except Exception as e:
                logger.exception(f"Failed to set history visible for supergroup {created_group_id}: {e}")
                # Not critical, but worth logging
        else:
            # For regular chats, we need to use a different approach
            try:
                logger.info(f"Making history visible for regular chat ID: {created_group_id}")
                await client(functions.messages.EditChatDefaultBannedRightsRequest(
                    peer=created_group_id,
                    banned_rights=DEFAULT_BANNED_RIGHTS_VISIBLE_HISTORY
                ))
                logger.info(f"History visibility set for regular chat {created_group_id}.")
                await asyncio.sleep(1)  # Small pause
            except Exception as e:
                logger.exception(f"Failed to set history visible for regular chat {created_group_id}: {e}")

        # --- 5. Add Remaining Members ---
        users_to_invite = all_users_to_add[1:]  # Skip the first user (bot) who was already added
        if users_to_invite:
            if is_supergroup:
                # For supergroups, use InviteToChannelRequest
                logger.info(f"Inviting {len(users_to_invite)} users to supergroup {created_group_id}...")
                try:
                    await client(functions.channels.InviteToChannelRequest(
                        channel=created_group_id,
                        users=users_to_invite
                    ))
                    logger.info(f"Successfully sent invites to {len(users_to_invite)} users for supergroup {created_group_id}.")
                    await asyncio.sleep(2)  # Pause after invitations
                except Exception as e:
                    logger.exception(f"Failed to invite users to supergroup {created_group_id}: {e}")
            else:
                # For regular chats, use AddChatUserRequest for each user individually
                logger.info(f"Adding {len(users_to_invite)} users to regular chat {created_group_id}...")
                for user in users_to_invite:
                    try:
                        await client(functions.messages.AddChatUserRequest(
                            chat_id=created_group_id,
                            user_id=user,
                            fwd_limit=100  # Forward limit
                        ))
                        logger.info(f"Added user {getattr(user, 'username', user.id)} to chat {created_group_id}")
                        await asyncio.sleep(1)  # Small pause between additions
                    except Exception as e:
                        logger.warning(f"Failed to add user {getattr(user, 'username', user.id)} to chat: {e}")

        # --- 6. Grant Admin Rights ---
        users_to_promote = [bot_entity] + manager_entities  # Promote bot and valid managers
        promoted_count = 0
        
        if is_supergroup:
            # For supergroups, use EditAdminRequest
            for entity in users_to_promote:
                if not entity:
                    continue  # Skip if entity is None
                try:
                    logger.info(f"Promoting user ID {entity.id} ({getattr(entity, 'username', 'N/A')}) to admin in supergroup {created_group_id}")
                    await client(functions.channels.EditAdminRequest(
                        channel=created_group_id,
                        user_id=entity,
                        admin_rights=ADMIN_RIGHTS,
                        rank=''  # Admin rank (e.g., 'Manager') - optional
                    ))
                    promoted_count += 1
                    logger.info(f"User ID {entity.id} promoted successfully in supergroup.")
                    await asyncio.sleep(0.5)  # Small delay between promotions
                except Exception as e:
                    logger.exception(f"Failed to promote user ID {entity.id} in supergroup {created_group_id}: {e}")
        else:
            # For regular chats, use EditChatAdminRequest
            for entity in users_to_promote:
                if not entity:
                    continue  # Skip if entity is None
                try:
                    logger.info(f"Promoting user ID {entity.id} ({getattr(entity, 'username', 'N/A')}) to admin in regular chat {created_group_id}")
                    await client(functions.messages.EditChatAdminRequest(
                        chat_id=created_group_id,
                        user_id=entity,
                        is_admin=True
                    ))
                    promoted_count += 1
                    logger.info(f"User ID {entity.id} promoted successfully in regular chat.")
                    await asyncio.sleep(0.5)  # Small delay between promotions
                except Exception as e:
                    logger.exception(f"Failed to promote user ID {entity.id} in regular chat {created_group_id}: {e}")

        logger.info(f"Promoted {promoted_count} users to admin in group {created_group_id}.")

        # --- 7. Send UID Code ---
        try:
            logger.info(f"Sending UID code '{uid_code}' to group {created_group_id}")
            # Use the correct way to send messages depending on group type
            if is_supergroup:
                await client.send_message(created_group_id, uid_code)
            else:
                await client.send_message(created_group_id, uid_code)
            logger.info(f"UID code sent successfully to group {created_group_id}.")
        except Exception as e:
            logger.exception(f"Failed to send UID code to group {created_group_id}: {e}")
            # Report the error, but the group has already been created
            return True, created_group_id, f"Група створена, але не вдалося надіслати UID: {e}"

        # --- Success ---
        return True, created_group_id, None

    except ConnectionError as e:
         logger.error(f"Telethon connection failed: {e}")
         return False, None, "Помилка підключення до Telegram API. Перевірте налаштування та авторизацію."
    except Exception as e:
        logger.exception(f"An unexpected error occurred during group creation process: {e}")
        # Return the group ID if it was created but another error occurred
        error_msg = f"Неочікувана помилка: {e}"
        return False, created_group_id, error_msg
    finally:
        if client and client.is_connected():
            logger.info("Disconnecting Telethon client.")
            await client.disconnect()