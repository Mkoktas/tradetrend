"""
Trend Skoru Motoru için unit testler.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from trend_engine.scorer import TrendScorer, ProductSignals, WEIGHTS


@pytest.fixture
def scorer():
    return TrendScorer()


@pytest.fixture
def high_signal():
    return ProductSignals(
        name="Çok Satan Ürün",
        google_trend_score=90, google_trend_change_pct=40,
        trendyol_sales_rank=2, trendyol_review_count=10000, trendyol_rating=4.9,
        tiktok_trend_score=88,
    )


@pytest.fixture
def low_signal():
    return ProductSignals(
        name="Az Satan Ürün",
        google_trend_score=10, google_trend_change_pct=-20,
        trendyol_sales_rank=999, trendyol_review_count=10, trendyol_rating=2.0,
        tiktok_trend_score=5,
    )


def test_composite_score_range(scorer, high_signal, low_signal):
    high_result = scorer.score_product(high_signal)
    low_result = scorer.score_product(low_signal)

    assert 0 <= high_result.composite_score <= 100
    assert 0 <= low_result.composite_score <= 100
    assert high_result.composite_score > low_result.composite_score


def test_risk_levels(scorer, high_signal, low_signal):
    high_result = scorer.score_product(high_signal)
    low_result = scorer.score_product(low_signal)

    assert high_result.risk_level in ("low", "medium", "high")
    assert low_result.risk_level == "high"


def test_channel_recommendations_sum(scorer, high_signal):
    result = scorer.score_product(high_signal)
    channels = result.channel_recommendations
    assert set(channels.keys()) == {"trendyol", "instagram", "store"}
    assert all(0 <= v <= 100 for v in channels.values())


def test_best_channel_is_highest(scorer, high_signal):
    result = scorer.score_product(high_signal)
    assert result.best_channel == max(result.channel_recommendations, key=result.channel_recommendations.get)


def test_forecast_length(scorer, high_signal):
    result = scorer.score_product(high_signal)
    assert len(result.weekly_forecast) == 6


def test_forecast_values_in_range(scorer, high_signal):
    result = scorer.score_product(high_signal)
    assert all(0 <= v <= 100 for v in result.weekly_forecast)


def test_rank_products_ordering(scorer):
    signals = [
        ProductSignals("A", google_trend_score=80, trendyol_sales_rank=5, tiktok_trend_score=70),
        ProductSignals("B", google_trend_score=30, trendyol_sales_rank=50, tiktok_trend_score=20),
        ProductSignals("C", google_trend_score=60, trendyol_sales_rank=15, tiktok_trend_score=50),
    ]
    ranked = scorer.rank_products(signals)
    assert ranked[0].composite_score >= ranked[1].composite_score >= ranked[2].composite_score


def test_get_top_n(scorer):
    from trend_engine.scorer import get_demo_signals
    signals = get_demo_signals()
    top3 = scorer.get_top_n(signals, n=3)
    assert len(top3) == 3


def test_weights_sum_to_one():
    total = sum(WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9


def test_zero_trendyol_rank(scorer):
    s = ProductSignals("Test", trendyol_sales_rank=0)
    result = scorer.score_product(s)
    assert result.trendyol_score == 0.0


def test_to_dict_serializable(scorer, high_signal):
    result = scorer.score_product(high_signal)
    d = result.to_dict()
    import json
    json_str = json.dumps(d)
    assert "product_name" in json_str
    assert "composite_score" in json_str
