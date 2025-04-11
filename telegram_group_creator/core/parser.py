import re
import logging
from typing import Dict, List, Tuple, Optional
from .config import PREDEFINED_MANAGERS

logger = logging.getLogger(__name__)

def parse_managers(text: str) -> Tuple[List[str], List[str]]:
    """
    Парсить ввід користувача для вибору менеджерів.
    Повертає кортеж: (список юзернеймів, список помилок).
    """
    selected_usernames = set()
    errors = []
    parts = re.split(r'[,\s]+', text.strip()) # Розділяємо по комі або пробілах

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if part.startswith('@'):
            # Це юзернейм
            if len(part) > 1: # Переконуємося, що це не просто "@"
                selected_usernames.add(part)
            else:
                errors.append(f"Некоректний юзернейм: '{part}'")
        else:
            # Спробуємо розпізнати як номер
            try:
                num = int(part)
                if num in PREDEFINED_MANAGERS:
                    selected_usernames.add(PREDEFINED_MANAGERS[num]['username'])
                else:
                    errors.append(f"Менеджера з номером {num} не знайдено.")
            except ValueError:
                errors.append(f"Не вдалося розпізнати '{part}'. Введіть номер або юзернейм (@username).")

    return sorted(list(selected_usernames)), errors

def parse_names(text: str) -> List[str]:
    """Парсить список назв закладів, по одній на рядок."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    # Видаляємо початкову нумерацію типу "1. " або "1) "
    cleaned_lines = [re.sub(r'^\d+[\.\)]\s*', '', line) for line in lines]
    return cleaned_lines

def parse_uids(text: str) -> List[str]:
    """Парсить список UID, по одному на рядок."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
     # Видаляємо початкову нумерацію типу "1. " або "1) "
    cleaned_lines = [re.sub(r'^\d+[\.\)]\s*', '', line) for line in lines]
    return cleaned_lines


def parse_bulk_message(text: str) -> Dict[str, List[str]]:
    """
    Парсить одне велике повідомлення з секціями.
    Повертає словник {'managers': [...], 'names': [...], 'uids': [...]}
    Або кидає ValueError у разі помилки формату.
    """
    data: Dict[str, List[str]] = {"managers": [], "names": [], "uids": []}
    current_section: Optional[str] = None
    section_content: Dict[str, str] = {"користувачі": "", "назви": "", "uid": ""}
    section_map = {"користувачі": "managers", "назви": "names", "uid": "uids"}

    lines = text.splitlines()

    for line in lines:
        line_stripped = line.strip().lower()

        # Перевіряємо, чи рядок починається з назви секції
        matched_section = None
        for section_key in section_map.keys():
            if line_stripped.startswith(section_key + ":"):
                matched_section = section_key
                break

        if matched_section:
            current_section = matched_section
            # Видаляємо назву секції з першого рядка її контенту
            content_after_marker = line.strip()[len(matched_section)+1:].strip()
            if content_after_marker:
                 section_content[current_section] = content_after_marker + "\n"
            else:
                 section_content[current_section] = "" # Починаємо збирати контент для цієї секції
        elif current_section:
            # Додаємо рядок до контенту поточної секції
             section_content[current_section] += line + "\n"

    # Парсимо контент кожної секції
    try:
        # Обробка менеджерів (включаючи "Додаткові:")
        manager_text = ""
        if "користувачі" in section_content:
             manager_lines = section_content["користувачі"].strip().splitlines()
             for line in manager_lines:
                 if not line.strip().lower().startswith("додаткові:"):
                     manager_text += line.strip() + " " # Додаємо номери/юзернейми через пробіл
                 else:
                     # Обробляємо додаткових користувачів
                     extra_users = line.split(":", 1)[1].strip()
                     manager_text += extra_users + " "

        parsed_managers, manager_errors = parse_managers(manager_text.strip())
        if manager_errors:
            # Можна об'єднати помилки або взяти першу
            raise ValueError(f"Помилки в секції 'Користувачі': {'; '.join(manager_errors)}")
        data["managers"] = parsed_managers
    except Exception as e:
        logger.error(f"Помилка парсингу секції 'Користувачі': {e}")
        raise ValueError(f"Помилка обробки секції 'Користувачі': {e}")


    try:
        if "назви" in section_content:
            data["names"] = parse_names(section_content["назви"].strip())
        else:
            raise ValueError("Секція 'Назви:' відсутня.")
    except Exception as e:
        logger.error(f"Помилка парсингу секції 'Назви': {e}")
        raise ValueError(f"Помилка обробки секції 'Назви': {e}")


    try:
        if "uid" in section_content:
             data["uids"] = parse_uids(section_content["uid"].strip())
        else:
            raise ValueError("Секція 'UID:' відсутня.")
    except Exception as e:
        logger.error(f"Помилка парсингу секції 'UID': {e}")
        raise ValueError(f"Помилка обробки секції 'UID': {e}")

    # Перевірка на порожні секції (опціонально, залежно від вимог)
    if not data["names"]:
         raise ValueError("Секція 'Назви:' не містить даних.")
    if not data["uids"]:
         raise ValueError("Секція 'UID:' не містить даних.")
    # Менеджери можуть бути порожніми, якщо користувач їх не вказав

    # Фінальна перевірка відповідності кількості назв та UID
    if len(data["names"]) != len(data["uids"]):
        raise ValueError(f"Кількість назв ({len(data['names'])}) не збігається з кількістю UID ({len(data['uids'])}).")

    return data