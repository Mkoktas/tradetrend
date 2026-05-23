-- TradeTrend MVP Database Schema

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    keywords TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS google_trends_data (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    keyword VARCHAR(255) NOT NULL,
    trend_score INTEGER NOT NULL,        -- 0-100, Google Trends value
    week_start DATE NOT NULL,
    region VARCHAR(50) DEFAULT 'TR',
    collected_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trendyol_data (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    product_name VARCHAR(500) NOT NULL,
    price DECIMAL(10, 2),
    rating DECIMAL(3, 2),
    review_count INTEGER DEFAULT 0,
    sales_rank INTEGER,                  -- Position in bestsellers list
    category_url VARCHAR(500),
    product_url VARCHAR(500),
    collected_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tiktok_trends_data (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    hashtag VARCHAR(255) NOT NULL,
    post_count BIGINT DEFAULT 0,
    trend_score INTEGER DEFAULT 0,       -- 0-100 normalized
    week_start DATE NOT NULL,
    collected_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trend_scores (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    google_score DECIMAL(5, 2) DEFAULT 0,
    trendyol_score DECIMAL(5, 2) DEFAULT 0,
    tiktok_score DECIMAL(5, 2) DEFAULT 0,
    composite_score DECIMAL(5, 2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
    channel_recommendation JSONB,        -- {"trendyol": 85, "instagram": 70, "store": 60}
    week_start DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS weekly_forecasts (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    forecast_week DATE NOT NULL,
    predicted_demand_index DECIMAL(5, 2),
    confidence_level DECIMAL(3, 2),      -- 0.0 to 1.0
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_google_trends_product_week
    ON google_trends_data(product_id, week_start);
CREATE INDEX IF NOT EXISTS idx_trendyol_product_date
    ON trendyol_data(product_id, collected_at);
CREATE INDEX IF NOT EXISTS idx_trend_scores_week
    ON trend_scores(week_start, composite_score DESC);
CREATE INDEX IF NOT EXISTS idx_products_category
    ON products(category);
