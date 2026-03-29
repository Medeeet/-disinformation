from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.db.database import init_db
from app.core.ml_engine import ml_engine
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    ml_engine.load()
    yield


app = FastAPI(
    title="Детектор дезинформации",
    description="Веб-система выявления дезинформации на основе ML и правил",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

app.include_router(router)
