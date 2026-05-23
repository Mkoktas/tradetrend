"""
TradeTrend veri toplama pipeline'ı.
Günlük cron job olarak veya elle çalıştırılabilir.

Kullanım:
  python run_pipeline.py               # tüm veri kaynakları
  python run_pipeline.py --source google
  python run_pipeline.py --source trendyol
  python run_pipeline.py --source tiktok
  python run_pipeline.py --demo        # DB olmadan demo modu
"""

import argparse
import logging
import sys
import io
from datetime import datetime

# Windows konsolunda UTF-8 çıktı için
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("pipeline")


def run_google_trends(db_session=None) -> dict:
    from data_collectors.google_trends import collect_and_save, KIRTASIYE_KEYWORDS
    logger.info("Google Trends verisi toplanıyor...")
    result = collect_and_save(keywords=KIRTASIYE_KEYWORDS, db_session=db_session)
    logger.info(f"Google Trends: {len(result['summary'])} keyword işlendi.")
    return result["summary"]


def run_trendyol_scraper(db_session=None) -> list:
    from data_collectors.trendyol_scraper import collect_and_save
    logger.info("Trendyol scraping başlıyor...")
    products = collect_and_save(category="kirtasiye", db_session=db_session)
    logger.info(f"Trendyol: {len(products)} ürün toplandı.")
    return products


def run_tiktok_scraper(db_session=None) -> list:
    from data_collectors.tiktok_scraper import collect_and_save, KIRTASIYE_HASHTAGS
    logger.info("TikTok trend verisi toplanıyor...")
    results = collect_and_save(hashtags=KIRTASIYE_HASHTAGS, db_session=db_session)
    logger.info(f"TikTok: {len(results)} hashtag işlendi.")
    return results


def run_scorer(db_session=None) -> list:
    from trend_engine.scorer import TrendScorer, get_demo_signals, build_signals_from_db

    scorer = TrendScorer()

    if db_session:
        signals = build_signals_from_db("kirtasiye", db_session)
        logger.info(f"DB'den {len(signals)} ürün sinyali yüklendi.")
    else:
        signals = get_demo_signals()
        logger.info("Demo sinyaller kullanılıyor.")

    top5 = scorer.get_top_n(signals, n=5)
    logger.info("=== TOP 5 ÜRÜN ===")
    for i, r in enumerate(top5, 1):
        logger.info(f"  {i}. {r.product_name}: {r.composite_score:.1f}/100 [{r.risk_level}]")

    return top5


def run_demo() -> None:
    """Veritabanı olmadan demo pipeline."""
    print("\n" + "=" * 60)
    print("TradeTrend MVP — Demo Pipeline")
    print("=" * 60 + "\n")

    print("1️⃣  Google Trends simülasyonu (pytrends demo)...")
    from data_collectors.google_trends import GoogleTrendsCollector
    collector = GoogleTrendsCollector()
    print("   ✓ GoogleTrendsCollector hazır")

    print("\n2️⃣  Trendyol scraper hazırlık kontrolü...")
    from data_collectors.trendyol_scraper import TrendyolScraper
    scraper = TrendyolScraper()
    print("   ✓ TrendyolScraper hazır")

    print("\n3️⃣  TikTok trend verisi (fallback modu)...")
    from data_collectors.tiktok_scraper import TikTokTrendCollector, KIRTASIYE_HASHTAGS
    tt = TikTokTrendCollector()
    tt_results = tt.fetch_hashtag_trends(KIRTASIYE_HASHTAGS[:5])
    for r in sorted(tt_results, key=lambda x: x["trend_score"], reverse=True):
        print(f"   #{r['hashtag']:<20} skor: {r['trend_score']}")

    print("\n4️⃣  Trend Skoru Hesaplanıyor...")
    from trend_engine.scorer import TrendScorer, get_demo_signals
    scorer = TrendScorer()
    top5 = scorer.get_top_n(get_demo_signals(), n=5)

    print("\n" + "=" * 60)
    print("🏆 SONUÇ — Top 5 Kırtasiye Ürünü")
    print("=" * 60)
    for i, r in enumerate(top5, 1):
        print(f"\n{i}. {r.product_name}")
        print(f"   Composite: {r.composite_score:.1f}/100  {r.risk_emoji}  {r.risk_level.upper()}")
        print(f"   G:{r.google_score:.0f} | T:{r.trendyol_score:.0f} | TK:{r.tiktok_score:.0f}")
        print(f"   En İyi Kanal: {r.best_channel.upper()} ({r.channel_recommendations[r.best_channel]:.0f}/100)")
        print(f"   6 Hafta Tahmini: {' → '.join(f'{v:.0f}' for v in r.weekly_forecast)}")

    print("\n✅ Demo tamamlandı!\n")
    print("📊 Dashboard için: streamlit run dashboard/streamlit_app.py\n")


def main():
    parser = argparse.ArgumentParser(description="TradeTrend veri pipeline")
    parser.add_argument("--source", choices=["google", "trendyol", "tiktok", "all"], default="all")
    parser.add_argument("--demo", action="store_true", help="DB olmadan demo modu")
    parser.add_argument("--no-db", action="store_true", help="DB kaydetme")
    args = parser.parse_args()

    if args.demo:
        run_demo()
        return

    db_session = None
    if not args.no_db:
        try:
            from database import SessionLocal, init_db
            init_db()
            db_session = SessionLocal()
            logger.info("Veritabanı bağlantısı kuruldu.")
        except Exception as e:
            logger.warning(f"DB bağlantısı başarısız: {e}. --no-db modu kullanılıyor.")

    try:
        start = datetime.now()

        if args.source in ("google", "all"):
            run_google_trends(db_session)

        if args.source in ("trendyol", "all"):
            run_trendyol_scraper(db_session)

        if args.source in ("tiktok", "all"):
            run_tiktok_scraper(db_session)

        run_scorer(db_session)

        elapsed = (datetime.now() - start).total_seconds()
        logger.info(f"Pipeline tamamlandı: {elapsed:.1f}s")

    finally:
        if db_session:
            db_session.close()


if __name__ == "__main__":
    main()
