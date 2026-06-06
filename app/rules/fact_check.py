"""Интеграция с Google Fact Check Tools API."""

import hashlib
import json
import os

import httpx

from app.config import FACT_CHECK_API_KEY, FACT_CHECK_API_URL


def _get_api_key() -> str:
    return os.environ.get("FACT_CHECK_API_KEY", FACT_CHECK_API_KEY)


def _hash_query(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()


async def _get_cached(query_hash: str, pool) -> dict | None:
    """Ищет кэшированный результат."""
    if pool is None:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT response_json FROM fact_check_cache WHERE query_hash = $1",
                query_hash,
            )
            if row:
                return json.loads(row["response_json"])
    except Exception:
        pass
    return None


async def _save_cache(query_hash: str, response: dict, pool) -> None:
    """Сохраняет результат в кэш."""
    if pool is None:
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO fact_check_cache (query_hash, response_json, fetched_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (query_hash) DO UPDATE SET
                    response_json = EXCLUDED.response_json,
                    fetched_at    = NOW()
                """,
                query_hash,
                json.dumps(response, ensure_ascii=False),
            )
    except Exception:
        pass


def _extract_key_claims(text: str) -> list[str]:
    """
    Извлекает ключевые утверждения из текста для поиска.
    Берём первое предложение и наиболее «утвердительные» фразы.
    """
    import re
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    claims = []
    if sentences:
        # Первое предложение (обычно заголовок/тезис)
        claims.append(sentences[0][:200])

    # Предложения с утвердительными конструкциями
    for s in sentences[1:5]:
        if any(kw in s.lower() for kw in ("доказано", "выяснил", "установил", "подтвердил",
                                           "обнаружил", "заявил", "утверждает")):
            claims.append(s[:200])

    return claims[:3]  # Максимум 3 запроса


async def check_fact_check(text: str, pool=None) -> tuple[float | None, list[str]]:
    """
    Проверяет текст через Google Fact Check API.
    Возвращает (score или None если API недоступно, list[str] результатов).
    """
    api_key = _get_api_key()
    if not api_key:
        return None, []

    claims = _extract_key_claims(text)
    if not claims:
        return None, []

    all_results: list[dict] = []
    flags: list[str] = []

    async with httpx.AsyncClient(timeout=10) as client:
        for claim in claims:
            query_hash = _hash_query(claim)

            # Проверяем кэш
            cached = await _get_cached(query_hash, pool)
            if cached is not None:
                results = cached.get("claims", [])
            else:
                try:
                    resp = await client.get(
                        FACT_CHECK_API_URL,
                        params={
                            "key": api_key,
                            "query": claim,
                            "languageCode": "ru",
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        results = data.get("claims", [])
                        await _save_cache(query_hash, data, pool)
                    else:
                        continue
                except Exception:
                    continue

            all_results.extend(results)

    if not all_results:
        return None, []

    # Анализируем рейтинги фактчекеров
    false_count = 0
    true_count = 0
    mixed_count = 0

    for claim_data in all_results:
        for review in claim_data.get("claimReview", []):
            rating = review.get("textualRating", "").lower()
            claim_text = claim_data.get("text", "")[:100]

            if any(kw in rating for kw in ("false", "ложь", "неправда", "фейк", "fake")):
                false_count += 1
                publisher = review.get("publisher", {}).get("name", "Факт-тексеруші")
                flags.append(f"Факт-тексеру: '{claim_text}...' — {rating} ({publisher})")
            elif any(kw in rating for kw in ("true", "правда", "верно")):
                true_count += 1
            else:
                mixed_count += 1

    total = false_count + true_count + mixed_count
    if total == 0:
        return None, flags

    # Скор на основе фактчекинга
    score = false_count / total
    return min(1.0, score), flags
