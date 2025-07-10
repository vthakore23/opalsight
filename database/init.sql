-- OpalSight Database Schema
-- This file initializes the database with the required tables and structure

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS opalsight;

-- Use the database
\c opalsight;

-- Create tables (basic structure - the Flask app will handle migrations)
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    market_cap BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transcripts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    quarter VARCHAR(10),
    year INTEGER,
    date DATE,
    content TEXT,
    url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sentiment_analysis (
    id SERIAL PRIMARY KEY,
    transcript_id INTEGER REFERENCES transcripts(id),
    overall_sentiment FLOAT,
    confidence_score FLOAT,
    positive_segments INTEGER DEFAULT 0,
    negative_segments INTEGER DEFAULT 0,
    neutral_segments INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_companies_symbol ON companies(symbol);
CREATE INDEX IF NOT EXISTS idx_transcripts_company_id ON transcripts(company_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_date ON transcripts(date);
CREATE INDEX IF NOT EXISTS idx_sentiment_transcript_id ON sentiment_analysis(transcript_id);

-- Insert some sample data
INSERT INTO companies (symbol, name, sector, market_cap) VALUES 
('MRNA', 'Moderna Inc.', 'Biotechnology', 50000000000),
('PFE', 'Pfizer Inc.', 'Biotechnology', 200000000000),
('JNJ', 'Johnson & Johnson', 'Healthcare', 400000000000)
ON CONFLICT (symbol) DO NOTHING;

