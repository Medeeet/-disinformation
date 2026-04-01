"""Главный оркестратор анализа текста."""

import json
import uuid

from app.core.ml_engine import ml_engine
from app.core.rule_engine import run_all_rules
from app.core.score_combiner import combine_scores
from app.db.models import INSERT_ANALYSIS


def _detect_threat_type(rule_scores: dict, flagged_patterns: list[str]) -> str:
    """
    Определяет основной тип угрозы на основе rule_scores и флагов.

    Returns:
        'disinformation' | 'phishing' | 'social_engineering' | 'scam' | 'propaganda' | 'safe'
    """
    phishing   = rule_scores.get("phishing", 0) or 0
    source     = rule_scores.get("source_credibility", 0) or 0
    clickbait  = rule_scores.get("clickbait", 0) or 0
    linguistic = rule_scores.get("linguistic", 0) or 0

    has_social_eng = any("Социнженерия" in f for f in flagged_patterns)
    has_scam       = any("Скам" in f or "выигр" in f.lower() or "компенсаци" in f.lower()
                         for f in flagged_patterns)
    has_phishing   = any("Фишинг" in f for f in flagged_patterns)

    if phishing >= 0.45:
        if has_social_eng:
            return "social_engineering"
        if has_scam:
            return "scam"
        if has_phishing:
            return "phishing"
        return "phishing"

    if source >= 0.55:
        return "propaganda"

    if clickbait >= 0.25 or linguistic >= 0.25:
        return "disinformation"

    return "disinformation"


async def analyze_text(text: str, url: str | None = None, pool=None) -> dict:
    """
    Полный анализ текста: ML + правила → комбинированный скор.

    Returns:
        dict с полными результатами анализа.
    """
    analysis_id = str(uuid.uuid4())

    # ML-инференс
    ml_score = ml_engine.predict(text)

    # Правила
    rules_result = await run_all_rules(text, url, pool=pool)
    rule_score = rules_result["combined_score"]

    # Комбинирование
    overall_score, verdict = combine_scores(ml_score, rule_score)

    # Короткий текст: модель ненадёжна на < 30 словах — ограничиваем вердикт
    word_count = len(text.split())
    if word_count < 30:
        from app.config import THRESHOLDS
        # Не выше "uncertain" — недостаточно текста для уверенного вывода
        overall_score = min(overall_score, THRESHOLDS["uncertain"] - 0.01)
        verdict = "uncertain"
        rules_result["flagged_patterns"].insert(
            0, f"Мало текста ({word_count} слов) — для точного анализа нужно от 30 слов"
        )

    threat_type = _detect_threat_type(
        rules_result["scores"], rules_result["flagged_patterns"]
    ) if verdict != "reliable" else "safe"

    result = {
        "analysis_id": analysis_id,
        "overall_score": round(overall_score, 4),
        "verdict": verdict,
        "threat_type": threat_type,
        "ml_score": round(ml_score, 4) if ml_score is not None else None,
        "rule_scores": rules_result["scores"],
        "flagged_patterns": rules_result["flagged_patterns"],
    }

    # Сохраняем в БД
    details_json = json.dumps({
        "rule_scores": rules_result["scores"],
        "flagged_patterns": rules_result["flagged_patterns"],
        "threat_type": threat_type,
    }, ensure_ascii=False)

    if pool is not None:
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    INSERT_ANALYSIS,
                    analysis_id,
                    text[:5000],  # Ограничиваем длину
                    url,
                    overall_score,
                    ml_score,
                    rule_score,
                    verdict,
                    details_json,
                )
        except Exception:
            pass  # Не прерываем анализ из-за ошибки БД

    return result
