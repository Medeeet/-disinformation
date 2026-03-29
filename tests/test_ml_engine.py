"""Тесты для ML engine."""

import pytest
from app.core.ml_engine import MLEngine


class TestMLEngine:
    def test_not_loaded_returns_none(self):
        engine = MLEngine()
        assert engine.is_loaded is False
        assert engine.predict("любой текст") is None

    def test_load_without_model_file(self):
        engine = MLEngine()
        engine.load()  # Файл модели не существует
        assert engine.is_loaded is False

    def test_predict_without_load(self):
        engine = MLEngine()
        result = engine.predict("ШОК! Невероятная новость!")
        assert result is None
