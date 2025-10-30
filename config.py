"""
Database Configuration for Competition Tracker
Environment variables and connection settings
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DatabaseConfig:
    """Database configuration management"""
    
    # MongoDB Atlas Configuration (your cluster)
    MONGODB_USERNAME: str = os.getenv("MONGODB_USERNAME", "myUser")
    MONGODB_PASSWORD: str = os.getenv("MONGODB_PASSWORD", "admin15")
    MONGODB_CLUSTER: str = os.getenv("MONGODB_CLUSTER", "competitiontrackerclust.o8dxgmq.mongodb.net")
    
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "competition_tracker")
    
    # Local MongoDB (fallback)
    MONGODB_URL: str = os.getenv("MONGODB_URL", "")
    
    # Collection names
    PRODUCTS_COLLECTION = "products"
    AMAZON_SCRAPING_DATA_COLLECTION = "amazon_scraping_data"
    SMARTPRIX_SCRAPING_DATA_COLLECTION = "smartprix_scraping_data"
    FLIPKART_SCRAPING_DATA_COLLECTION = "flipkart_scraping_data"
    FLIPKART_REVIEWS_COLLECTION = "flipkart_reviews"
    PRICE_HISTORY_COLLECTION = "price_history"
    COMPETITORS_COLLECTION = "competitors"
    SCRAPING_LOGS_COLLECTION = "scraping_logs"
    ANALYTICS_CACHE_COLLECTION = "analytics_cache"
    PRICE_ALERTS_COLLECTION = "price_alerts"
    
    # Performance Settings
    CONNECTION_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    CONNECTION_TIMEOUT: int = int(os.getenv("DB_TIMEOUT", "30"))
    
    # Data Retention Settings (in days)
    PRICE_HISTORY_RETENTION: int = int(os.getenv("PRICE_HISTORY_RETENTION", "365"))
    SCRAPING_LOGS_RETENTION: int = int(os.getenv("SCRAPING_LOGS_RETENTION", "30"))
    ANALYTICS_CACHE_RETENTION: int = int(os.getenv("ANALYTICS_CACHE_RETENTION", "1"))
    
    @classmethod
    def get_mongodb_url(cls) -> str:
        """Get properly formatted MongoDB connection URL"""
        if cls.MONGODB_USERNAME and cls.MONGODB_PASSWORD and cls.MONGODB_CLUSTER:
            # MongoDB Atlas connection (cloud database for team collaboration)
            from urllib.parse import quote_plus
            username = quote_plus(cls.MONGODB_USERNAME)
            password = quote_plus(cls.MONGODB_PASSWORD)
            return f"mongodb+srv://{username}:{password}@{cls.MONGODB_CLUSTER}/?retryWrites=true&w=majority&appName=CompetitionTracker"
        else:
            # Local MongoDB connection (single developer)
            return cls.MONGODB_URL or "mongodb://localhost:27017/"
    
    @classmethod
    def get_database_settings(cls) -> dict:
        """Get all database settings as dictionary"""
        return {
            "url": cls.get_mongodb_url(),
            "database": cls.DATABASE_NAME,
            "pool_size": cls.CONNECTION_POOL_SIZE,
            "timeout": cls.CONNECTION_TIMEOUT,
            "collections": {
                "products": cls.PRODUCTS_COLLECTION,
                "price_history": cls.PRICE_HISTORY_COLLECTION,
                "competitors": cls.COMPETITORS_COLLECTION,
                "scraping_logs": cls.SCRAPING_LOGS_COLLECTION,
                "analytics_cache": cls.ANALYTICS_CACHE_COLLECTION,
                "price_alerts": cls.PRICE_ALERTS_COLLECTION
            },
            "retention": {
                "price_history_days": cls.PRICE_HISTORY_RETENTION,
                "scraping_logs_days": cls.SCRAPING_LOGS_RETENTION,
                "analytics_cache_days": cls.ANALYTICS_CACHE_RETENTION
            }
        }


class ScrapingConfig:
    """Scraping configuration settings"""
    
    # Scraping intervals (in hours)
    AMAZON_SCRAPING_INTERVAL: int = int(os.getenv("AMAZON_SCRAPING_INTERVAL", "24"))
    SMARTPRIX_SCRAPING_INTERVAL: int = int(os.getenv("SMARTPRIX_SCRAPING_INTERVAL", "12"))
    
    # Concurrent scraping limits
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
    REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", "1.0"))
    
    # Retry settings
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "5"))
    
    # Data quality thresholds
    MIN_DATA_QUALITY_SCORE: float = float(os.getenv("MIN_DATA_QUALITY_SCORE", "0.7"))
    
    @classmethod
    def get_scraping_settings(cls) -> dict:
        """Get scraping configuration as dictionary"""
        return {
            "intervals": {
                "amazon_hours": cls.AMAZON_SCRAPING_INTERVAL,
                "smartprix_hours": cls.SMARTPRIX_SCRAPING_INTERVAL
            },
            "limits": {
                "max_concurrent": cls.MAX_CONCURRENT_REQUESTS,
                "request_delay": cls.REQUEST_DELAY
            },
            "retry": {
                "max_retries": cls.MAX_RETRIES,
                "retry_delay": cls.RETRY_DELAY
            },
            "quality": {
                "min_score": cls.MIN_DATA_QUALITY_SCORE
            }
        }


class AnalyticsConfig:
    """Analytics and alerting configuration"""
    
    # Price alert thresholds
    PRICE_CHANGE_ALERT_THRESHOLD: float = float(os.getenv("PRICE_ALERT_THRESHOLD", "10.0"))
    SIGNIFICANT_PRICE_DROP: float = float(os.getenv("SIGNIFICANT_PRICE_DROP", "15.0"))
    
    # Analytics refresh intervals (in hours)
    ANALYTICS_REFRESH_INTERVAL: int = int(os.getenv("ANALYTICS_REFRESH_INTERVAL", "6"))
    COMPETITOR_ANALYSIS_INTERVAL: int = int(os.getenv("COMPETITOR_ANALYSIS_INTERVAL", "12"))
    
    # Market analysis settings
    TOP_COMPETITORS_LIMIT: int = int(os.getenv("TOP_COMPETITORS_LIMIT", "20"))
    PRICE_TREND_DAYS: int = int(os.getenv("PRICE_TREND_DAYS", "30"))
    
    @classmethod
    def get_analytics_settings(cls) -> dict:
        """Get analytics configuration as dictionary"""
        return {
            "alerts": {
                "price_change_threshold": cls.PRICE_CHANGE_ALERT_THRESHOLD,
                "significant_drop": cls.SIGNIFICANT_PRICE_DROP
            },
            "refresh": {
                "analytics_hours": cls.ANALYTICS_REFRESH_INTERVAL,
                "competitor_analysis_hours": cls.COMPETITOR_ANALYSIS_INTERVAL
            },
            "analysis": {
                "top_competitors": cls.TOP_COMPETITORS_LIMIT,
                "trend_days": cls.PRICE_TREND_DAYS
            }
        }


# Export main configuration
config = DatabaseConfig()
scraping_config = ScrapingConfig()
analytics_config = AnalyticsConfig()