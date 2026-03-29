"""Проверка репутации источника по домену."""

import json
import re
from urllib.parse import urlparse

from app.config import DATA_DIR

_sources_db: dict | None = None


def _load_sources() -> dict:
    global _sources_db
    if _sources_db is not None:
        return _sources_db

    path = DATA_DIR / "sources.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            _sources_db = {s["domain"]: s for s in data}
    else:
        _sources_db = {}
    return _sources_db


def _extract_domain(url: str) -> str | None:
    """Извлекает домен из URL."""
    if not url:
        return None
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        domain = parsed.hostname
        if domain and domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return None


# Легитимные домены для проверки мимикрии
LEGITIMATE_DOMAINS = {
    "bbc.com", "bbc.co.uk", "reuters.com", "apnews.com",
    "tass.ru", "ria.ru", "interfax.ru", "rbc.ru",
    "kommersant.ru", "vedomosti.ru", "lenta.ru",
    "meduza.io", "novayagazeta.ru",
}


def _check_domain_mimicry(domain: str) -> tuple[float, list[str]]:
    """Проверяет, мимикрирует ли домен под известный источник."""
    flags = []
    if not domain:
        return 0.0, flags

    for legit in LEGITIMATE_DOMAINS:
        legit_base = legit.split(".")[0]
        if legit_base in domain and domain != legit and not domain.endswith(f".{legit}"):
            flags.append(f"Домен '{domain}' похож на легитимный '{legit}'")
            return 0.8, flags

    return 0.0, flags


def _check_suspicious_tld(domain: str) -> tuple[float, list[str]]:
    """Проверяет подозрительные TLD."""
    flags = []
    if not domain:
        return 0.0, flags

    suspicious_tlds = {".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".buzz", ".click"}
    for tld in suspicious_tlds:
        if domain.endswith(tld):
            flags.append(f"Подозрительный домен верхнего уровня: {tld}")
            return 0.5, flags

    return 0.0, flags


def check_source(url: str | None) -> tuple[float, list[str]]:
    """
    Проверяет репутацию источника.
    Возвращает (score 0.0–1.0, list[str] найденных проблем).
    Скор: 0 = надёжный, 1 = ненадёжный.
    """
    if not url:
        return 0.0, []

    domain = _extract_domain(url)
    if not domain:
        return 0.0, []

    flags: list[str] = []
    scores: list[float] = []

    # Проверка по базе источников
    sources = _load_sources()
    if domain in sources:
        source_info = sources[domain]
        credibility = source_info.get("credibility_score", 0.5)
        # Инвертируем: credibility 0.0 (ненадёжный) → score 1.0
        score = 1.0 - credibility
        if score > 0.5:
            category = source_info.get("category", "")
            flags.append(f"Источник '{domain}' с низкой репутацией (категория: {category})")
        scores.append(score)

    # Проверка мимикрии
    score, mimicry_flags = _check_domain_mimicry(domain)
    if score > 0:
        scores.append(score)
        flags.extend(mimicry_flags)

    # Проверка TLD
    score, tld_flags = _check_suspicious_tld(domain)
    if score > 0:
        scores.append(score)
        flags.extend(tld_flags)

    if scores:
        final_score = max(scores)  # Берём максимальный сигнал
    else:
        final_score = 0.0

    return min(1.0, final_score), flags
