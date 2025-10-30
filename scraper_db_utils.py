"""
Database utilities for scrapers
Shared MongoDB connection and storage functions for all scrapers
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging
from bson import ObjectId
import motor.motor_asyncio
from config import DatabaseConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperDatabaseManager:
    """Shared database manager for all scrapers"""
    
    def __init__(self):
        """Initialize database connection"""
        self.connection_string = DatabaseConfig.get_mongodb_url()
        self.database_name = DatabaseConfig.DATABASE_NAME
        self.client = None
        self.db = None
        
    async def connect(self):
        """Establish database connection"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.connection_string,
                maxPoolSize=DatabaseConfig.CONNECTION_POOL_SIZE,
                serverSelectionTimeoutMS=DatabaseConfig.CONNECTION_TIMEOUT * 1000
            )
            self.db = self.client[self.database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB: {self.database_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def store_amazon_scraping_data(self, scraped_data: List[Dict], search_query: str) -> bool:
        """
        Store Amazon scraping results in database
        
        Args:
            scraped_data: List of scraped product data from Amazon
            search_query: The search query used for scraping
            
        Returns:
            bool: Success status
        """
        try:
            if not scraped_data:
                logger.warning("No Amazon data to store")
                return False
                
            collection = self.db[DatabaseConfig.AMAZON_SCRAPING_DATA_COLLECTION]
            stored_count = 0
            
            for item in scraped_data:
                # Extract ASIN from product link
                asin = self._extract_asin_from_url(item.get('product_link', ''))
                
                # Parse price information
                price_info = self._parse_amazon_price(item.get('selling_price', '0'))
                original_price_info = self._parse_amazon_price(item.get('original_price_mrp', '0'))
                
                # Parse rating and reviews
                rating_info = self._parse_amazon_rating(item.get('star_rating', ''))
                reviews_count = self._parse_amazon_reviews(item.get('review_count', '0'))
                
                # Create product document
                product_doc = {
                    "asin": asin,
                    "search_query": search_query,
                    "product_title": item.get('product_title', '').strip(),
                    "brand": self._extract_brand_from_title(item.get('product_title', '')),
                    "selling_price": price_info['value'],
                    "selling_price_currency": price_info['currency'],
                    "original_price_mrp": original_price_info['value'],
                    "discount_percentage": self._calculate_discount_percentage(
                        price_info['value'], original_price_info['value']
                    ),
                    "star_rating": rating_info['rating'],
                    "rating_out_of": rating_info['max_rating'],
                    "review_count": reviews_count,
                    "product_link": item.get('product_link', ''),
                    "platform": "amazon",
                    "scraped_at": datetime.utcnow(),
                    "last_updated": datetime.utcnow(),
                    "data_quality_score": self._calculate_data_quality_score(item),
                    "status": "active"
                }
                
                # Upsert product (update if ASIN exists, insert if new)
                filter_criteria = {"asin": asin} if asin else {
                    "product_title": product_doc["product_title"],
                    "platform": "amazon"
                }
                
                result = await collection.update_one(
                    filter_criteria,
                    {
                        "$set": product_doc,
                        "$setOnInsert": {
                            "created_at": datetime.utcnow(),
                            "product_id": str(ObjectId())
                        }
                    },
                    upsert=True
                )
                
                if result.upserted_id or result.modified_count > 0:
                    stored_count += 1
                    
                # Store in price history if we have price data
                if price_info['value'] > 0:
                    await self._store_price_history(
                        asin or product_doc["product_title"],
                        "amazon",
                        price_info['value'],
                        original_price_info['value']
                    )
            
            logger.info(f"✅ Amazon: Stored {stored_count}/{len(scraped_data)} products")
            
            # Log scraping activity
            await self._log_scraping_activity(
                "amazon", 
                "success" if stored_count > 0 else "no_data",
                stored_count,
                search_query
            )
            
            return stored_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error storing Amazon data: {e}")
            await self._log_scraping_activity("amazon", "failed", 0, search_query, [str(e)])
            return False

    async def store_smartprix_scraping_data(self, scraped_data: List[Dict], search_query: str) -> bool:
        """
        Store Smartprix scraping results in database
        
        Args:
            scraped_data: List of scraped product data from Smartprix
            search_query: The search query used for scraping
            
        Returns:
            bool: Success status
        """
        try:
            if not scraped_data:
                logger.warning("No Smartprix data to store")
                return False
                
            collection = self.db[DatabaseConfig.SMARTPRIX_SCRAPING_DATA_COLLECTION]
            stored_count = 0
            
            for item in scraped_data:
                # Extract product ID from link
                product_id = self._extract_smartprix_id_from_url(item.get('product_link', ''))
                
                # Parse price information
                price_info = self._parse_smartprix_price(item.get('price', '₹0'))
                
                # Parse user score
                user_score = self._parse_smartprix_score(item.get('user_score', '0'))
                
                # Create product document
                product_doc = {
                    "smartprix_id": product_id,
                    "search_query": search_query,
                    "product_title": item.get('product_title', '').strip(),
                    "brand": self._extract_brand_from_title(item.get('product_title', '')),
                    "price": price_info['value'],
                    "price_currency": price_info['currency'],
                    "user_score": user_score,
                    "key_specs": item.get('key_specs', []),
                    "product_link": item.get('product_link', ''),
                    "platform": "smartprix",
                    "scraped_at": datetime.utcnow(),
                    "last_updated": datetime.utcnow(),
                    "data_quality_score": self._calculate_data_quality_score(item),
                    "status": "active"
                }
                
                # Upsert product
                filter_criteria = {"smartprix_id": product_id} if product_id else {
                    "product_title": product_doc["product_title"],
                    "platform": "smartprix"
                }
                
                result = await collection.update_one(
                    filter_criteria,
                    {
                        "$set": product_doc,
                        "$setOnInsert": {
                            "created_at": datetime.utcnow(),
                            "product_id": str(ObjectId())
                        }
                    },
                    upsert=True
                )
                
                if result.upserted_id or result.modified_count > 0:
                    stored_count += 1
                    
                # Store in price history
                if price_info['value'] > 0:
                    await self._store_price_history(
                        product_id or product_doc["product_title"],
                        "smartprix",
                        price_info['value']
                    )
            
            logger.info(f"✅ Smartprix: Stored {stored_count}/{len(scraped_data)} products")
            
            # Log scraping activity
            await self._log_scraping_activity(
                "smartprix", 
                "success" if stored_count > 0 else "no_data",
                stored_count,
                search_query
            )
            
            return stored_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error storing Smartprix data: {e}")
            await self._log_scraping_activity("smartprix", "failed", 0, search_query, [str(e)])
            return False

    async def store_flipkart_reviews_data(self, review_data: Dict) -> bool:
        """
        Store Flipkart reviews data in database
        
        Args:
            review_data: Dictionary containing product info and reviews
            
        Returns:
            bool: Success status
        """
        try:
            if not review_data or not review_data.get('reviews'):
                logger.warning("No Flipkart reviews data to store")
                return False
                
            collection = self.db[DatabaseConfig.FLIPKART_REVIEWS_COLLECTION]
            
            # Process reviews
            processed_reviews = []
            for review in review_data.get('reviews', []):
                processed_review = {
                    "reviewer_name": review.get('name', 'Anonymous'),
                    "rating": self._parse_flipkart_rating(review.get('rating', '0')),
                    "review_summary": review.get('summary', '').strip(),
                    "review_text": review.get('text', '').strip(),
                    "review_date": datetime.utcnow(),  # Flipkart doesn't provide dates in current scraper
                    "helpful_count": 0,  # Not captured in current scraper
                    "verified_purchase": True  # Assume verified for now
                }
                processed_reviews.append(processed_review)
            
            # Create review document
            review_doc = {
                "product_id": review_data.get('product_id', ''),
                "product_name": review_data.get('product_name', '').strip(),
                "platform": "flipkart",
                "total_reviews_scraped": len(processed_reviews),
                "reviews": processed_reviews,
                "scraped_at": datetime.utcnow(),
                "last_updated": datetime.utcnow(),
                "data_quality_score": len(processed_reviews) / 10.0 if len(processed_reviews) <= 10 else 1.0,
                "status": "active"
            }
            
            # Upsert review document
            result = await collection.update_one(
                {"product_id": review_data.get('product_id', '')},
                {
                    "$set": review_doc,
                    "$setOnInsert": {
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            success = result.upserted_id is not None or result.modified_count > 0
            
            if success:
                logger.info(f"✅ Flipkart: Stored {len(processed_reviews)} reviews for {review_data.get('product_name', 'Unknown')}")
                
                # Update review summary statistics
                await self._update_review_statistics(review_data.get('product_id', ''), processed_reviews)
            
            # Log scraping activity
            await self._log_scraping_activity(
                "flipkart_reviews", 
                "success" if success else "failed",
                len(processed_reviews),
                review_data.get('product_name', '')
            )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error storing Flipkart reviews: {e}")
            await self._log_scraping_activity(
                "flipkart_reviews", "failed", 0, 
                review_data.get('product_name', ''), [str(e)]
            )
            return False

    # Helper methods
    async def _store_price_history(self, product_identifier: str, platform: str, 
                                 current_price: float, original_price: float = None):
        """Store price point in price history collection"""
        try:
            price_history_collection = self.db["price_history"]
            
            price_doc = {
                "product_identifier": product_identifier,
                "platform": platform,
                "current_price": current_price,
                "original_price": original_price,
                "currency": "INR",
                "timestamp": datetime.utcnow(),
                "price_change": None  # Will be calculated later with trends
            }
            
            await price_history_collection.insert_one(price_doc)
            
        except Exception as e:
            logger.error(f"❌ Error storing price history: {e}")

    async def _update_review_statistics(self, product_id: str, reviews: List[Dict]):
        """Update review statistics for a product"""
        try:
            if not reviews:
                return
                
            # Calculate review statistics
            ratings = [r.get('rating', 0) for r in reviews if r.get('rating', 0) > 0]
            
            if not ratings:
                return
                
            review_stats = {
                "total_reviews": len(reviews),
                "average_rating": sum(ratings) / len(ratings),
                "rating_distribution": {},
                "last_review_update": datetime.utcnow()
            }
            
            # Calculate rating distribution
            for rating in [1, 2, 3, 4, 5]:
                count = len([r for r in ratings if r == rating])
                review_stats["rating_distribution"][str(rating)] = count
            
            # Update product collection with review stats
            products_collection = self.db[DatabaseConfig.PRODUCTS_COLLECTION]
            await products_collection.update_many(
                {"$or": [
                    {"asin": product_id},
                    {"smartprix_id": product_id},
                    {"product_id": product_id}
                ]},
                {"$set": {"review_statistics": review_stats}}
            )
            
        except Exception as e:
            logger.error(f"❌ Error updating review statistics: {e}")

    async def _log_scraping_activity(self, platform: str, status: str, 
                                   items_processed: int, search_query: str, 
                                   errors: List[str] = None):
        """Log scraping activity for monitoring"""
        try:
            logs_collection = self.db[DatabaseConfig.SCRAPING_LOGS_COLLECTION]
            
            log_doc = {
                "platform": platform,
                "status": status,  # success, failed, no_data, partial
                "items_processed": items_processed,
                "search_query": search_query,
                "errors": errors or [],
                "timestamp": datetime.utcnow(),
                "session_id": str(ObjectId())
            }
            
            await logs_collection.insert_one(log_doc)
            
        except Exception as e:
            logger.error(f"❌ Error logging scraping activity: {e}")

    # Parsing utility methods
    def _extract_asin_from_url(self, url: str) -> Optional[str]:
        """Extract ASIN from Amazon URL"""
        import re
        if not url:
            return None
        match = re.search(r'/dp/([A-Z0-9]{10})', url)
        return match.group(1) if match else None

    def _extract_smartprix_id_from_url(self, url: str) -> Optional[str]:
        """Extract product ID from Smartprix URL"""
        import re
        if not url:
            return None
        match = re.search(r'/([^/]+)/?$', url)
        return match.group(1) if match else None

    def _parse_amazon_price(self, price_str: str) -> Dict:
        """Parse Amazon price string"""
        if not price_str:
            return {"value": 0.0, "currency": "INR"}
            
        # Remove currency symbols and commas
        cleaned = price_str.replace('₹', '').replace(',', '').strip()
        
        try:
            value = float(cleaned)
            return {"value": value, "currency": "INR"}
        except ValueError:
            return {"value": 0.0, "currency": "INR"}

    def _parse_smartprix_price(self, price_str: str) -> Dict:
        """Parse Smartprix price string"""
        if not price_str:
            return {"value": 0.0, "currency": "INR"}
            
        # Remove currency symbols and commas
        cleaned = price_str.replace('₹', '').replace(',', '').strip()
        
        try:
            value = float(cleaned)
            return {"value": value, "currency": "INR"}
        except ValueError:
            return {"value": 0.0, "currency": "INR"}

    def _parse_amazon_rating(self, rating_str: str) -> Dict:
        """Parse Amazon rating string like '4.2 out of 5 stars'"""
        if not rating_str:
            return {"rating": 0.0, "max_rating": 5}
            
        try:
            # Extract the first number from the rating string
            import re
            match = re.search(r'(\d+\.?\d*)', rating_str)
            if match:
                rating = float(match.group(1))
                return {"rating": rating, "max_rating": 5}
        except (ValueError, AttributeError):
            pass
            
        return {"rating": 0.0, "max_rating": 5}

    def _parse_amazon_reviews(self, reviews_str: str) -> int:
        """Parse Amazon reviews count"""
        if not reviews_str:
            return 0
            
        # Remove commas and extract numbers
        cleaned = reviews_str.replace(',', '').strip()
        
        try:
            return int(cleaned)
        except ValueError:
            return 0

    def _parse_smartprix_score(self, score_str: str) -> float:
        """Parse Smartprix user score"""
        if not score_str:
            return 0.0
            
        try:
            return float(score_str)
        except ValueError:
            return 0.0

    def _parse_flipkart_rating(self, rating_str: str) -> int:
        """Parse Flipkart rating from star text"""
        if not rating_str:
            return 0
            
        # Flipkart ratings are usually numbers like "5", "4", etc.
        try:
            return int(rating_str.split()[0])
        except (ValueError, IndexError):
            return 0

    def _extract_brand_from_title(self, title: str) -> str:
        """Extract brand name from product title"""
        if not title or title is None:
            return "Unknown"
        
        # Ensure title is a string
        title = str(title).strip()
            
        title_lower = title.lower()
        common_brands = [
            'apple', 'samsung', 'oneplus', 'xiaomi', 'redmi', 'realme', 
            'oppo', 'vivo', 'nokia', 'motorola', 'poco', 'infinix',
            'dell', 'hp', 'lenovo', 'asus', 'acer', 'msi',
            'sony', 'jbl', 'boat', 'noise', 'zebronics'
        ]
        
        for brand in common_brands:
            if brand in title_lower:
                return brand.title()
                
        # Try to get the first word as brand
        first_word = title.split()[0] if title.split() else "Unknown"
        return first_word

    def _calculate_discount_percentage(self, current_price: float, original_price: float) -> float:
        """Calculate discount percentage"""
        if not original_price or original_price <= current_price:
            return 0.0
            
        try:
            discount = ((original_price - current_price) / original_price) * 100
            return round(discount, 2)
        except (ZeroDivisionError, TypeError):
            return 0.0

    def _calculate_data_quality_score(self, item: Dict) -> float:
        """Calculate data quality score based on available fields"""
        total_fields = 6
        available_fields = 0
        
        # Check essential fields with safe string operations
        title = item.get('product_title') or ''
        if str(title).strip():
            available_fields += 1
        if item.get('selling_price') or item.get('price'):
            available_fields += 1
        link = item.get('product_link') or ''
        if str(link).strip():
            available_fields += 1
        if item.get('star_rating') or item.get('user_score'):
            available_fields += 1
        if item.get('review_count') or item.get('key_specs'):
            available_fields += 1
        if item.get('original_price_mrp'):
            available_fields += 1
            
        return round(available_fields / total_fields, 2)

    async def store_flipkart_scraping_data(self, scraped_data: List[Dict], search_query: str) -> bool:
        """
        Store Flipkart scraping data in the flipkart_scraping_data collection
        
        Args:
            scraped_data: List of scraped product data from Flipkart
            search_query: The search query used for scraping
            
        Returns:
            bool: Success status
        """
        try:
            if not scraped_data:
                logger.warning("No Flipkart data to store")
                return False
                
            collection = self.db[DatabaseConfig.FLIPKART_SCRAPING_DATA_COLLECTION]
            stored_count = 0
            
            for item in scraped_data:
                try:
                    # Debug logging to identify the exact issue
                    logger.info(f"Processing item: {item}")
                    
                    # Safe get with proper defaults and type checking
                    selling_price = str(item.get('selling_price') or '0')
                    original_price = str(item.get('original_price_mrp') or '0')
                    star_rating = str(item.get('star_rating') or '')
                    review_count = str(item.get('review_count') or '0')
                    product_title = str(item.get('product_title') or '')
                    product_link = str(item.get('product_link') or '')
                    
                    logger.info(f"Extracted values - title: {product_title}, price: {selling_price}, rating: {star_rating}")
                    
                    # Parse price information
                    price_info = self._parse_amazon_price(selling_price)
                    original_price_info = self._parse_amazon_price(original_price)
                    
                    # Parse rating and reviews
                    rating_info = self._parse_amazon_rating(star_rating)
                    reviews_count = self._parse_amazon_reviews(review_count)
                    
                    # Create product document with safe string operations
                    safe_product_title = str(product_title or '').strip()
                    safe_product_link = str(product_link or '').strip()
                    
                    product_doc = {
                    "search_query": search_query,
                    "product_title": safe_product_title,
                    "brand": self._extract_brand_from_title(safe_product_title),
                    "selling_price": price_info['value'],
                    "selling_price_currency": price_info['currency'],
                    "original_price_mrp": original_price_info['value'],
                    "discount_percentage": self._calculate_discount_percentage(
                        price_info['value'], original_price_info['value']
                    ),
                    "star_rating": rating_info['rating'],
                    "rating_out_of": rating_info['max_rating'],
                    "review_count": reviews_count,
                    "product_link": safe_product_link,
                    "platform": "flipkart",
                    "scraped_at": datetime.utcnow(),
                    "last_updated": datetime.utcnow(),
                    "data_quality_score": self._calculate_data_quality_score(item),
                    "status": "active"
                }
                
                    # Upsert product (update if exists, insert if new)
                    filter_criteria = {
                        "product_title": product_doc["product_title"],
                        "platform": "flipkart"
                    }
                    
                    result = await collection.update_one(
                        filter_criteria,
                        {
                            "$set": product_doc,
                            "$setOnInsert": {
                                "created_at": datetime.utcnow(),
                                "product_id": str(ObjectId())
                            }
                        },
                        upsert=True
                    )
                    
                    if result.upserted_id or result.modified_count > 0:
                        stored_count += 1
                        
                    # Store in price history if we have price data
                    if price_info['value'] > 0:
                        await self._store_price_history(
                            product_doc["product_title"],
                            "flipkart",
                            price_info['value'],
                            original_price_info['value']
                        )

                except Exception as item_error:
                    logger.warning(f"⚠️ Failed to process Flipkart item: {item_error}")
                    continue

            logger.info(f"✅ Flipkart: Stored {stored_count}/{len(scraped_data)} products")
            
            # Log scraping activity
            await self._log_scraping_activity(
                "flipkart", 
                search_query, 
                len(scraped_data), 
                stored_count
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Flipkart storage error: {e}")
            return False

    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

# Singleton instance for scrapers to use
db_manager = ScraperDatabaseManager()