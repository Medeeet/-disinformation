import json
import math

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.api.schemas import AnalyzeRequest, AnalyzeResponse, SourceRequest
from app.core.analyzer import analyze_text
from app.db.models import (
    SELECT_ANALYSES_PAGE,
    SELECT_ANALYSES_COUNT,
    SELECT_ANALYSIS_BY_ID,
    INSERT_SOURCE,
    SELECT_ALL_SOURCES,
)

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

_THREAT_NAMES = {
    "disinformation":     "жалған ақпарат",
    "phishing":           "фишинг",
    "social_engineering": "әлеуметтік инженерия",
    "scam":               "алаяқтық",
    "propaganda":         "насихат",
    "safe":               "",
}

_THREAT_LABELS = {
    "disinformation":     "Жалған ақпарат",
    "phishing":           "Фишинг",
    "social_engineering": "Әлеуметтік инженерия",
    "scam":               "Алаяқтық (скам)",
    "propaganda":         "Насихат",
    "safe":               "Қауіпсіз",
}

_THREAT_DESCRIPTIONS = {
    "disinformation":     "Мәтінде жалған ақпарат белгілері бар: манипулятивті риторика, кликбейт немесе сенімсіз дереккөз",
    "phishing":           "Фишингтік шабуыл белгілері анықталды: деректерді сұрау, банктер немесе мемлекеттік органдарды имитациялау",
    "social_engineering": "Әлеуметтік инженерия әдістері анықталды: қысым, қорқыту, билікті имитациялау",
    "scam":               "Алаяқтық белгілері анықталды: жалған ұтыстар, «жүлде үшін комиссия» схемалары",
    "propaganda":         "Дереккөз сенім рейтингі төмен насихаттық БАҚ санатына жатады",
    "safe":               "Ақпараттық қауіптер анықталмады",
}


def _build_verdict_label(verdict: str, threat_type: str) -> str:
    if verdict == "reliable":
        return "Қауіп анықталмады"
    if verdict == "uncertain":
        if threat_type == "insufficient_text":
            return "Талдауға мәтін жеткіліксіз"
        threat = _THREAT_NAMES.get(threat_type, "")
        return f"Анық емес" + (f" / {threat}" if threat else "")
    if verdict == "suspicious":
        return f"Күмәнді: {_THREAT_LABELS.get(threat_type, 'белгісіз қауіп')}"
    # likely_disinformation
    return f"Жоғары қауіп: {_THREAT_LABELS.get(threat_type, 'белгісіз қауіп')}"


def _build_verdict_description(verdict: str, threat_type: str) -> str:
    if verdict == "reliable":
        return _THREAT_DESCRIPTIONS["safe"]
    if verdict == "uncertain":
        if threat_type == "insufficient_text":
            return "Талдау үшін мәтін тым қысқа — кемінде 30 сөз қажет"
        return "Қауіптің әлсіз белгілері анықталды, бірақ нақты қорытынды жасауға жеткіліксіз"
    return _THREAT_DESCRIPTIONS.get(threat_type, "Ақпараттық қауіп белгілері анықталды")


