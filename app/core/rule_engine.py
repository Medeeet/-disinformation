"""Оркестратор всех правил."""

from app.rules.clickbait import check_clickbait
from app.rules.linguistic import check_linguistic
from app.rules.source_check import check_source
from app.rules.structural import check_structural
from app.rules.fact_check import check_fact_check
from app.rules.phishing import check_phishing


async def run_all_rules(text: str, url: str | None = None, pool=None) -> dict:
    """
    Запускает все правила и возвращает результат.

    Returns:
        {
            "scores": {
                "clickbait": float,
                "linguistic": float,
                "source_credibility": float,
                "structural": float,
                "fact_check": float | None,
                "phishing": float,
            },
            "combined_score": float,
            "flagged_patterns": list[str],
        }
    """
    all_flags: list[str] = []

    # Кликбейт
    clickbait_score, clickbait_flags = check_clickbait(text)
    all_flags.extend(clickbait_flags)

    # Лингвистика
    linguistic_score, linguistic_flags = check_linguistic(text)
    all_flags.extend(linguistic_flags)

    # Источник и безопасность URL
    source_score, source_flags = check_source(url)
    all_flags.extend(source_flags)

    # Структура
    structural_score, structural_flags = check_structural(text, url)
    all_flags.extend(structural_flags)

    # Фактчекинг (async)
    fact_check_score, fact_check_flags = await check_fact_check(text, pool=pool)
    all_flags.extend(fact_check_flags)

    # Фишинг и социальная инженерия
    phishing_score, phishing_flags = check_phishing(text, url)
    all_flags.extend(phishing_flags)

    # Взвешенный скор правил
    weights = {
        "clickbait": 0.20,
        "linguistic": 0.20,
        "source_credibility": 0.15,
        "structural": 0.15,
        "fact_check": 0.10,
        "phishing": 0.20,
    }

    scores = {
        "clickbait": clickbait_score,
        "linguistic": linguistic_score,
        "source_credibility": source_score,
        "structural": structural_score,
        "fact_check": fact_check_score,
        "phishing": phishing_score,
    }

    total_weight = 0.0
    weighted_sum = 0.0
    for key, score in scores.items():
        if score is not None:
            w = weights[key]
            weighted_sum += score * w
            total_weight += w

    combined_score = weighted_sum / total_weight if total_weight > 0 else 0.0

    return {
        "scores": scores,
        "combined_score": combined_score,
        "flagged_patterns": all_flags,
    }
