"""Лингвистические маркеры дезинформации с использованием pymorphy3."""

import json
import re

import pymorphy3

from app.config import DATA_DIR

_morph = pymorphy3.MorphAnalyzer()
_emotional_lexicon: dict | None = None


def _load_lexicon() -> dict:
    global _emotional_lexicon
    if _emotional_lexicon is not None:
        return _emotional_lexicon

    path = DATA_DIR / "emotional_lexicon.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            _emotional_lexicon = json.load(f)
    else:
        _emotional_lexicon = {"high_arousal": [], "manipulative": []}
    return _emotional_lexicon


def _analyze_verb_tenses(words: list[str]) -> tuple[float, list[str]]:
    """
    Дезинформация часто использует настоящее время для создания срочности.
    Достоверные источники чаще используют прошедшее время.
    """
    present_count = 0
    past_count = 0
    flags = []

    for word in words:
        parsed = _morph.parse(word)
        if not parsed:
            continue
        best = parsed[0]
        if "VERB" in best.tag or "INFN" in best.tag:
            if "pres" in best.tag:
                present_count += 1
            elif "past" in best.tag:
                past_count += 1

    total_verbs = present_count + past_count
    if total_verbs >= 3:
        present_ratio = present_count / total_verbs
        if present_ratio > 0.8:
            flags.append(f"Чрезмерное настоящее время ({present_ratio:.0%} глаголов)")
            return min(1.0, present_ratio * 0.6), flags
        elif present_ratio > 0.6:
            flags.append(f"Повышенное настоящее время ({present_ratio:.0%} глаголов)")
            return present_ratio * 0.3, flags

    return 0.0, flags


def _analyze_pronouns(words: list[str]) -> tuple[float, list[str]]:
    """
    Дезинформация избегает первого лица, использует безличные конструкции.
    """
    first_person = 0
    third_person = 0
    impersonal = 0
    flags = []

    for word in words:
        lower = word.lower()
        if lower in ("я", "мы", "мой", "наш", "моё", "наше", "мною", "нами"):
            first_person += 1
        elif lower in ("он", "она", "они", "его", "её", "их", "им"):
            third_person += 1

    # Безличные конструкции
    text_joined = " ".join(words).lower()
    impersonal_patterns = [
        r"(?:как\s+)?известно,?\s*что",
        r"по\s+(?:данным|информации|сведениям)",
        r"(?:учёные|эксперты|специалисты)\s+(?:утверждают|считают|говорят|заявляют)",
        r"(?:было|стало)\s+известно",
    ]
    for pattern in impersonal_patterns:
        matches = re.findall(pattern, text_joined)
        impersonal += len(matches)

    total = first_person + third_person + impersonal
    if total >= 2:
        if first_person == 0 and (third_person + impersonal) >= 3:
            flags.append("Полное отсутствие первого лица — безличный стиль")
            return 0.5, flags
        elif first_person == 0:
            flags.append("Отсутствие первого лица")
            return 0.2, flags

    return 0.0, flags


def _analyze_emotional_loading(words: list[str]) -> tuple[float, list[str]]:
    """Проверяет наличие эмоционально нагруженной лексики."""
    lexicon = _load_lexicon()
    high_arousal = set(lexicon.get("high_arousal", []) + lexicon.get("high_arousal_kz", []))
    manipulative = set(lexicon.get("manipulative", []) + lexicon.get("manipulative_kz", []))
    flags = []
    arousal_count = 0
    manip_count = 0

    for word in words:
        parsed = _morph.parse(word)
        if not parsed:
            continue
        normal = parsed[0].normal_form
        if normal in high_arousal:
            arousal_count += 1
        if normal in manipulative:
            manip_count += 1

    if len(words) > 0:
        arousal_ratio = arousal_count / len(words)
        if arousal_ratio > 0.05:
            flags.append(f"Высокая эмоциональная нагруженность ({arousal_count} слов)")
            score = min(1.0, arousal_ratio * 10)
        elif arousal_count >= 3:
            flags.append(f"Умеренная эмоциональная нагруженность ({arousal_count} слов)")
            score = 0.3
        else:
            score = arousal_count * 0.05

        if manip_count >= 2:
            flags.append(f"Манипулятивная лексика ({manip_count} слов)")
            score = min(1.0, score + manip_count * 0.15)
    else:
        score = 0.0

    return score, flags


def check_linguistic(text: str) -> tuple[float, list[str]]:
    """
    Комплексный лингвистический анализ текста.
    Возвращает (score 0.0–1.0, list[str] найденных маркеров).
    """
    words = re.findall(r"[а-яёА-ЯЁa-zA-Z]+", text)
    if not words:
        return 0.0, []

    all_flags: list[str] = []
    scores: list[float] = []

    # Анализ времён глаголов
    score, flags = _analyze_verb_tenses(words)
    scores.append(score)
    all_flags.extend(flags)

    # Анализ местоимений
    score, flags = _analyze_pronouns(words)
    scores.append(score)
    all_flags.extend(flags)

    # Эмоциональная нагруженность
    score, flags = _analyze_emotional_loading(words)
    scores.append(score)
    all_flags.extend(flags)

    # Общий лингвистический скор — среднее взвешенное
    if scores:
        final_score = sum(scores) / len(scores)
    else:
        final_score = 0.0

    return min(1.0, final_score), all_flags
