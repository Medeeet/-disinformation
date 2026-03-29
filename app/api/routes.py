import json
import math

from fastapi import APIRouter, Form, Query, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import aiosqlite

from app.config import BASE_DIR, DB_PATH
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

VERDICT_LABELS = {
    "reliable": "Достоверно",
    "uncertain": "Неопределённо",
    "suspicious": "Подозрительно",
    "likely_disinformation": "Вероятная дезинформация",
}
VERDICT_DESCRIPTIONS = {
    "reliable": "Текст не содержит значимых признаков дезинформации",
    "uncertain": "Обнаружены отдельные признаки, но их недостаточно для однозначного вывода",
    "suspicious": "Обнаружено несколько признаков дезинформации, рекомендуется проверить источник",
    "likely_disinformation": "Высокая вероятность дезинформации — множество признаков",
}


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

    result = await analyze_text(input_text, input_url or None)

    verdict = result["verdict"]
    template_data = {
        "request": request,
        "analysis_id": result["analysis_id"],
        "overall_score": result["overall_score"],
        "verdict": verdict,
        "verdict_label": VERDICT_LABELS.get(verdict, verdict),
        "verdict_description": VERDICT_DESCRIPTIONS.get(verdict, ""),
        "ml_score": result.get("ml_score"),
        "rule_scores": result["rule_scores"],
        "flagged_patterns": result.get("flagged_patterns", []),
        "input_text": input_text,
    }

    return templates.TemplateResponse("results_partial.html", template_data)


@router.get("/analysis/{analysis_id}", response_class=HTMLResponse)
async def analysis_detail(request: Request, analysis_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(SELECT_ANALYSIS_BY_ID, (analysis_id,))
        row = await cursor.fetchone()

    if not row:
        return HTMLResponse("<p>Анализ не найден</p>", status_code=404)

    details = json.loads(row["details_json"]) if row["details_json"] else {}
    verdict = row["verdict"]

    return templates.TemplateResponse("results.html", {
        "request": request,
        "overall_score": row["overall_score"],
        "verdict": verdict,
        "verdict_label": VERDICT_LABELS.get(verdict, verdict),
        "verdict_description": VERDICT_DESCRIPTIONS.get(verdict, ""),
        "ml_score": row["ml_score"],
        "rule_scores": details.get("rule_scores", {}),
        "flagged_patterns": details.get("flagged_patterns", []),
        "input_text": row["input_text"],
    })


@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, page: int = Query(1, ge=1)):
    per_page = 20
    offset = (page - 1) * per_page

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(SELECT_ANALYSES_COUNT)
        total = (await cursor.fetchone())[0]
        cursor = await db.execute(SELECT_ANALYSES_PAGE, (per_page, offset))
        rows = await cursor.fetchall()

    total_pages = max(1, math.ceil(total / per_page))

    return templates.TemplateResponse("history.html", {
        "request": request,
        "analyses": rows,
        "page": page,
        "total_pages": total_pages,
    })


@router.get("/api/v1/sources")
async def list_sources():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(SELECT_ALL_SOURCES)
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


@router.post("/api/v1/sources")
async def add_source(source: SourceRequest):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(INSERT_SOURCE, (
            source.domain, source.credibility_score, source.category, source.notes
        ))
        await db.commit()
    return {"status": "ok", "domain": source.domain}
