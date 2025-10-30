"""
MongoDB Database Manager for Competition Tracker
Designed for real-time competitor intelligence and pricing analytics
"""

import motor.motor_asyncio
import pymongo
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import json
import logging
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompetitionTrackerDB:
    """
    MongoDB Database Manager for Competition Tracker
    Handles products, pricing history, competitor analysis, and analytics
    """
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", 
                 database_name: str = "competition_tracker"):
        """Initialize database connection and collections"""
        self.client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
        self.db = self.client[database_name]
        
        # Define collections
        self.products = self.db.products
        self.price_history = self.db.price_history
        self.competitors = self.db.competitors
        self.scraping_logs = self.db.scraping_logs
        self.analytics_cache = self.db.analytics_cache
        self.price_alerts = self.db.price_alerts
        
        logger.info(f"Connected to MongoDB database: {database_name}")

    async def setup_database(self):
        """Create indexes and initial setup for optimal performance"""
        try:
            # Products collection indexes
            await self.products.create_index("product_id", unique=True)
            await self.products.create_index("asin", sparse=True)  # Amazon ASIN
            await self.products.create_index("smartprix_id", sparse=True)
            await self.products.create_index([("brand", 1), ("category", 1)])
            await self.products.create_index("metadata.status")
            await self.products.create_index("metadata.last_updated")
            
            # Price history indexes
            await self.price_history.create_index([
                ("product_id", 1), 
                ("platform", 1), 
                ("timestamp", -1)
            ])
            await self.price_history.create_index("timestamp")
            
            # Competitors collection
            await self.competitors.create_index("platform", unique=True)
            
            # Scraping logs with TTL (expire after 30 days)
            await self.scraping_logs.create_index(
                "timestamp", 
                expireAfterSeconds=30*24*60*60
            )
            
            # Analytics cache with TTL (expire after 1 day)
            await self.analytics_cache.create_index(
                "created_at", 
                expireAfterSeconds=24*60*60
            )
            
            logger.info("✅ Database indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            return False

    async def store_amazon_product(self, product_data: Dict) -> str:
        """
        Store Amazon product data from scraper results
        
        Args:
            product_data: Dictionary containing Amazon product information
            
        Returns:
            product_id: MongoDB ObjectId as string
        """
        try:
            # Extract ASIN from link
            asin = self._extract_asin(product_data.get('link', ''))
            
            # Parse price
            price_whole = product_data.get('price_whole', '0').replace(',', '')
            price_fraction = product_data.get('price_fraction', '00')
            current_price = float(f"{price_whole}.{price_fraction}") if price_whole != '0' else 0.0
            
            # Parse original price
            original_price_str = product_data.get('list_price', '₹0').replace('₹', '').replace(',', '')
            original_price = float(original_price_str) if original_price_str != '0' else current_price
            
            # Parse rating and reviews
            rating_text = product_data.get('rating', '0 out of 5 stars')
            rating = float(rating_text.split()[0]) if 'out of' in rating_text else 0.0
            
            reviews_text = product_data.get('reviews', '0').replace(',', '')
            reviews_count = int(reviews_text) if reviews_text.isdigit() else 0
            
            # Create product document
            product_doc = {
                "product_id": str(ObjectId()),
                "asin": asin,
                "name": product_data.get('title', '').strip(),
                "brand": self._extract_brand(product_data.get('title', '')),
                "category": "electronics",  # Default category, can be enhanced
                "platforms": {
                    "amazon": {
                        "current_price": current_price,
                        "original_price": original_price,
                        "currency": "INR",
                        "rating": rating,
                        "reviews_count": reviews_count,
                        "url": f"https://www.amazon.in{product_data.get('link', '')}",
                        "last_updated": datetime.utcnow(),
                        "availability": "in_stock"
                    }
                },
                "pricing_analytics": {
                    "discount_percentage": round(((original_price - current_price) / original_price * 100), 2) if original_price > 0 else 0,
                    "price_competitiveness": "unknown",
                    "last_price_change": None
                },
                "metadata": {
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "status": "active",
                    "scraping_frequency": "daily",
                    "data_quality_score": self._calculate_data_quality(product_data)
                }
            }
            
            # Upsert product (update if ASIN exists, insert if new)
            result = await self.products.update_one(
                {"asin": asin} if asin else {"name": product_doc["name"]},
                {"$set": product_doc},
                upsert=True
            )
            
            product_id = str(result.upserted_id) if result.upserted_id else product_doc["product_id"]
            
            # Store price history
            await self._store_price_point(product_id, "amazon", current_price, original_price)
            
            logger.info(f"✅ Amazon product stored: {product_doc['name'][:50]}...")
            return product_id
            
        except Exception as e:
            logger.error(f"❌ Error storing Amazon product: {e}")
            return None

    async def store_smartprix_product(self, scraper_result: Dict) -> str:
        """
        Store Smartprix product data from scraper results
        
        Args:
            scraper_result: Complete result from SmartprixScraper
            
        Returns:
            product_id: MongoDB ObjectId as string
        """
        try:
            if not scraper_result.get("success"):
                logger.warning("❌ Smartprix scraper result indicates failure")
                return None
            
            product_info = scraper_result["product_info"]
            price_history = scraper_result["price_history"]
            
            # Create product document
            product_doc = {
                "product_id": str(ObjectId()),
                "smartprix_id": product_info["product_ids"][0] if product_info["product_ids"] else None,
                "price_pid": product_info["price_pids"][0] if product_info["price_pids"] else None,
                "name": product_info["name"],
                "brand": product_info["brand"],
                "category": self._extract_category_from_name(product_info["name"]),
                "platforms": {
                    "smartprix": {
                        "current_price": product_info["current_price"],
                        "currency": "INR",
                        "url": scraper_result["url"],
                        "last_updated": datetime.utcnow(),
                        "availability": "in_stock"
                    }
                },
                "pricing_analytics": {
                    "price_trends": {},
                    "volatility_scores": {},
                    "best_time_to_buy": None
                },
                "metadata": {
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "status": "active",
                    "scraping_frequency": "daily",
                    "data_quality_score": 0.95  # Smartprix generally has high quality data
                }
            }
            
            # Add price history analytics
            for time_range, data in price_history.items():
                if data["data_points"] > 0:
                    product_doc["pricing_analytics"]["price_trends"][time_range] = {
                        "trend": data["price_trend"],
                        "trend_percentage": data["trend_percentage"],
                        "min_price": data["min_price"],
                        "max_price": data["max_price"],
                        "average_price": data["average_price"],
                        "volatility": data["price_volatility"]
                    }
            
            # Store product
            result = await self.products.update_one(
                {"smartprix_id": product_doc["smartprix_id"]} if product_doc["smartprix_id"] else {"name": product_doc["name"]},
                {"$set": product_doc},
                upsert=True
            )
            
            product_id = str(result.upserted_id) if result.upserted_id else product_doc["product_id"]
            
            # Store detailed price history
            await self._store_smartprix_price_history(product_id, price_history)
            
            logger.info(f"✅ Smartprix product stored: {product_doc['name'][:50]}...")
            return product_id
            
        except Exception as e:
            logger.error(f"❌ Error storing Smartprix product: {e}")
            return None

    async def get_competitor_analysis(self, product_name: str = None, 
                                   category: str = None, 
                                   limit: int = 10) -> Dict:
        """
        Get comprehensive competitor analysis
        
        Args:
            product_name: Optional product name filter
            category: Optional category filter  
            limit: Maximum number of products to analyze
            
        Returns:
            Dictionary with competitor analysis results
        """
        try:
            # Build match criteria
            match_criteria = {"metadata.status": "active"}
            if product_name:
                match_criteria["name"] = {"$regex": product_name, "$options": "i"}
            if category:
                match_criteria["category"] = category
            
            # Aggregation pipeline for competitor analysis
            pipeline = [
                {"$match": match_criteria},
                {"$limit": limit},
                {
                    "$project": {
                        "name": 1,
                        "brand": 1,
                        "category": 1,
                        "amazon_price": "$platforms.amazon.current_price",
                        "smartprix_price": "$platforms.smartprix.current_price",
                        "amazon_rating": "$platforms.amazon.rating",
                        "amazon_reviews": "$platforms.amazon.reviews_count",
                        "pricing_analytics": 1,
                        "last_updated": "$metadata.updated_at"
                    }
                },
                {
                    "$addFields": {
                        "price_comparison": {
                            "$cond": {
                                "if": {"$and": [
                                    {"$ne": ["$amazon_price", None]},
                                    {"$ne": ["$smartprix_price", None]}
                                ]},
                                "then": {
                                    "$subtract": ["$amazon_price", "$smartprix_price"]
                                },
                                "else": None
                            }
                        },
                        "cheapest_platform": {
                            "$cond": {
                                "if": {"$and": [
                                    {"$ne": ["$amazon_price", None]},
                                    {"$ne": ["$smartprix_price", None]}
                                ]},
                                "then": {
                                    "$cond": {
                                        "if": {"$lt": ["$amazon_price", "$smartprix_price"]},
                                        "then": "amazon",
                                        "else": "smartprix"
                                    }
                                },
                                "else": {
                                    "$cond": {
                                        "if": {"$ne": ["$amazon_price", None]},
                                        "then": "amazon",
                                        "else": "smartprix"
                                    }
                                }
                            }
                        }
                    }
                },
                {"$sort": {"price_comparison": 1}}
            ]
            
            results = await self.products.aggregate(pipeline).to_list(limit)
            
            # Calculate summary statistics
            summary = await self._calculate_market_summary(results)
            
            return {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "total_products": len(results),
                "market_summary": summary,
                "products": results
            }
            
        except Exception as e:
            logger.error(f"❌ Error in competitor analysis: {e}")
            return {"error": str(e)}

    async def get_price_alerts(self, threshold_percentage: float = 10.0) -> List[Dict]:
        """
        Get products with significant price changes for alerts
        
        Args:
            threshold_percentage: Minimum price change percentage for alert
            
        Returns:
            List of products with significant price changes
        """
        try:
            # Get recent price history (last 7 days)
            since_date = datetime.utcnow() - timedelta(days=7)
            
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": since_date}
                    }
                },
                {
                    "$sort": {"timestamp": -1}
                },
                {
                    "$group": {
                        "_id": "$product_id",
                        "latest_price": {"$first": "$price"},
                        "earliest_price": {"$last": "$price"},
                        "price_changes": {"$push": "$price"}
                    }
                },
                {
                    "$addFields": {
                        "price_change_percentage": {
                            "$multiply": [
                                {"$divide": [
                                    {"$subtract": ["$latest_price", "$earliest_price"]},
                                    "$earliest_price"
                                ]},
                                100
                            ]
                        }
                    }
                },
                {
                    "$match": {
                        "price_change_percentage": {
                            "$gte": threshold_percentage
                        }
                    }
                },
                {
                    "$lookup": {
                        "from": "products",
                        "localField": "_id",
                        "foreignField": "product_id",
                        "as": "product_info"
                    }
                }
            ]
            
            alerts = await self.price_history.aggregate(pipeline).to_list(100)
            
            # Store alerts in alerts collection
            for alert in alerts:
                alert_doc = {
                    "product_id": alert["_id"],
                    "product_name": alert["product_info"][0]["name"] if alert["product_info"] else "Unknown",
                    "price_change_percentage": alert["price_change_percentage"],
                    "old_price": alert["earliest_price"],
                    "new_price": alert["latest_price"],
                    "alert_type": "price_increase" if alert["price_change_percentage"] > 0 else "price_decrease",
                    "created_at": datetime.utcnow(),
                    "status": "new"
                }
                
                await self.price_alerts.update_one(
                    {"product_id": alert["_id"], "status": "new"},
                    {"$set": alert_doc},
                    upsert=True
                )
            
            logger.info(f"✅ Generated {len(alerts)} price alerts")
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error generating price alerts: {e}")
            return []

    async def log_scraping_activity(self, platform: str, status: str, 
                                  products_scraped: int = 0, errors: List[str] = None) -> bool:
        """Log scraping activity for monitoring and debugging"""
        try:
            log_doc = {
                "platform": platform,
                "timestamp": datetime.utcnow(),
                "status": status,  # "success", "partial", "failed"
                "products_scraped": products_scraped,
                "errors": errors or [],
                "session_id": str(ObjectId())
            }
            
            await self.scraping_logs.insert_one(log_doc)
            return True
            
        except Exception as e:
            logger.error(f"❌ Error logging scraping activity: {e}")
            return False

    # Helper methods
    async def _store_price_point(self, product_id: str, platform: str, 
                               current_price: float, original_price: float = None):
        """Store individual price point in price history"""
        try:
            price_doc = {
                "product_id": product_id,
                "platform": platform,
                "price": current_price,
                "original_price": original_price,
                "currency": "INR",
                "timestamp": datetime.utcnow()
            }
            
            await self.price_history.insert_one(price_doc)
            
        except Exception as e:
            logger.error(f"❌ Error storing price point: {e}")

    async def _store_smartprix_price_history(self, product_id: str, price_history: Dict):
        """Store comprehensive Smartprix price history"""
        try:
            for time_range, data in price_history.items():
                if data["data_points"] > 0 and "raw_data" in data:
                    # Store each price point
                    for price_point in data["raw_data"]:
                        price_doc = {
                            "product_id": product_id,
                            "platform": "smartprix",
                            "price": price_point["price"],
                            "currency": "INR",
                            "timestamp": price_point["date"],
                            "time_range": time_range
                        }
                        
                        await self.price_history.update_one(
                            {
                                "product_id": product_id,
                                "timestamp": price_point["date"],
                                "platform": "smartprix"
                            },
                            {"$set": price_doc},
                            upsert=True
                        )
            
        except Exception as e:
            logger.error(f"❌ Error storing Smartprix price history: {e}")

    async def _calculate_market_summary(self, products: List[Dict]) -> Dict:
        """Calculate market summary statistics"""
        try:
            amazon_prices = [p["amazon_price"] for p in products if p.get("amazon_price")]
            smartprix_prices = [p["smartprix_price"] for p in products if p.get("smartprix_price")]
            
            return {
                "total_products_compared": len(products),
                "amazon_average_price": sum(amazon_prices) / len(amazon_prices) if amazon_prices else 0,
                "smartprix_average_price": sum(smartprix_prices) / len(smartprix_prices) if smartprix_prices else 0,
                "products_cheaper_on_amazon": len([p for p in products if p.get("cheapest_platform") == "amazon"]),
                "products_cheaper_on_smartprix": len([p for p in products if p.get("cheapest_platform") == "smartprix"]),
                "average_price_difference": sum([abs(p.get("price_comparison", 0)) for p in products]) / len(products) if products else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating market summary: {e}")
            return {}

    def _extract_asin(self, amazon_url: str) -> str:
        """Extract ASIN from Amazon URL"""
        import re
        match = re.search(r'/dp/([A-Z0-9]{10})', amazon_url)
        return match.group(1) if match else None

    def _extract_brand(self, product_name: str) -> str:
        """Extract brand from product name"""
        # Simple brand extraction - can be enhanced with ML
        common_brands = ['Apple', 'Samsung', 'OnePlus', 'Xiaomi', 'iPhone', 'MacBook', 'Dell', 'HP', 'Lenovo']
        for brand in common_brands:
            if brand.lower() in product_name.lower():
                return brand
        return "Unknown"

    def _extract_category_from_name(self, product_name: str) -> str:
        """Extract category from product name"""
        categories = {
            'mobile': ['mobile', 'phone', 'smartphone'],
            'laptop': ['laptop', 'macbook', 'notebook'],
            'tablet': ['tablet', 'ipad'],
            'headphones': ['headphones', 'earphones', 'earbuds'],
            'watch': ['watch', 'smartwatch']
        }
        
        name_lower = product_name.lower()
        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        return "electronics"

    def _calculate_data_quality(self, product_data: Dict) -> float:
        """Calculate data quality score (0-1)"""
        score = 0.0
        checks = [
            product_data.get('title'),
            product_data.get('price_whole'),
            product_data.get('link'),
            product_data.get('rating'),
        ]
        
        score = sum(1 for check in checks if check) / len(checks)
        return round(score, 2)

    async def close(self):
        """Close database connection"""
        self.client.close()
        logger.info("Database connection closed")


# Example usage and migration script
async def migrate_existing_data():
    """Migrate existing JSON data to MongoDB"""
    db = CompetitionTrackerDB()
    await db.setup_database()
    
    try:
        # Load existing JSON data
        with open('competitor_intelligence_db.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        logger.info(f"Migrating {len(existing_data)} products to MongoDB...")
        
        for product in existing_data:
            await db.store_amazon_product(product)
        
        logger.info("✅ Migration completed successfully")
        
    except FileNotFoundError:
        logger.info("No existing JSON file found, starting with fresh database")
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
    
    await db.close()


if __name__ == "__main__":
    # Run migration
    asyncio.run(migrate_existing_data())