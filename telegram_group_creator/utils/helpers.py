import html

def format_list_html(items: list[str], numbered: bool = False) -> str:
    """
    Форматує список елементів у HTML для Telegram.

    Args:
        items: Список рядків.
        numbered: Чи потрібно нумерувати список.

    Returns:
        Відформатований HTML рядок.
    """
    if not items:
        return "<i>(порожньо)</i>"

    escaped_items = [html.escape(item) for item in items]

    if numbered:
        return "\n".join(f"{i+1}. {item}" for i, item in enumerate(escaped_items))
    else:
        # Використовуємо тире для ненумерованого списку
        return "\n".join(f"- {item}" for item in escaped_items)