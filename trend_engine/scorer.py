"""
Trend Skoru Motoru — v0.2
Google Trends, Trendyol, Amazon TR ve TikTok verilerini birleştirerek
composite trend skoru, risk seviyesi ve kanal önerileri üretir.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
import math

logger = logging.getLogger(__name__)

# ─── Ağırlıklar — 4 kaynaklı model ───────────────────────────────────────────
WEIGHTS = {
    "google":   0.25,
    "trendyol": 0.35,
    "amazon":   0.25,
    "tiktok":   0.15,
}

# ─── Risk eşikleri ────────────────────────────────────────────────────────────
RISK_THRESHOLDS = {"low": 60, "medium": 35}

# ─── Kanal bazlı ağırlık matrisi ─────────────────────────────────────────────
CHANNEL_WEIGHTS = {
    "trendyol":  {"google": 0.20, "trendyol": 0.50, "amazon": 0.20, "tiktok": 0.10},
    "amazon_tr": {"google": 0.20, "trendyol": 0.20, "amazon": 0.50, "tiktok": 0.10},
    "instagram": {"google": 0.25, "trendyol": 0.15, "amazon": 0.15, "tiktok": 0.45},
    "store":     {"google": 0.35, "trendyol": 0.25, "amazon": 0.15, "tiktok": 0.25},
}


@dataclass
class ProductSignals:
    """Bir ürün için ham sinyal verisi — 4 kaynak."""
    name: str
    category: str = "kirtasiye"
    # Google Trends
    google_trend_score: float = 0.0
    google_trend_change_pct: float = 0.0
    # Trendyol
    trendyol_sales_rank: int = 999
    trendyol_rank_change: float = 0.0
    trendyol_review_count: int = 0
    trendyol_rating: float = 0.0
    # Amazon TR
    amazon_sales_rank: int = 999
    amazon_rank_change: float = 0.0
    amazon_review_count: int = 0
    amazon_rating: float = 0.0
    # TikTok
    tiktok_trend_score: float = 0.0
    tiktok_post_count: int = 0


@dataclass
class TrendResult:
    """Hesaplanmış trend skoru ve öneriler."""
    product_name: str
    google_score: float
    trendyol_score: float
    amazon_score: float
    tiktok_score: float
    composite_score: float
    risk_level: str
    risk_emoji: str
    channel_recommendations: dict
    best_channel: str
    weekly_forecast: list = field(default_factory=list)
    week_start: date = field(default_factory=date.today)

    def to_dict(self) -> dict:
        return {
            "product_name":           self.product_name,
            "google_score":           round(self.google_score, 1),
            "trendyol_score":         round(self.trendyol_score, 1),
            "amazon_score":           round(self.amazon_score, 1),
            "tiktok_score":           round(self.tiktok_score, 1),
            "composite_score":        round(self.composite_score, 1),
            "risk_level":             self.risk_level,
            "risk_emoji":             self.risk_emoji,
            "channel_recommendations": {k: round(v, 1) for k, v in self.channel_recommendations.items()},
            "best_channel":           self.best_channel,
            "weekly_forecast":        [round(v, 1) for v in self.weekly_forecast],
            "week_start":             self.week_start.isoformat(),
        }


class TrendScorer:
    def __init__(self):
        self.weights = WEIGHTS
        self.channel_weights = CHANNEL_WEIGHTS

    # ── Kaynak skorları ──────────────────────────────────────────────────────

    def calculate_google_score(self, signals: ProductSignals) -> float:
        base = signals.google_trend_score
        momentum = min(20, max(-20, signals.google_trend_change_pct * 0.4))
        return max(0.0, min(100.0, base + momentum))

    def calculate_trendyol_score(self, signals: ProductSignals) -> float:
        rank = signals.trendyol_sales_rank
        rank_score = 0.0 if rank <= 0 or rank >= 999 else max(0, 100 - math.log10(rank) * 50)
        rank_chg   = min(15, max(-15, signals.trendyol_rank_change * 0.5))
        reviews    = min(20, math.log10(max(signals.trendyol_review_count, 1)) * 5)
        rating     = (signals.trendyol_rating / 5) * 10 if signals.trendyol_rating > 0 else 0
        return max(0.0, min(100.0, rank_score * 0.55 + rank_chg + reviews * 0.30 + rating * 0.15))

    def calculate_amazon_score(self, signals: ProductSignals) -> float:
        """Amazon TR sıralaması, yorum sayısı ve rating'i birleştirerek skor üretir."""
        rank = signals.amazon_sales_rank
        rank_score = 0.0 if rank <= 0 or rank >= 999 else max(0, 100 - math.log10(rank) * 50)
        rank_chg   = min(15, max(-15, signals.amazon_rank_change * 0.5))
        reviews    = min(20, math.log10(max(signals.amazon_review_count, 1)) * 5)
        rating     = (signals.amazon_rating / 5) * 10 if signals.amazon_rating > 0 else 0
        return max(0.0, min(100.0, rank_score * 0.55 + rank_chg + reviews * 0.30 + rating * 0.15))

    def calculate_tiktok_score(self, signals: ProductSignals) -> float:
        return max(0.0, min(100.0, signals.tiktok_trend_score))

    # ── Composite & risk ────────────────────────────────────────────────────

    def calculate_composite_score(self, g: float, t: float, a: float, tk: float) -> float:
        w = self.weights
        return g * w["google"] + t * w["trendyol"] + a * w["amazon"] + tk * w["tiktok"]

    def determine_risk_level(self, composite: float) -> tuple:
        if composite >= RISK_THRESHOLDS["low"]:    return "low",    "🟢"
        elif composite >= RISK_THRESHOLDS["medium"]: return "medium", "🟡"
        else:                                        return "high",   "🔴"

    def calculate_channel_recommendations(self, g: float, t: float, a: float, tk: float) -> dict:
        scores = {"google": g, "trendyol": t, "amazon": a, "tiktok": tk}
        return {
            ch: round(sum(scores[src] * w for src, w in wts.items()), 1)
            for ch, wts in self.channel_weights.items()
        }

    # ── Haftalık tahmin ─────────────────────────────────────────────────────

    def generate_weekly_forecast(self, composite: float, trend_change: float, weeks: int = 6) -> list:
        fc = [composite]
        weekly_momentum = trend_change * 0.05
        for i in range(1, weeks):
            nv = fc[-1] + weekly_momentum * (0.8 ** i)
            nv = max(0.0, min(100.0, nv + (50 - nv) * 0.05))
            fc.append(round(nv, 1))
        return fc

    # ── Ana metod ───────────────────────────────────────────────────────────

    def score_product(self, signals: ProductSignals) -> TrendResult:
        g  = self.calculate_google_score(signals)
        t  = self.calculate_trendyol_score(signals)
        a  = self.calculate_amazon_score(signals)
        tk = self.calculate_tiktok_score(signals)
        composite = self.calculate_composite_score(g, t, a, tk)
        risk_level, risk_emoji = self.determine_risk_level(composite)
        channels   = self.calculate_channel_recommendations(g, t, a, tk)
        best_ch    = max(channels, key=channels.get)
        forecast   = self.generate_weekly_forecast(composite, signals.google_trend_change_pct)
        logger.info(f"{signals.name}: G={g:.1f} T={t:.1f} A={a:.1f} TK={tk:.1f} → {composite:.1f} [{risk_level}]")
        return TrendResult(
            product_name=signals.name,
            google_score=g, trendyol_score=t, amazon_score=a, tiktok_score=tk,
            composite_score=composite, risk_level=risk_level, risk_emoji=risk_emoji,
            channel_recommendations=channels, best_channel=best_ch,
            weekly_forecast=forecast,
            week_start=date.today() - timedelta(days=date.today().weekday()),
        )

    def rank_products(self, signals_list: list) -> list:
        return sorted([self.score_product(s) for s in signals_list],
                      key=lambda r: r.composite_score, reverse=True)

    def get_top_n(self, signals_list: list, n: int = 5) -> list:
        return self.rank_products(signals_list)[:n]


