"""Тесты для анализатора и score combiner."""

import pytest
from app.core.score_combiner import combine_scores, get_verdict


class TestScoreCombiner:
    def test_reliable_verdict(self):
        score, verdict = combine_scores(0.1, 0.1)
        assert verdict == "reliable"
        assert score < 0.3

    def test_uncertain_verdict(self):
        score, verdict = combine_scores(0.4, 0.4)
        assert verdict == "uncertain"

    def test_suspicious_verdict(self):
        score, verdict = combine_scores(0.6, 0.6)
        assert verdict == "suspicious"

    def test_disinformation_verdict(self):
        score, verdict = combine_scores(0.9, 0.8)
        assert verdict == "likely_disinformation"

    def test_no_ml_score(self):
        score, verdict = combine_scores(None, 0.2)
        assert score == 0.2
        assert verdict == "reliable"

    def test_no_ml_high_rules(self):
        score, verdict = combine_scores(None, 0.8)
        assert verdict == "likely_disinformation"

    def test_weighted_combination(self):
        # ML=0.6 * 0.6 + Rules=0.4 * 0.4 = 0.36 + 0.16 = 0.52
        score, verdict = combine_scores(0.6, 0.4)
        assert 0.5 <= score <= 0.55

    def test_get_verdict_boundaries(self):
        assert get_verdict(0.0) == "reliable"
        assert get_verdict(0.29) == "reliable"
        assert get_verdict(0.3) == "uncertain"
        assert get_verdict(0.49) == "uncertain"
        assert get_verdict(0.5) == "suspicious"
        assert get_verdict(0.69) == "suspicious"
        assert get_verdict(0.7) == "likely_disinformation"
        assert get_verdict(1.0) == "likely_disinformation"
