"""Add performance indexes to improve query speed

Run this migration with:
    python migrations/add_performance_indexes.py
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config.config import Config

def add_indexes():
    """Add database indexes for performance optimization"""
    config = Config()
    engine = create_engine(config.DATABASE_URL)
    
    indexes = [
        # Company indexes
        "CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies(ticker);",
        "CREATE INDEX IF NOT EXISTS idx_companies_sector ON companies(sector);",
        "CREATE INDEX IF NOT EXISTS idx_companies_market_cap ON companies(market_cap);",
        
        # Transcript indexes
        "CREATE INDEX IF NOT EXISTS idx_transcripts_company_id ON transcripts(company_id);",
        "CREATE INDEX IF NOT EXISTS idx_transcripts_fiscal_period ON transcripts(fiscal_year, fiscal_quarter);",
        "CREATE INDEX IF NOT EXISTS idx_transcripts_call_date ON transcripts(call_date);",
        "CREATE INDEX IF NOT EXISTS idx_transcripts_fmp_fetch_date ON transcripts(fmp_fetch_date);",
        
        # Sentiment analysis indexes
        "CREATE INDEX IF NOT EXISTS idx_sentiment_transcript_id ON sentiment_analysis(transcript_id);",
        "CREATE INDEX IF NOT EXISTS idx_sentiment_overall ON sentiment_analysis(overall_sentiment);",
        "CREATE INDEX IF NOT EXISTS idx_sentiment_confidence ON sentiment_analysis(management_confidence_score);",
        "CREATE INDEX IF NOT EXISTS idx_sentiment_analyzed_at ON sentiment_analysis(analyzed_at);",
        
        # Trend analysis indexes
        "CREATE INDEX IF NOT EXISTS idx_trends_company_id ON trend_analysis(company_id);",
        "CREATE INDEX IF NOT EXISTS idx_trends_category ON trend_analysis(trend_category);",
        "CREATE INDEX IF NOT EXISTS idx_trends_date ON trend_analysis(analysis_date);",
        "CREATE INDEX IF NOT EXISTS idx_trends_sentiment_change ON trend_analysis(sentiment_change);",
        
        # Alert indexes
        "CREATE INDEX IF NOT EXISTS idx_alerts_company_id ON alerts(company_id);",
        "CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(is_resolved);",
        "CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);",
        "CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at);",
        
        # Watchlist indexes
        "CREATE INDEX IF NOT EXISTS idx_watchlist_user_id ON watchlist(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_watchlist_company_id ON watchlist(company_id);",
        "CREATE INDEX IF NOT EXISTS idx_watchlist_user_company ON watchlist(user_id, company_id);",
        
        # API usage indexes
        "CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);",
        "CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage(timestamp);",
        
        # Monthly report indexes
        "CREATE INDEX IF NOT EXISTS idx_reports_month_year ON monthly_reports(month, year);",
        
        # Composite indexes for common queries
        "CREATE INDEX IF NOT EXISTS idx_transcripts_company_date ON transcripts(company_id, call_date DESC);",
        "CREATE INDEX IF NOT EXISTS idx_trends_company_date ON trend_analysis(company_id, analysis_date DESC);",
        "CREATE INDEX IF NOT EXISTS idx_alerts_unresolved_severity ON alerts(is_resolved, severity) WHERE is_resolved = FALSE;",
    ]
    
    print("Adding performance indexes...")
    
    with engine.connect() as conn:
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                conn.commit()
                print(f"✓ {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                print(f"✗ Failed to create index: {e}")
    
    print("\nAnalyzing tables for query optimization...")
    
    analyze_queries = [
        "ANALYZE companies;",
        "ANALYZE transcripts;",
        "ANALYZE sentiment_analysis;",
        "ANALYZE trend_analysis;",
        "ANALYZE alerts;",
        "ANALYZE watchlist;",
        "ANALYZE api_usage;",
        "ANALYZE monthly_reports;"
    ]
    
    with engine.connect() as conn:
        for query in analyze_queries:
            try:
                conn.execute(text(query))
                conn.commit()
                table_name = query.split()[1].rstrip(';')
                print(f"✓ Analyzed {table_name}")
            except Exception as e:
                print(f"✗ Failed to analyze: {e}")
    
    print("\nDatabase performance optimization complete!")
    
    # Display index usage statistics
    print("\nChecking index usage...")
    stats_query = """
    SELECT 
        schemaname,
        tablename,
        indexname,
        idx_scan as index_scans,
        idx_tup_read as tuples_read,
        idx_tup_fetch as tuples_fetched
    FROM 
        pg_stat_user_indexes
    WHERE 
        schemaname = 'public'
    ORDER BY 
        idx_scan DESC
    LIMIT 20;
    """
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(stats_query))
            rows = result.fetchall()
            
            if rows:
                print("\nTop used indexes:")
                print("-" * 80)
                print(f"{'Index Name':<40} {'Scans':<15} {'Tuples Read':<15}")
                print("-" * 80)
                for row in rows:
                    if row[3] > 0:  # Only show used indexes
                        print(f"{row[2]:<40} {row[3]:<15} {row[4]:<15}")
    except Exception as e:
        print(f"Could not retrieve index statistics: {e}")

if __name__ == "__main__":
    add_indexes() 