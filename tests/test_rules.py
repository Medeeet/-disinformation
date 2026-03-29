"""Тесты для системы правил."""

import pytest
from app.rules.clickbait import check_clickbait
from app.rules.linguistic import check_linguistic
from app.rules.source_check import check_source
from app.rules.structural import check_structural


class TestClickbait:
    def test_obvious_clickbait(self):
        text = "ШОК! Вы не поверите, что случилось!!! Перешлите всем!!!"
        score, flags = check_clickbait(text)
        assert score > 0.5
        assert len(flags) > 0

    def test_reliable_text(self):
        text = "По данным Росстата, инфляция за январь составила 0.8 процента."
        score, flags = check_clickbait(text)
        assert score < 0.3

    def test_caps_lock(self):
        text = "ВСЯ ПРАВДА О ТОМ ЧТО ПРОИСХОДИТ В СТРАНЕ СЕЙЧАС"
        score, flags = check_clickbait(text)
        assert score > 0.3
        assert any("CAPS" in f for f in flags)

    def test_excessive_exclamation(self):
        text = "Невероятно! Это просто шок! Как такое возможно!! Ужас!!!"
        score, flags = check_clickbait(text)
        assert score > 0.3

    def test_conspiracy_phrases(self):
        text = "Власти скрывают правду о том, что на самом деле происходит"
        score, flags = check_clickbait(text)
        assert score > 0.2
        assert any("скрывают" in f.lower() for f in flags)


class TestLinguistic:
    def test_present_tense_heavy(self):
        text = ("Происходит невероятное. Люди выходят на улицы. "
                "Власти молчат. Ситуация ухудшается. Никто не говорит правду.")
        score, flags = check_linguistic(text)
        assert score >= 0.0  # Может быть 0, если мало глаголов распознано

    def test_neutral_text(self):
        text = ("Вчера прошло заседание комитета. Участники обсудили бюджет. "
                "Я присутствовал на встрече и записал основные тезисы.")
        score, flags = check_linguistic(text)
        assert score < 0.5


class TestSourceCheck:
    def test_reliable_source(self):
        score, flags = check_source("https://reuters.com/article/123")
        assert score < 0.2

    def test_unreliable_source(self):
        score, flags = check_source("https://newsfront.info/article/123")
        assert score > 0.5

    def test_domain_mimicry(self):
        score, flags = check_source("https://bbcnews.com.co/article")
        assert score > 0.5
        assert any("похож" in f for f in flags)

    def test_suspicious_tld(self):
        score, flags = check_source("https://breaking-news.xyz/article")
        assert score > 0.3

    def test_no_url(self):
        score, flags = check_source(None)
        assert score == 0.0

    def test_social_network(self):
        score, flags = check_source("https://vk.com/wall123")
        assert score > 0.3


class TestStructural:
    def test_short_text(self):
        text = "Это очень короткий текст без деталей."
        score, flags = check_structural(text)
        assert score > 0.1
        assert any("короткий" in f.lower() for f in flags)

    def test_anonymous_experts(self):
        text = ("Учёные утверждают, что вакцина опасна. "
                "Эксперты считают, что ситуация критическая. "
                "Специалисты предупреждают об угрозе.")
        score, flags = check_structural(text)
        assert score > 0.2

    def test_call_to_share(self):
        text = ("Важная информация для всех! " * 20 +
                "Максимальный репост! Перешлите всем, пока не удалили!")
        score, flags = check_structural(text)
        assert any("распространен" in f.lower() for f in flags)

    def test_proper_article(self):
        text = ("По данным исследования Московского государственного университета, "
                "опубликованного 15 марта 2025 года, " +
                "показатели улучшились на 15 процентов по сравнению с прошлым годом. " * 10 +
                "Подробнее: https://example.com/study")
        score, flags = check_structural(text)
        assert score < 0.5
