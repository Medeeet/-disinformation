"""Детекция кликбейта по паттернам и эвристикам."""

import json
import re
from pathlib import Path

from app.config import DATA_DIR

_patterns: list[dict] | None = None


def _load_patterns() -> list[dict]:
    global _patterns
    if _patterns is not None:
        return _patterns

    path = DATA_DIR / "clickbait_patterns.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            _patterns = json.load(f)
    else:
        _patterns = []
    return _patterns


# Встроенные паттерны (всегда работают)
BUILTIN_PATTERNS = [
    # Кликбейтные фразы (русские)
    (r"(?i)\bшок\b[!]*", 0.8, "Кликбейтное слово: ШОК"),
    (r"(?i)\bсрочно\b[!]*", 0.7, "Кликбейтное слово: СРОЧНО"),
    (r"(?i)\bсенсация\b", 0.7, "Кликбейтное слово: СЕНСАЦИЯ"),
    (r"(?i)вы не поверите", 0.6, "Кликбейтная фраза: 'вы не поверите'"),
    (r"(?i)вот что на самом деле", 0.5, "Кликбейтная фраза: 'вот что на самом деле'"),
    (r"(?i)стало известно,?\s*что", 0.4, "Безатрибутивная фраза: 'стало известно, что'"),
    (r"(?i)никто не ожидал", 0.5, "Кликбейтная фраза: 'никто не ожидал'"),
    (r"(?i)это изменит всё", 0.5, "Кликбейтная фраза: 'это изменит всё'"),
    (r"(?i)скрывают правду", 0.7, "Конспирологическая фраза: 'скрывают правду'"),
    (r"(?i)вся правда о", 0.5, "Кликбейтная фраза: 'вся правда о'"),
    (r"(?i)то,?\s*что.*скрыва", 0.6, "Конспирологическая фраза о сокрытии"),
    (r"(?i)власти\s+(?:скрывают|молчат|не говорят)", 0.7, "Конспирологическая фраза о властях"),
    # Числа в заголовке (типично для кликбейта)
    (r"^\d+\s+(?:причин|способ|факт|секрет|ошибок|признак)", 0.4, "Числовой кликбейт в начале"),
]


def check_clickbait(text: str) -> tuple[float, list[str]]:
    """
    Анализирует текст на кликбейт.
    Возвращает (score 0.0–1.0, list[str] найденных паттернов).
    """
    flags: list[str] = []
    total_weight = 0.0

    # Встроенные паттерны
    for pattern, weight, label in BUILTIN_PATTERNS:
        if re.search(pattern, text):
            flags.append(label)
            total_weight += weight

    # Паттерны из JSON-файла
    for p in _load_patterns():
        regex = p.get("pattern", "")
        weight = p.get("weight", 0.3)
        label = p.get("label", "Паттерн из базы")
        if regex and re.search(regex, text, re.IGNORECASE):
            flags.append(label)
            total_weight += weight

    # Чрезмерная пунктуация
    exclamation_count = text.count("!")
    if exclamation_count >= 5:
        flags.append(f"Чрезмерное количество '!' ({exclamation_count})")
        total_weight += min(0.8, exclamation_count * 0.1)
    elif exclamation_count >= 3:
        flags.append(f"Повышенное количество '!' ({exclamation_count})")
        total_weight += 0.3

    # Чрезмерные заглавные буквы
    words = text.split()
    if words:
        caps_words = sum(1 for w in words if w.isupper() and len(w) > 2)
        caps_ratio = caps_words / len(words)
        if caps_ratio > 0.3:
            flags.append(f"Чрезмерное использование CAPS LOCK ({caps_ratio:.0%})")
            total_weight += 0.6
        elif caps_ratio > 0.15:
            flags.append(f"Повышенное использование CAPS LOCK ({caps_ratio:.0%})")
            total_weight += 0.3

    # Множественные вопросительные/восклицательные знаки
    if re.search(r"[!?]{3,}", text):
        flags.append("Множественные знаки пунктуации (!!!, ???)")
        total_weight += 0.4

    # Нормализация: максимум 1.0
    score = min(1.0, total_weight / 3.0)  # Делим на 3 для нормализации

    return score, flags
