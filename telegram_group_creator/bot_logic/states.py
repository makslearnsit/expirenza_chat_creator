# Визначаємо стани для ConversationHandler
(
    SELECTING_MODE,
    AWAITING_MANAGERS,
    AWAITING_NAMES,
    AWAITING_UIDS,
    CONFIRMATION,
    AWAITING_BULK_MESSAGE,
) = range(6) # Шість станів