"""Проверка репутации источника и безопасности URL.

Модуль кибербезопасности: анализ доменов, обнаружение тайпсквоттинга,
фишинговых URL, подозрительных TLD и структурных аномалий URL.
"""

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

# Казахстанские домены для проверки тайпсквоттинга
KZ_LEGITIMATE_DOMAINS = {
    "egov.kz", "gov.kz", "nationalbank.kz", "kaspi.kz",
    "halykbank.kz", "tengrinews.kz", "zakon.kz", "inform.kz",
    "kapital.kz", "vlast.kz", "forbes.kz", "nur.kz",
}


def _check_domain_mimicry(domain: str) -> tuple[float, list[str]]:
    """Проверяет, мимикрирует ли домен под известный источник (тайпсквоттинг)."""
    flags = []
    if not domain:
        return 0.0, flags

    all_legit = LEGITIMATE_DOMAINS | KZ_LEGITIMATE_DOMAINS

    for legit in all_legit:
        legit_base = legit.split(".")[0]
        if legit_base in domain and domain != legit and not domain.endswith(f".{legit}"):
            flags.append(f"[Киберқауіпсіздік] Тайпсквоттинг: '{domain}' домені '{legit}'-ке еліктейді")
            return 0.8, flags

    # Проверка на замену символов (гомоглифы / опечатки)
    _typosquat_pairs = {
        "kaspi": ["kasp1", "kaspl", "kaspy", "kaspii", "kaspi-bank"],
        "egov": ["eg0v", "eqov", "egov-kz", "e-gov"],
        "halyk": ["ha1yk", "haluk", "halyk-bank"],
        "tengri": ["tengr1", "tenqri", "tengrl"],
    }
    domain_base = domain.split(".")[0].lower()
    for legit_name, typos in _typosquat_pairs.items():
        for typo in typos:
            if domain_base == typo or domain_base.startswith(typo):
                flags.append(f"[Киберқауіпсіздік] Тайпсквоттинг: '{domain}' '{legit_name}'-ге ұқсас")
                return 0.85, flags

    return 0.0, flags


def _check_suspicious_tld(domain: str) -> tuple[float, list[str]]:
    """Проверяет подозрительные TLD."""
    flags = []
    if not domain:
        return 0.0, flags

    suspicious_tlds = {".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".buzz", ".click",
                       ".work", ".racing", ".download", ".stream", ".loan", ".date", ".win"}
    for tld in suspicious_tlds:
        if domain.endswith(tld):
            flags.append(f"[Киберқауіпсіздік] Күмәнді жоғарғы деңгейлі домен: {tld}")
            return 0.5, flags

    return 0.0, flags


def _check_url_security(url: str) -> tuple[float, list[str]]:
    """Расширенный анализ безопасности URL."""
    flags = []
    scores = []

    if not url:
        return 0.0, flags

    # HTTP без шифрования
    if url.lower().startswith("http://"):
        flags.append("[Киберқауіпсіздік] Шифрлаусыз URL (HTTPS орнына HTTP)")
        scores.append(0.3)

    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
    except Exception:
        return 0.0, flags

    hostname = parsed.hostname or ""
    path = parsed.path or ""
    query = parsed.query or ""

    # IP-адрес вместо домена
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', hostname):
        flags.append(f"[Киберқауіпсіздік] URL домен орнына IP-мекенжайын қолданады: {hostname}")
        scores.append(0.7)

    # Избыточная длина URL (часто используется в фишинге)
    if len(url) > 200:
        flags.append(f"[Киберқауіпсіздік] Күмәнді ұзын URL ({len(url)} таңба)")
        scores.append(0.4)

    # Множество поддоменов
    if hostname.count(".") >= 4:
        flags.append(f"[Киберқауіпсіздік] Көп субдомен: {hostname}")
        scores.append(0.6)

    # Символ @ в URL (редирект-трюк)
    if "@" in url.split("//", 1)[-1].split("/", 1)[0]:
        flags.append("[Киберқауіпсіздік] URL-дегі @ таңбасы — нақты доменді жасыру мүмкіндігі")
        scores.append(0.8)

    # Кодированные символы в домене
    if "%" in hostname:
        flags.append("[Киберқауіпсіздік] Домен атындағы URL-кодтау — обфускация мүмкіндігі")
        scores.append(0.6)

    # Подозрительные ключевые слова в пути
    phish_path_keywords = ["login", "signin", "verify", "secure", "account",
                           "update", "confirm", "banking", "password", "wallet"]
    path_lower = path.lower()
    kw_found = [kw for kw in phish_path_keywords if kw in path_lower]
    if len(kw_found) >= 2:
        flags.append(f"[Киберқауіпсіздік] URL-де фишинг кілт сөздері бар: {', '.join(kw_found)}")
        scores.append(0.5)

    # Двойное расширение файла
    if re.search(r'\.\w{2,4}\.\w{2,4}$', path):
        flags.append("[Киберқауіпсіздік] URL-дегі қос файл кеңейтімі — жасыру мүмкіндігі")
        scores.append(0.6)

    if scores:
        return min(1.0, max(scores)), flags
    return 0.0, flags


def check_source(url: str | None) -> tuple[float, list[str]]:
    """
    Проверяет репутацию источника и безопасность URL.
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
            flags.append(f"'{domain}' дереккөзінің беделі төмен (санаты: {category})")
        scores.append(score)

    # Проверка мимикрии / тайпсквоттинга
    score, mimicry_flags = _check_domain_mimicry(domain)
    if score > 0:
        scores.append(score)
        flags.extend(mimicry_flags)

    # Проверка TLD
    score, tld_flags = _check_suspicious_tld(domain)
    if score > 0:
        scores.append(score)
        flags.extend(tld_flags)

    # Расширенный анализ безопасности URL
    score, security_flags = _check_url_security(url)
    if score > 0:
        scores.append(score)
        flags.extend(security_flags)

    if scores:
        final_score = max(scores)  # Берём максимальный сигнал
    else:
        final_score = 0.0

    return min(1.0, final_score), flags
