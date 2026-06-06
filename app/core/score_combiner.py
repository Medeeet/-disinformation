"""Комбинирование ML-скора и скора правил в итоговый вердикт."""

from app.config import ML_WEIGHT, RULES_WEIGHT, THRESHOLDS

# Если ML уверенно бьёт тревогу, но все правила молчат —
# признак ложного срабатывания (особенно для казахских текстов).
_ML_ALARM_THRESHOLD = 0.88
_RULES_CLEAN_THRESHOLD = 0.18
# Правила практически молчат: ML без единого подтверждения. На казахских
# легитимных новостях ruBert тут часто ошибается. Эмпирически у реальной
# дезинформации правила дают >= 0.09 (кликбейт/структура), у ложных
# срабатываний на честных текстах — <= 0.03. Порог 0.06 разделяет их.
_RULES_SILENT_THRESHOLD = 0.06


def combine_scores(ml_score: float | None, rule_score: float) -> tuple[float, str]:
    """
    Комбинирует ML-скор и скор правил в итоговый вердикт.

    При конфликте ML vs. правил (ML кричит, правила молчат) —
    снижаем доверие к ML: актуально для казахских текстов, где
    ruBert даёт ложные срабатывания.

    Returns:
        (overall_score, verdict)
    """
    if ml_score is None:
        return rule_score, get_verdict(rule_score)

    if ml_score > _ML_ALARM_THRESHOLD and rule_score < _RULES_CLEAN_THRESHOLD:
        # Конфликт: ML уверенно бьёт тревогу, правила слабы. Различаем два случая.
        if rule_score < _RULES_SILENT_THRESHOLD:
            # Правила МОЛЧАТ полностью — ML без единого подтверждения. На
            # казахских легитимных новостях ruBert тут часто ошибается, поэтому
            # сильно снижаем доверие к ML: честный текст остаётся «надёжным».
            w_ml, w_rules = 0.20, 0.80
        else:
            # Есть слабое подтверждение правил (кликбейт/структура) — признак
            # реальной дезинформации. Оставляем ML заметный вес, чтобы уверенная
            # модель подняла вердикт до «подозрительно».
            w_ml, w_rules = 0.45, 0.55
    else:
        w_ml, w_rules = ML_WEIGHT, RULES_WEIGHT

    overall = w_ml * ml_score + w_rules * rule_score
    return overall, get_verdict(overall)


def get_verdict(score: float) -> str:
    if score < THRESHOLDS["reliable"]:
        return "reliable"
    elif score < THRESHOLDS["uncertain"]:
        return "uncertain"
    elif score < THRESHOLDS["suspicious"]:
        return "suspicious"
    else:
        return "likely_disinformation"
