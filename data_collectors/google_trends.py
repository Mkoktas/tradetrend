"""
Google Trends veri toplama modülü.
pytrends kütüphanesi ile Türkiye için haftalık trend verisi çeker.
"""

import time
import logging
from datetime import datetime, date, timedelta
from typing import Optional
import pandas as pd
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kırtasiye sektörü için anahtar kelimeler
KIRTASIYE_KEYWORDS = [
    "termos",
    "akıllı defter",
    "renkli kalemler",
    "silgi",
    "kalemlik",
    "okul çantası",
    "defter",
    "fosforlu kalem",
    "makas",
    "yapıştırıcı",
]

# pytrends max 5 keyword per request
BATCH_SIZE = 5


class GoogleTrendsCollector:
    def __init__(self, hl: str = "tr-TR", tz: int = 180, geo: str = "TR"):
        self.pytrends = TrendReq(hl=hl, tz=tz, timeout=(10, 25), retries=3, backoff_factor=0.5)
        self.geo = geo

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_interest_over_time(self, keywords: list[str], timeframe: str) -> pd.DataFrame:
        self.pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=self.geo, gprop="")
        df = self.pytrends.interest_over_time()
        if df.empty:
            logger.warning(f"No data returned for keywords: {keywords}")
            return pd.DataFrame()
        return df.drop(columns=["isPartial"], errors="ignore")

    def fetch_weekly_trends(
        self,
        keywords: list[str],
        weeks_back: int = 8,
    ) -> dict[str, list[dict]]:
        """
        Verilen keyword listesi için son N haftanın trend verisini çeker.
        Returns: {keyword: [{"week_start": date, "trend_score": int}, ...]}
        """
        end_date = date.today()
        start_date = end_date - timedelta(weeks=weeks_back)
        timeframe = f"{start_date.strftime('%Y-%m-%d')} {end_date.strftime('%Y-%m-%d')}"

        results: dict[str, list[dict]] = {kw: [] for kw in keywords}

        # pytrends 5 keyword limiti nedeniyle batch'ler halinde çek
        for i in range(0, len(keywords), BATCH_SIZE):
            batch = keywords[i : i + BATCH_SIZE]
            logger.info(f"Fetching Google Trends for: {batch}")

            try:
                df = self._fetch_interest_over_time(batch, timeframe)
                if df.empty:
                    continue

                for kw in batch:
                    if kw not in df.columns:
                        continue
                    for week_dt, score in df[kw].items():
                        results[kw].append(
                            {
                                "week_start": week_dt.date() if hasattr(week_dt, "date") else week_dt,
                                "trend_score": int(score),
                                "region": self.geo,
                                "keyword": kw,
                            }
                        )

            except ResponseError as e:
                logger.error(f"Google Trends API error for batch {batch}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error for batch {batch}: {e}")

            # Rate limiting: 1 saniye bekle
            if i + BATCH_SIZE < len(keywords):
                time.sleep(1)

        return results

    def fetch_regional_breakdown(self, keyword: str) -> dict[str, int]:
        """
        Türkiye içi bölgesel ilgi dağılımını çeker.
        Returns: {"Istanbul": 100, "Ankara": 75, ...}
        """
        try:
            self.pytrends.build_payload([keyword], cat=0, timeframe="today 3-m", geo=self.geo)
            region_df = self.pytrends.interest_by_region(resolution="REGION", inc_low_vol=True, inc_geo_code=False)
            if region_df.empty:
                return {}
            return region_df[keyword].to_dict()
        except Exception as e:
            logger.error(f"Regional breakdown error for '{keyword}': {e}")
            return {}

    def get_trending_searches(self) -> list[str]:
        """Türkiye'deki günlük trend aramaları."""
        try:
            trending = self.pytrends.trending_searches(pn="turkey")
            return trending[0].tolist()[:20]
        except Exception as e:
            logger.error(f"Trending searches error: {e}")
            return []

    def calculate_trend_change(self, trend_data: list[dict]) -> float:
        """
        Son 2 haftanın ortalamasını önceki 2 haftayla karşılaştırır.
        Returns: Yüzde değişim (-100 ile +∞ arası)
        """
        if len(trend_data) < 4:
            return 0.0

        sorted_data = sorted(trend_data, key=lambda x: x["week_start"])
        recent_avg = sum(d["trend_score"] for d in sorted_data[-2:]) / 2
        previous_avg = sum(d["trend_score"] for d in sorted_data[-4:-2]) / 2

        if previous_avg == 0:
            return 100.0 if recent_avg > 0 else 0.0

        return round(((recent_avg - previous_avg) / previous_avg) * 100, 2)


def collect_and_save(keywords: Optional[list[str]] = None, db_session=None) -> dict:
    """
    Pipeline entry point: keyword listesi için trend verisi toplar, opsiyonel olarak DB'ye kaydeder.
    """
    if keywords is None:
        keywords = KIRTASIYE_KEYWORDS

    collector = GoogleTrendsCollector()
    results = collector.fetch_weekly_trends(keywords)

    summary = {}
    for keyword, data in results.items():
        change = collector.calculate_trend_change(data)
        latest_score = data[-1]["trend_score"] if data else 0
        summary[keyword] = {
            "latest_score": latest_score,
            "trend_change_pct": change,
            "data_points": len(data),
        }
        logger.info(f"{keyword}: score={latest_score}, change={change:+.1f}%")

    if db_session:
        _save_to_db(results, db_session)

    return {"raw": results, "summary": summary}


def _save_to_db(results: dict, session) -> None:
    from database.models import Product, GoogleTrendsData

    for keyword, data_points in results.items():
        product = session.query(Product).filter_by(name=keyword, category="kirtasiye").first()
        if not product:
            product = Product(name=keyword, category="kirtasiye", keywords=[keyword])
            session.add(product)
            session.flush()

        for point in data_points:
            existing = (
                session.query(GoogleTrendsData)
                .filter_by(product_id=product.id, week_start=point["week_start"])
                .first()
            )
            if existing:
                existing.trend_score = point["trend_score"]
            else:
                session.add(
                    GoogleTrendsData(
                        product_id=product.id,
                        keyword=keyword,
                        trend_score=point["trend_score"],
                        week_start=point["week_start"],
                        region=point.get("region", "TR"),
                    )
                )

    session.commit()
    logger.info("Google Trends data saved to database.")


if __name__ == "__main__":
    import json

    print("Google Trends verisi çekiliyor: 'termos' için son 8 hafta...\n")
    collector = GoogleTrendsCollector()
    data = collector.fetch_weekly_trends(["termos", "akıllı defter", "renkli kalemler"])

    for keyword, points in data.items():
        change = collector.calculate_trend_change(points)
        print(f"\n{keyword}:")
        print(f"  Veri noktası: {len(points)}")
        if points:
            print(f"  Son skor: {points[-1]['trend_score']}")
            print(f"  Trend değişimi: {change:+.1f}%")
            print("  Son 4 hafta:")
            for p in points[-4:]:
                print(f"    {p['week_start']}: {p['trend_score']}")
