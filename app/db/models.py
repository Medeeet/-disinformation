"""
SQL-запросы для работы с таблицами.
"""

INSERT_ANALYSIS = """
INSERT INTO analyses (id, input_text, input_url, overall_score, ml_score, rule_score, verdict, details_json)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

SELECT_ANALYSIS_BY_ID = """
SELECT * FROM analyses WHERE id = ?
"""

SELECT_ANALYSES_PAGE = """
SELECT * FROM analyses ORDER BY created_at DESC LIMIT ? OFFSET ?
"""

SELECT_ANALYSES_COUNT = """
SELECT COUNT(*) FROM analyses
"""

INSERT_SOURCE = """
INSERT OR REPLACE INTO sources (domain, credibility_score, category, notes, last_updated)
VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
"""

SELECT_SOURCE_BY_DOMAIN = """
SELECT * FROM sources WHERE domain = ?
"""

SELECT_ALL_SOURCES = """
SELECT * FROM sources ORDER BY domain
"""

INSERT_FACT_CHECK_CACHE = """
INSERT OR REPLACE INTO fact_check_cache (query_hash, response_json, fetched_at)
VALUES (?, ?, CURRENT_TIMESTAMP)
"""

SELECT_FACT_CHECK_CACHE = """
SELECT response_json FROM fact_check_cache WHERE query_hash = ?
"""
