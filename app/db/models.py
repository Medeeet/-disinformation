"""
SQL-запросы для работы с таблицами (asyncpg — плейсхолдеры $1, $2, ...).
"""

INSERT_ANALYSIS = """
INSERT INTO analyses (id, input_text, input_url, overall_score, ml_score, rule_score, verdict, details_json)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
"""

SELECT_ANALYSIS_BY_ID = """
SELECT * FROM analyses WHERE id = $1
"""

SELECT_ANALYSES_PAGE = """
SELECT * FROM analyses ORDER BY created_at DESC LIMIT $1 OFFSET $2
"""

SELECT_ANALYSES_COUNT = """
SELECT COUNT(*) FROM analyses
"""

INSERT_SOURCE = """
INSERT INTO sources (domain, credibility_score, category, notes, last_updated)
VALUES ($1, $2, $3, $4, NOW())
ON CONFLICT (domain) DO UPDATE SET
    credibility_score = EXCLUDED.credibility_score,
    category          = EXCLUDED.category,
    notes             = EXCLUDED.notes,
    last_updated      = NOW()
"""

SELECT_SOURCE_BY_DOMAIN = """
SELECT * FROM sources WHERE domain = $1
"""

SELECT_ALL_SOURCES = """
SELECT * FROM sources ORDER BY domain
"""

INSERT_FACT_CHECK_CACHE = """
INSERT INTO fact_check_cache (query_hash, response_json, fetched_at)
VALUES ($1, $2, NOW())
ON CONFLICT (query_hash) DO UPDATE SET
    response_json = EXCLUDED.response_json,
    fetched_at    = NOW()
"""

SELECT_FACT_CHECK_CACHE = """
SELECT response_json FROM fact_check_cache WHERE query_hash = $1
"""
