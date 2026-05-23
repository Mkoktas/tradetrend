"""
Trendyol web scraping modülü.
BeautifulSoup + requests ile çok satanlar verisi çeker.
Rate limiting: 1 istek/saniye (ToS uyumu için).
"""

import time
import logging
import random
from datetime import datetime
from typing import Optional
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.trendyol.com"

# Kırtasiye kategorisi URL'leri
CATEGORY_URLS = {
    "kirtasiye": "/kirtasiye-x-c103498",
    "kalemler": "/kalemler-x-c106498",
    "defterler": "/defter-bloknot-x-c106499",
    "okul_cantasi": "/okul-cantasi-x-c106472",
    "masaustu_aksesuarlari": "/masa-ustu-aksesuarlari-x-c106500",
}

BESTSELLERS_PATH = "/cok-satanlar"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


class TrendyolScraper:
    def __init__(self, rate_limit_seconds: float = 1.5):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.rate_limit = rate_limit_seconds
        self._last_request_time = 0

    def _wait_rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            sleep_time = self.rate_limit - elapsed + random.uniform(0.1, 0.5)
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        self._wait_rate_limit()
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.warning("Trendyol 403: Rate limit veya bot koruması. Bekleniyor...")
                time.sleep(10)
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise

    def scrape_bestsellers(self, category: str = "kirtasiye", max_pages: int = 3) -> list[dict]:
        """
        Trendyol çok satanlar sayfasından ürün verisi toplar.
        Returns: List of product dicts
        """
        category_path = CATEGORY_URLS.get(category, CATEGORY_URLS["kirtasiye"])
        url = f"{BASE_URL}{category_path}{BESTSELLERS_PATH}"

        all_products = []

        for page in range(1, max_pages + 1):
            page_url = f"{url}?pi={page}"
            logger.info(f"Scraping page {page}: {page_url}")

            soup = self._get_page(page_url)
            if not soup:
                break

            products = self._parse_product_cards(soup, category_path)
            if not products:
                logger.info(f"Sayfa {page}'de ürün bulunamadı, durduruluyor.")
                break

            # Rank hesapla (sayfa başına 24 ürün varsayımıyla)
            start_rank = (page - 1) * 24 + 1
            for i, product in enumerate(products):
                product["sales_rank"] = start_rank + i

            all_products.extend(products)
            logger.info(f"Sayfa {page}: {len(products)} ürün toplandı.")

        logger.info(f"Toplam {len(all_products)} ürün toplandı.")
        return all_products

    def _parse_product_cards(self, soup: BeautifulSoup, category_url: str) -> list[dict]:
        """Ürün kartlarını parse eder."""
        products = []

        # Trendyol'un mevcut HTML yapısına göre selectors
        product_cards = soup.select("div.p-card-wrppr") or soup.select("div[data-id]")

        if not product_cards:
            # Alternatif selector dene
            product_cards = soup.select(".product-card") or soup.select("[class*='ProductCard']")

        for card in product_cards:
            try:
                product = self._extract_product_data(card, category_url)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Ürün parse hatası: {e}")
                continue

        return products

    def _extract_product_data(self, card: BeautifulSoup, category_url: str) -> Optional[dict]:
        """Tek bir ürün kartından veri çıkarır."""
        # Ürün adı
        name_el = (
            card.select_one(".product-description-name")
            or card.select_one("[class*='ProductName']")
            or card.select_one(".name")
        )
        if not name_el:
            return None
        name = name_el.get_text(strip=True)

        # Fiyat
        price = None
        price_el = (
            card.select_one(".prc-box-dscntd")
            or card.select_one(".prc-box-sllng")
            or card.select_one("[class*='Price']")
        )
        if price_el:
            price_text = price_el.get_text(strip=True)
            price = self._parse_price(price_text)

        # Puan
        rating = None
        rating_el = card.select_one(".rating") or card.select_one("[class*='Rating']")
        if rating_el:
            try:
                rating = float(rating_el.get_text(strip=True).replace(",", "."))
            except (ValueError, AttributeError):
                pass

        # Yorum sayısı
        review_count = 0
        review_el = card.select_one(".review-count") or card.select_one("[class*='ReviewCount']")
        if review_el:
            try:
                review_text = review_el.get_text(strip=True).replace("(", "").replace(")", "")
                review_count = int(review_text.replace(".", "").replace(",", ""))
            except (ValueError, AttributeError):
                pass

        # Ürün URL
        product_url = None
        link_el = card.select_one("a[href]")
        if link_el:
            href = link_el.get("href", "")
            product_url = f"{BASE_URL}{href}" if href.startswith("/") else href

        return {
            "product_name": name,
            "price": price,
            "rating": rating,
            "review_count": review_count,
            "product_url": product_url,
            "category_url": category_url,
            "collected_at": datetime.now(),
        }

    @staticmethod
    def _parse_price(price_text: str) -> Optional[float]:
        """'1.299,99 TL' formatındaki fiyatı float'a çevirir."""
        try:
            cleaned = price_text.replace("TL", "").replace("₺", "").strip()
            cleaned = cleaned.replace(".", "").replace(",", ".")
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def get_category_sales_growth(self, products_now: list[dict], products_prev: list[dict]) -> dict[str, float]:
        """
        İki farklı zamandaki ürün listelerini karşılaştırarak sıralama değişimini hesaplar.
        Rank iyileşmesi = pozitif büyüme.
        """
        prev_ranks = {p["product_name"]: p.get("sales_rank", 999) for p in products_prev}
        growth = {}

        for product in products_now:
            name = product["product_name"]
            current_rank = product.get("sales_rank", 999)
            prev_rank = prev_ranks.get(name, 999)

            if prev_rank > 0:
                rank_improvement = prev_rank - current_rank
                growth_pct = (rank_improvement / prev_rank) * 100
                growth[name] = round(growth_pct, 2)

        return growth


def collect_and_save(category: str = "kirtasiye", db_session=None) -> list[dict]:
    """Pipeline entry point."""
    scraper = TrendyolScraper()
    products = scraper.scrape_bestsellers(category=category, max_pages=3)

    if db_session:
        _save_to_db(products, category, db_session)

    return products


def _save_to_db(products: list[dict], category: str, session) -> None:
    from database.models import Product, TrendyolData

    for item in products:
        product = session.query(Product).filter_by(name=item["product_name"], category=category).first()
        if not product:
            product = Product(
                name=item["product_name"],
                category=category,
                keywords=[item["product_name"].lower()],
            )
            session.add(product)
            session.flush()

        session.add(
            TrendyolData(
                product_id=product.id,
                product_name=item["product_name"],
                price=item.get("price"),
                rating=item.get("rating"),
                review_count=item.get("review_count", 0),
                sales_rank=item.get("sales_rank"),
                category_url=item.get("category_url"),
                product_url=item.get("product_url"),
            )
        )

    session.commit()
    logger.info(f"{len(products)} Trendyol ürünü veritabanına kaydedildi.")


if __name__ == "__main__":
    print("Trendyol kırtasiye çok satanlar scraping başlıyor...\n")
    scraper = TrendyolScraper()
    products = scraper.scrape_bestsellers(category="kirtasiye", max_pages=1)

    print(f"\nToplam {len(products)} ürün bulundu:\n")
    for i, p in enumerate(products[:10], 1):
        print(f"{i:2}. {p['product_name'][:50]:<50} | {p.get('price') or 'N/A':>10} TL | "
              f"★{p.get('rating') or '-'} | {p.get('review_count', 0)} yorum")
