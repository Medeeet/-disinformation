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
    "disinformation":     "дезинформация",
    "phishing":           "фишинг",
    "social_engineering": "социальная инженерия",
    "scam":               "мошенничество",
    "propaganda":         "пропаганда",
    "safe":               "",
}

_THREAT_LABELS = {
    "disinformation":     "Дезинформация",
    "phishing":           "Фишинг",
    "social_engineering": "Социальная инженерия",
    "scam":               "Мошенничество (скам)",
    "propaganda":         "Пропаганда",
    "safe":               "Безопасно",
}

_THREAT_DESCRIPTIONS = {
    "disinformation":     "Текст содержит признаки дезинформации: манипулятивная риторика, кликбейт или ненадёжный источник",
    "phishing":           "Обнаружены признаки фишинговой атаки: запросы данных, имитация банков или госорганов",
    "social_engineering": "Обнаружены методы социальной инженерии: давление, запугивание, имитация власти",
    "scam":               "Обнаружены признаки мошенничества: фейковые выигрыши, схемы «комиссия за приз»",
    "propaganda":         "Источник относится к категории пропагандистских СМИ с низким рейтингом доверия",
    "safe":               "Информационных угроз не обнаружено",
}


def _build_verdict_label(verdict: str, threat_type: str) -> str:
    if verdict == "reliable":
        return "Угроз не обнаружено"
    if verdict == "uncertain":
        threat = _THREAT_NAMES.get(threat_type, "")
        return f"Неопределённо" + (f" / {threat}" if threat else "")
    if verdict == "suspicious":
        return f"Подозрительно: {_THREAT_LABELS.get(threat_type, 'неизвестная угроза')}"
    # likely_disinformation
    return f"Высокий риск: {_THREAT_LABELS.get(threat_type, 'неизвестная угроза')}"


def _build_verdict_description(verdict: str, threat_type: str) -> str:
    if verdict == "reliable":
        return _THREAT_DESCRIPTIONS["safe"]
    if verdict == "uncertain":
        return "Обнаружены слабые признаки угрозы, но их недостаточно для однозначного вывода"
    return _THREAT_DESCRIPTIONS.get(threat_type, "Обнаружены признаки информационной угрозы")


@router.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/api/v1/analyze")
async def analyze_endpoint(request: Request, text: str = Form(""), url: str = Form("")):
    input_text = text.strip()
    input_url = url.strip()

    if not input_text and not input_url:
        return HTMLResponse("<p class='error'>Введите текст или URL</p>", status_code=400)

    # Если указан URL, пытаемся извлечь текст
    if input_url and not input_text:
        import httpx
        from bs4 import BeautifulSoup

        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
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
            return HTMLResponse(f"<p class='error'>Ошибка загрузки URL: {e}</p>", status_code=400)

    if not input_text:
        return HTMLResponse("<p class='error'>Не удалось извлечь текст</p>", status_code=400)

    pool = getattr(request.app.state, "pool", None)
    result = await analyze_text(input_text, input_url or None, pool=pool)

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
        return HTMLResponse("<p>База данных недоступна</p>", status_code=503)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(SELECT_ANALYSIS_BY_ID, analysis_id)

    if not row:
        return HTMLResponse("<p>Анализ не найден</p>", status_code=404)

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
        return HTMLResponse("<p>База данных недоступна</p>", status_code=503)

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
        return {"status": "error", "detail": "База данных недоступна"}

    async with pool.acquire() as conn:
        await conn.execute(
            INSERT_SOURCE,
            source.domain,
            source.credibility_score,
            source.category,
            source.notes,
        )
    return {"status": "ok", "domain": source.domain}
