"""Комбинирование ML-скора и скора правил в итоговый вердикт."""

from app.config import ML_WEIGHT, RULES_WEIGHT, THRESHOLDS


def combine_scores(ml_score: float | None, rule_score: float) -> tuple[float, str]:
    """
    Комбинирует ML-скор и скор правил.

    Returns:
        (overall_score, verdict)
    """
    if ml_score is not None:
        overall = ML_WEIGHT * ml_score + RULES_WEIGHT * rule_score
    else:
        # Если ML недоступна, используем только правила
        overall = rule_score

    verdict = get_verdict(overall)
    return overall, verdict


def get_verdict(score: float) -> str:
    """Определяет вердикт по скору."""
    if score < THRESHOLDS["reliable"]:
        return "reliable"
    elif score < THRESHOLDS["uncertain"]:
        return "uncertain"
    elif score < THRESHOLDS["suspicious"]:
        return "suspicious"
    else:
        return "likely_disinformation"
