import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Пути
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"

# PostgreSQL — берётся из переменной окружения DATABASE_URL
# По умолчанию: локальная БД без пароля (для разработки)
DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/cybershield"
)

# ML
ONNX_MODEL_PATH = MODELS_DIR / "model.onnx"
TOKENIZER_PATH = MODELS_DIR / "tokenizer"
MAX_SEQ_LENGTH = 256

# Веса ансамбля
# ML_WEIGHT снижен до 0.40: ruBert обучен преимущественно на русском,
# для казахских текстов правила дают более надёжный сигнал.
ML_WEIGHT = 0.40
RULES_WEIGHT = 0.60

# Пороги вердиктов
THRESHOLDS = {
    "reliable": 0.28,
    "uncertain": 0.48,
    "suspicious": 0.68,
}

# Google Fact Check API
FACT_CHECK_API_KEY = ""  # Задать через переменную окружения
FACT_CHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
