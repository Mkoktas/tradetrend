import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from trend_engine.scorer import TrendScorer, get_demo_signals

app = FastAPI(
    title="TradeTrend API",
    description="KOBİ ve esnaflar için yapay zeka destekli ürün trend analizi",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

scorer = TrendScorer()


@app.get("/")
def root():
    return {"service": "TradeTrend API", "version": "0.1.0", "status": "ok"}


@app.get("/api/v1/trends")
def get_trends(
    sector: str = Query(default="kirtasiye", description="Sektör adı"),
    top_n: int = Query(default=5, ge=1, le=20, description="Kaç ürün döneceği"),
):
    signals = get_demo_signals()
    results = scorer.get_top_n(signals, n=top_n)
    return {
        "sector": sector,
        "count": len(results),
        "results": [r.to_dict() for r in results],
    }


@app.get("/api/v1/trends/{product_name}")
def get_product_trend(product_name: str):
    signals = get_demo_signals()
    match = next((s for s in signals if s.name.lower() == product_name.lower()), None)
    if not match:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Ürün bulunamadı: {product_name}")
    result = scorer.score_product(match)
    return result.to_dict()


@app.get("/api/v1/health")
def health():
    return {"status": "healthy"}
