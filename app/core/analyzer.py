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

    has_social_eng = any("Әлеуметтік инженерия" in f for f in flagged_patterns)
    has_scam       = any("Алаяқтық" in f for f in flagged_patterns)
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

    from app.config import THRESHOLDS
    from app.core.score_combiner import get_verdict

    source_score = rules_result["scores"].get("source_credibility") or 0.0

    # Короткий текст: модель ненадёжна на < 30 словах — ограничиваем вердикт
    word_count = len(text.split())
    insufficient_text = word_count < 30
    if insufficient_text:
        # Не выше "uncertain" — недостаточно текста для уверенного вывода
        overall_score = min(overall_score, THRESHOLDS["uncertain"] - 0.01)
        verdict = "uncertain"
        rules_result["flagged_patterns"].insert(
            0, f"Мәтін аз ({word_count} сөз) — нақты талдау үшін кемінде 30 сөз қажет"
        )

    # Репутация источника — высокоточный сигнал из курируемого списка, который
    # НЕ зависит от длины текста. Пропаганда часто стилистически «чистая» (ML даёт
    # низкий скор), поэтому известный недостоверный домен нельзя обнулять ни
    # усреднением, ни «недостатком текста» — иначе Царьград/Sputnik получают
    # «надёжно». Пол вердикта по репутации применяем даже к коротким текстам.
    if source_score >= 0.70:      # пропаганда / опасный URL → «подозрительно»
        floor = THRESHOLDS["uncertain"] + 0.07
    elif source_score >= 0.50:    # низкая достоверность → «неопределённо»
        floor = THRESHOLDS["reliable"] + 0.04
    else:
        floor = 0.0
    if overall_score < floor:
        overall_score = floor
        verdict = get_verdict(overall_score)

    # Доверенный источник (credibility >= 0.75 → source_score <= 0.25) при
    # молчащих правилах: крик ML здесь — ложное срабатывание (типично для
    # лент/разделов, где модель видит мешанину заголовков). Доверяем курируемому
    # списку и не вешаем «дезинформацию» на kapital.kz/forbes.kz и т.п.
    # 0 < source_score: домен реально найден в базе (а не «нет URL»).
    if 0 < source_score <= 0.25 and rule_score < 0.20:
        overall_score = min(overall_score, THRESHOLDS["reliable"] - 0.01)
        verdict = "reliable"

    # Тип угрозы. Репутация источника важнее «недостатка текста»: известный
    # пропаганда-домен помечаем как насихат даже без полноценной статьи.
    if verdict == "reliable":
        threat_type = "safe"
    elif source_score >= 0.55:
        threat_type = "propaganda"
    elif insufficient_text:
        threat_type = "insufficient_text"
    else:
        threat_type = _detect_threat_type(
            rules_result["scores"], rules_result["flagged_patterns"]
        )

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
