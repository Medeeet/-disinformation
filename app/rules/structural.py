"""Структурные и метаданные-эвристики для выявления дезинформации."""

import re


def check_structural(text: str, url: str | None = None) -> tuple[float, list[str]]:
    """
    Анализирует структурные признаки текста.
    Возвращает (score 0.0–1.0, list[str] найденных проблем).
    """
    flags: list[str] = []
    total_weight = 0.0
    max_weight = 3.0  # Для нормализации

    words = text.split()
    word_count = len(words)

    # Слишком короткий текст (< 50 слов) — подозрительно для статьи
    if word_count < 50:
        flags.append(f"Очень короткий текст ({word_count} слов)")
        total_weight += 0.4
    elif word_count < 100:
        flags.append(f"Короткий текст ({word_count} слов)")
        total_weight += 0.2

    # Нет ссылок на источники в тексте
    has_links = bool(re.search(r"https?://\S+", text))
    # Домен без протокола: например, parlament.kz, nationalbank.kz
    has_domain_ref = bool(re.search(r"\b\w[\w-]*\.(kz|ru|com|org|net|gov)\b", text, re.IGNORECASE))
    has_citations = bool(re.search(
        r"(?:по данным|согласно|как (?:сообщает|заявил|написал)|источник:|ссылка:|"
        r"хабарлады|жарияланған|деп хабарлады|баспасөз қызметі|пресс-служб)",
        text, re.IGNORECASE
    ))
    if not has_links and not has_domain_ref and not has_citations:
        flags.append("Отсутствуют ссылки на источники")
        total_weight += 0.3

    # Анонимные эксперты
    anonymous_experts = re.findall(
        r"(?:учёные|эксперты|специалисты|аналитики|врачи|исследователи)\s+"
        r"(?:утверждают|считают|доказали|выяснили|предупреждают|говорят)",
        text, re.IGNORECASE
    )
    if anonymous_experts and not re.search(r"(?:университет|институт|лаборатори|центр\s)", text, re.IGNORECASE):
        flags.append(f"Ссылки на анонимных экспертов без аффилиации ({len(anonymous_experts)} раз)")
        total_weight += 0.7

    # Чрезмерное количество абзацев из одного предложения
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if sentences:
        short_sentences = sum(1 for s in sentences if len(s.split()) < 8)
        short_ratio = short_sentences / len(sentences)
        if short_ratio > 0.7 and len(sentences) > 5:
            flags.append(f"Преобладают очень короткие предложения ({short_ratio:.0%})")
            total_weight += 0.3

    # Нет дат/временных привязок
    has_date = bool(re.search(
        r"\d{1,2}[./]\d{1,2}[./]\d{2,4}|\d{4}\s*год|\d{4}\s*жыл|"
        r"\b(?:январ|феврал|март|апрел|ма[йя]|июн|июл|август|сентябр|октябр|ноябр|декабр)\w*\s+\d{4}|"
        r"\b(?:қаңтар|ақпан|наурыз|сәуір|мамыр|маусым|шілде|тамыз|қыркүйек|қазан|қараша|желтоқсан)\w*",
        text, re.IGNORECASE
    ))
    if not has_date:
        flags.append("Отсутствуют конкретные даты")
        total_weight += 0.3

    # Призыв к распространению
    share_patterns = re.findall(
        r"(?:перешли|расскажи|поделись|репост|распространи|разошли|покажи всем|"
        r"максимальный\s+репост|пока\s+не\s+удалили)",
        text, re.IGNORECASE
    )
    if share_patterns:
        flags.append("Призыв к распространению")
        total_weight += 0.6

    score = min(1.0, total_weight / max_weight)
    return score, flags