@router.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/api/v1/analyze")
async def analyze_endpoint(request: Request, text: str = Form(""), url: str = Form("")):
    input_text = text.strip()
    input_url = url.strip()

    if not input_text and not input_url:
        return HTMLResponse("<p class='error'>Мәтін немесе URL енгізіңіз</p>", status_code=400)

    # Если указан URL, пытаемся извлечь текст
    fetch_note: str | None = None
    if input_url and not input_text:
        import httpx
        from bs4 import BeautifulSoup

        # Браузерный User-Agent: многие сайты (Царьград, RT и др.) отдают 403/блок
        # на дефолтный httpx-агент. С реальным UA страница чаще загружается.
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ru,kk;q=0.9,en;q=0.8",
        }
        try:
            async with httpx.AsyncClient(
                timeout=15, follow_redirects=True, headers=headers
            ) as client:
                resp = await client.get(input_url)
                resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            # Удаляем скрипты и стили
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            paragraphs = soup.find_all("p")
            input_text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            if not input_text:
                input_text = soup.get_text(separator="\n", strip=True)
        except Exception as e:
            # Не прерываем анализ ошибкой: текст не получили, но домен может быть
            # известен — тогда вынесем вердикт по репутации источника (ниже).
            fetch_note = (
                f"Бетті жүктеу мүмкін болмады ({type(e).__name__}) — "
                f"талдау тек дереккөз беделі бойынша жүргізілді"
            )

    # Текст не получили (фетч упал или страница пустая).
    if not input_text:
        from app.rules.source_check import _extract_domain, _load_sources
        domain = _extract_domain(input_url) if input_url else None
        if domain and domain in _load_sources():
            # Домен есть в базе — анализируем по репутации источника без текста.
            input_text = ""
            if fetch_note is None:
                fetch_note = "Бет мазмұнын алу мүмкін болмады — талдау тек дереккөз беделі бойынша"
        else:
            msg = fetch_note or "Мәтінді алу мүмкін болмады"
            return HTMLResponse(f"<p class='error'>{msg}</p>", status_code=400)

    pool = getattr(request.app.state, "pool", None)
    result = await analyze_text(input_text, input_url or None, pool=pool)
    if fetch_note:
        result.setdefault("flagged_patterns", []).insert(0, fetch_note)

    verdict = result["verdict"]
    threat_type = result.get("threat_type", "disinformation")
    template_data = {
        "request": request,
        "analysis_id": result["analysis_id"],
        "overall_score": result["overall_score"],
        "verdict": verdict,
        "threat_type": threat_type,
        "threat_label": _THREAT_LABELS.get(threat_type, ""),
        "verdict_label": _build_verdict_label(verdict, threat_type),
        "verdict_description": _build_verdict_description(verdict, threat_type),
        "ml_score": result.get("ml_score"),
        "rule_scores": result["rule_scores"],
        "flagged_patterns": result.get("flagged_patterns", []),
        "input_text": input_text,
    }

    return templates.TemplateResponse("results_partial.html", template_data)


@router.get("/analysis/{analysis_id}", response_class=HTMLResponse)
async def analysis_detail(request: Request, analysis_id: str):
    pool = getattr(request.app.state, "pool", None)
    if pool is None:
        return HTMLResponse("<p>Дерекқор қолжетімсіз</p>", status_code=503)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(SELECT_ANALYSIS_BY_ID, analysis_id)

    if not row:
        return HTMLResponse("<p>Талдау табылмады</p>", status_code=404)

    details = json.loads(row["details_json"]) if row["details_json"] else {}
    verdict = row["verdict"]
    rule_scores = details.get("rule_scores", {})
    flagged = details.get("flagged_patterns", [])
    threat_type = details.get("threat_type") or (
        "safe" if verdict == "reliable" else "disinformation"
    )

    return templates.TemplateResponse("results.html", {
        "request": request,
        "overall_score": row["overall_score"],
        "verdict": verdict,
        "threat_type": threat_type,
        "threat_label": _THREAT_LABELS.get(threat_type, ""),
        "verdict_label": _build_verdict_label(verdict, threat_type),
        "verdict_description": _build_verdict_description(verdict, threat_type),
        "ml_score": row["ml_score"],
        "rule_scores": rule_scores,
        "flagged_patterns": flagged,
        "input_text": row["input_text"],
    })


@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, page: int = Query(1, ge=1)):
    per_page = 20
    offset = (page - 1) * per_page

    pool = getattr(request.app.state, "pool", None)
    if pool is None:
        return HTMLResponse("<p>Дерекқор қолжетімсіз</p>", status_code=503)

    async with pool.acquire() as conn:
        total_row = await conn.fetchrow(SELECT_ANALYSES_COUNT)
        total = total_row[0]
        rows = await conn.fetch(SELECT_ANALYSES_PAGE, per_page, offset)

    total_pages = max(1, math.ceil(total / per_page))

    return templates.TemplateResponse("history.html", {
        "request": request,
        "analyses": [dict(r) for r in rows],
        "page": page,
        "total_pages": total_pages,
    })


@router.get("/api/v1/sources")
async def list_sources(request: Request):
    pool = getattr(request.app.state, "pool", None)
    if pool is None:
        return []

    async with pool.acquire() as conn:
        rows = await conn.fetch(SELECT_ALL_SOURCES)
    return [dict(r) for r in rows]


@router.post("/api/v1/sources")
async def add_source(request: Request, source: SourceRequest):
    pool = getattr(request.app.state, "pool", None)
    if pool is None:
        return {"status": "error", "detail": "Дерекқор қолжетімсіз"}

    async with pool.acquire() as conn:
        await conn.execute(
            INSERT_SOURCE,
            source.domain,
            source.credibility_score,
            source.category,
            source.notes,
        )
    return {"status": "ok", "domain": source.domain}
