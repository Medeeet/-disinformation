from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Пути
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "disinformation.db"

# ML
ONNX_MODEL_PATH = MODELS_DIR / "model.onnx"
TOKENIZER_PATH = MODELS_DIR / "tokenizer"
MAX_SEQ_LENGTH = 256

# Веса ансамбля
ML_WEIGHT = 0.6
RULES_WEIGHT = 0.4

# Пороги вердиктов
THRESHOLDS = {
    "reliable": 0.3,
    "uncertain": 0.5,
    "suspicious": 0.7,
}

# Google Fact Check API
FACT_CHECK_API_KEY = ""  # Задать через переменную окружения
FACT_CHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
