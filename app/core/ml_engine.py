"""ML-движок: загрузка и инференс ONNX модели."""

import logging
import os

import numpy as np

# transformers используется ТОЛЬКО для токенизатора (инференс идёт через ONNX Runtime),
# поэтому подавляем предупреждение об отсутствии PyTorch/TensorFlow/Flax —
# DL-бэкенд здесь не нужен.
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

from app.config import ONNX_MODEL_PATH, TOKENIZER_PATH, MAX_SEQ_LENGTH

logger = logging.getLogger(__name__)


class MLEngine:
    """Singleton-обёртка для ONNX Runtime инференса."""

    def __init__(self):
        self._session = None
        self._tokenizer = None
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def load(self):
        """Загружает модель и токенизатор. Вызывается при старте приложения."""
        if not ONNX_MODEL_PATH.exists():
            logger.warning(
                "ONNX модель не найдена по пути %s. ML-скор будет недоступен. "
                "Обучите модель на Colab и поместите model.onnx в папку models/",
                ONNX_MODEL_PATH,
            )
            return

        if not TOKENIZER_PATH.exists():
            logger.warning("Токенизатор не найден по пути %s", TOKENIZER_PATH)
            return

        try:
            import onnxruntime as ort

            self._session = ort.InferenceSession(
                str(ONNX_MODEL_PATH),
                providers=["CPUExecutionProvider"],
            )

            from transformers import AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(str(TOKENIZER_PATH))
            self._loaded = True
            logger.info("ML-модель загружена успешно")
        except ImportError as e:
            logger.warning("Не удалось импортировать onnxruntime/transformers: %s", e)
        except Exception as e:
            logger.error("Ошибка загрузки ML-модели: %s", e)

    def predict(self, text: str) -> float | None:
        """
        Предсказывает вероятность дезинформации.

        Returns:
            float (0.0–1.0) или None если модель не загружена.
        """
        if not self._loaded:
            return None

        try:
            inputs = self._tokenizer(
                text,
                max_length=MAX_SEQ_LENGTH,
                truncation=True,
                padding="max_length",
                return_tensors="np",
            )

            input_feed = {
                "input_ids": inputs["input_ids"].astype(np.int64),
                "attention_mask": inputs["attention_mask"].astype(np.int64),
            }

            # Добавляем token_type_ids если модель их принимает
            input_names = [inp.name for inp in self._session.get_inputs()]
            if "token_type_ids" in input_names and "token_type_ids" in inputs:
                input_feed["token_type_ids"] = inputs["token_type_ids"].astype(np.int64)

            outputs = self._session.run(None, input_feed)
            logits = outputs[0][0]

            # Softmax
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / exp_logits.sum()

            # Предполагаем: index 0 = reliable, index 1 = disinformation
            disinformation_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])

            return disinformation_prob

        except Exception as e:
            logger.error("Ошибка инференса: %s", e)
            return None


# Глобальный singleton
ml_engine = MLEngine()