def get_demo_signals() -> list:
    return [
        ProductSignals("Termos",             google_trend_score=72, google_trend_change_pct=28.5,
                       trendyol_sales_rank=3,  trendyol_review_count=4520,  trendyol_rating=4.7,
                       amazon_sales_rank=12,   amazon_review_count=1800,    amazon_rating=4.5,
                       tiktok_trend_score=85),
        ProductSignals("Akıllı Defter",      google_trend_score=58, google_trend_change_pct=15.2,
                       trendyol_sales_rank=12, trendyol_review_count=1830,  trendyol_rating=4.5,
                       amazon_sales_rank=35,   amazon_review_count=620,     amazon_rating=4.2,
                       tiktok_trend_score=62),
        ProductSignals("Renkli Kalemler",    google_trend_score=65, google_trend_change_pct=8.3,
                       trendyol_sales_rank=7,  trendyol_review_count=8940,  trendyol_rating=4.8,
                       amazon_sales_rank=20,   amazon_review_count=3200,    amazon_rating=4.6,
                       tiktok_trend_score=71),
        ProductSignals("Okul Çantası",       google_trend_score=88, google_trend_change_pct=45.0,
                       trendyol_sales_rank=1,  trendyol_review_count=12000, trendyol_rating=4.9,
                       amazon_sales_rank=5,    amazon_review_count=4800,    amazon_rating=4.7,
                       tiktok_trend_score=92),
    ]
