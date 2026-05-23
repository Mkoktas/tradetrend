from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Decimal as SADecimal, DateTime,
    Date, BigInteger, ForeignKey, JSON, ARRAY, Text, CheckConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))
    keywords = Column(ARRAY(Text))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    google_trends = relationship("GoogleTrendsData", back_populates="product", cascade="all, delete")
    trendyol_data = relationship("TrendyolData", back_populates="product", cascade="all, delete")
    tiktok_data = relationship("TikTokTrendsData", back_populates="product", cascade="all, delete")
    trend_scores = relationship("TrendScore", back_populates="product", cascade="all, delete")
    forecasts = relationship("WeeklyForecast", back_populates="product", cascade="all, delete")


class GoogleTrendsData(Base):
    __tablename__ = "google_trends_data"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    keyword = Column(String(255), nullable=False)
    trend_score = Column(Integer, nullable=False)
    week_start = Column(Date, nullable=False)
    region = Column(String(50), default="TR")
    collected_at = Column(DateTime, default=datetime.now)

    product = relationship("Product", back_populates="google_trends")


class TrendyolData(Base):
    __tablename__ = "trendyol_data"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    product_name = Column(String(500), nullable=False)
    price = Column(SADecimal(10, 2))
    rating = Column(SADecimal(3, 2))
    review_count = Column(Integer, default=0)
    sales_rank = Column(Integer)
    category_url = Column(String(500))
    product_url = Column(String(500))
    collected_at = Column(DateTime, default=datetime.now)

    product = relationship("Product", back_populates="trendyol_data")


class TikTokTrendsData(Base):
    __tablename__ = "tiktok_trends_data"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    hashtag = Column(String(255), nullable=False)
    post_count = Column(BigInteger, default=0)
    trend_score = Column(Integer, default=0)
    week_start = Column(Date, nullable=False)
    collected_at = Column(DateTime, default=datetime.now)

    product = relationship("Product", back_populates="tiktok_data")


class TrendScore(Base):
    __tablename__ = "trend_scores"
    __table_args__ = (
        CheckConstraint("risk_level IN ('low', 'medium', 'high')", name="ck_risk_level"),
    )

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    google_score = Column(SADecimal(5, 2), default=0)
    trendyol_score = Column(SADecimal(5, 2), default=0)
    tiktok_score = Column(SADecimal(5, 2), default=0)
    composite_score = Column(SADecimal(5, 2), nullable=False)
    risk_level = Column(String(20), nullable=False)
    channel_recommendation = Column(JSON)
    week_start = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    product = relationship("Product", back_populates="trend_scores")


class WeeklyForecast(Base):
    __tablename__ = "weekly_forecasts"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    forecast_week = Column(Date, nullable=False)
    predicted_demand_index = Column(SADecimal(5, 2))
    confidence_level = Column(SADecimal(3, 2))
    created_at = Column(DateTime, default=datetime.now)

    product = relationship("Product", back_populates="forecasts")
