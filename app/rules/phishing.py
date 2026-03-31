"""Обнаружение фишинга и социальной инженерии.

Модуль кибербезопасности: выявляет признаки фишинговых атак,
скам-сообщений и методов социальной инженерии в тексте.
"""

import json
import re

from app.config import DATA_DIR

_patterns_cache: dict | None = None


def _load_patterns() -> dict:
    global _patterns_cache
    if _patterns_cache is not None:
        return _patterns_cache

    path = DATA_DIR / "phishing_patterns.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            _patterns_cache = json.load(f)
    else:
        _patterns_cache = {}
    return _patterns_cache


def _check_patterns(text: str, patterns: list[dict]) -> tuple[float, list[str]]:
    """Проверяет текст по списку паттернов."""
    flags = []
    max_score = 0.0

    for p in patterns:
        try:
            if re.search(p["pattern"], text, re.IGNORECASE):
                flags.append(f"[Кибербез] {p['label']}")
                max_score = max(max_score, p["weight"])
        except re.error:
            continue

    return max_score, flags


def _check_suspicious_urls_in_text(text: str) -> tuple[float, list[str]]:
    """Выявляет подозрительные URL внутри текста."""
    flags = []
    score = 0.0

    url_pattern = re.compile(
        r'https?://[^\s<>"\']+|(?<!\w)(?:www\.)[^\s<>"\']+',
        re.IGNORECASE,
    )
    urls = url_pattern.findall(text)

    for url in urls:
        url_lower = url.lower()

        # IP-адрес вместо домена
        if re.search(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url_lower):
            flags.append(f"[Кибербез] URL с IP-адресом вместо домена: {url[:60]}")
            score = max(score, 0.7)

        # Подозрительные сокращатели ссылок
        shorteners = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
                       "is.gd", "buff.ly", "clck.ru", "cutt.ly", "rb.gy"]
        for s in shorteners:
            if s in url_lower:
                flags.append(f"[Кибербез] Сокращённая ссылка ({s}) — может скрывать вредоносный URL")
                score = max(score, 0.5)
                break

        # Множество поддоменов (phishing.bank.secure.login.evil.com)
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url if "://" in url else f"https://{url}")
            hostname = parsed.hostname or ""
            if hostname.count(".") >= 4:
                flags.append(f"[Кибербез] Подозрительная структура URL (множество поддоменов): {hostname[:60]}")
                score = max(score, 0.6)
        except Exception:
            pass

        # Ключевые слова в URL, типичные для фишинга
        phish_keywords = ["login", "signin", "verify", "secure", "account",
                          "update", "confirm", "banking", "password", "auth"]
        domain_part = url_lower.split("?")[0]
        kw_count = sum(1 for kw in phish_keywords if kw in domain_part)
        if kw_count >= 2:
            flags.append(f"[Кибербез] URL содержит типичные фишинговые ключевые слова: {url[:60]}")
            score = max(score, 0.6)

    return score, flags


def _check_urgency_pressure(text: str) -> tuple[float, list[str]]:
    """Выявляет тактики давления через срочность (типично для социнженерии)."""
    flags = []
    score = 0.0

    urgency_phrases_ru = [
        (r"(?:осталось|есть|только|всего) \d+ (?:час|минут)", 0.5),
        (r"(?:предложение|акция) (?:ограничен|действует .{0,10}до)", 0.4),
        (r"не упустите .{0,20}(?:шанс|возможность)", 0.4),
        (r"(?:последний|единственный) (?:шанс|возможность)", 0.5),
    ]
    urgency_phrases_kz = [
        (r"(?:қалды|бар|тек) \d+ (?:сағат|минут)", 0.5),
        (r"мүмкіндікті жіберіп алмаңыз", 0.4),
        (r"(?:соңғы|жалғыз) мүмкіндік", 0.5),
    ]

    for pattern, weight in urgency_phrases_ru + urgency_phrases_kz:
        try:
            if re.search(pattern, text, re.IGNORECASE):
                flags.append(f"[Кибербез] Тактика давления через срочность")
                score = max(score, weight)
                break
        except re.error:
            continue

    return score, flags


def check_phishing(text: str, url: str | None = None) -> tuple[float, list[str]]:
    """
    Проверяет текст на признаки фишинга и социальной инженерии.

    Возвращает (score 0.0–1.0, list[str] обнаруженных угроз).
    Скор: 0 = безопасно, 1 = высокая вероятность фишинга/скама.
    """
    if not text:
        return 0.0, []

    all_flags: list[str] = []
    all_scores: list[float] = []

    data = _load_patterns()

    # Проверка по паттернам фишинга (RU + KZ)
    for category in ("phishing_ru", "phishing_kz",
                     "social_engineering_ru", "social_engineering_kz"):
        patterns = data.get(category, [])
        score, flags = _check_patterns(text, patterns)
        if score > 0:
            all_scores.append(score)
            all_flags.extend(flags)

    # Проверка URL в тексте
    score, flags = _check_suspicious_urls_in_text(text)
    if score > 0:
        all_scores.append(score)
        all_flags.extend(flags)

    # Тактики давления
    score, flags = _check_urgency_pressure(text)
    if score > 0:
        all_scores.append(score)
        all_flags.extend(flags)

    if not all_scores:
        return 0.0, []

    # Комбинируем: max + бонус за количество срабатываний
    max_score = max(all_scores)
    count_bonus = min(0.15, len(all_flags) * 0.03)
    final_score = min(1.0, max_score + count_bonus)

    return round(final_score, 4), all_flags
