-- OpalSight Database Schema
-- Automated earnings call analysis platform

-- Companies table with FMP integration
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255),
    market_cap DECIMAL(20,2),
    sector VARCHAR(100),
    industry VARCHAR(100),
    exchange VARCHAR(20),
    fmp_has_transcripts BOOLEAN DEFAULT FALSE,
    transcript_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_companies_ticker ON companies(ticker);
CREATE INDEX idx_companies_market_cap ON companies(market_cap);

-- Transcripts with FMP data structure
CREATE TABLE IF NOT EXISTS transcripts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    call_date TIMESTAMP NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER NOT NULL,
    raw_text TEXT,
    cleaned_text TEXT,
    word_count INTEGER,
    fmp_fetch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, fiscal_year, fiscal_quarter)
);

CREATE INDEX idx_transcripts_company_date ON transcripts(company_id, call_date DESC);
CREATE INDEX idx_transcripts_fiscal ON transcripts(fiscal_year DESC, fiscal_quarter DESC);

-- Enhanced sentiment analysis
CREATE TABLE IF NOT EXISTS sentiment_analysis (
    id SERIAL PRIMARY KEY,
    transcript_id INTEGER REFERENCES transcripts(id) ON DELETE CASCADE,
    overall_sentiment FLOAT,
    management_confidence_score FLOAT,
    guidance_sentiment FLOAT,
    product_mentions JSONB,
    confidence_indicators JSONB,
    key_topics JSONB,
    sentiment_by_section JSONB,
    gpt_enhanced BOOLEAN DEFAULT FALSE,
    gpt_insights JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sentiment_transcript ON sentiment_analysis(transcript_id);
CREATE INDEX idx_sentiment_scores ON sentiment_analysis(overall_sentiment, management_confidence_score);

-- Historical comparisons
CREATE TABLE IF NOT EXISTS trend_analysis (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    analysis_date DATE NOT NULL,
    trend_category VARCHAR(20) CHECK (trend_category IN ('improving', 'stable', 'declining', 'insufficient_data')),
    sentiment_change FLOAT,
    confidence_change FLOAT,
    key_changes JSONB,
    notable_quotes JSONB,
    comparison_window INTEGER DEFAULT 4,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trend_company_date ON trend_analysis(company_id, analysis_date DESC);
CREATE INDEX idx_trend_category ON trend_analysis(trend_category);

-- Monthly reports
CREATE TABLE IF NOT EXISTS monthly_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL UNIQUE,
    companies_analyzed INTEGER,
    improving_count INTEGER,
    stable_count INTEGER,
    declining_count INTEGER,
    report_data JSONB,
    pdf_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API usage tracking
CREATE TABLE IF NOT EXISTS api_usage (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    endpoint VARCHAR(100),
    calls_made INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, endpoint)
);

CREATE INDEX idx_api_usage_date ON api_usage(date DESC);

-- User watchlists (for future features)
CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    alert_threshold FLOAT DEFAULT 0.2,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, company_id)
);

-- Alerts for significant changes
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    alert_type VARCHAR(50),
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high')),
    message TEXT,
    data JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_company ON alerts(company_id, created_at DESC);
CREATE INDEX idx_alerts_unresolved ON alerts(resolved) WHERE resolved = FALSE; 