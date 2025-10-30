"""
Enhanced Database Manager for Competition Tracker
Includes user authentication, scraping outputs, and dynamic data retrieval
"""

import motor.motor_asyncio
import pymongo
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import json
import logging
from bson import ObjectId
import bcrypt
from passlib.context import CryptContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompetitionTrackerDB:
    """
    Enhanced MongoDB Database Manager for Competition Tracker
    Features:
    - User authentication and management
    - Scraping data storage (Amazon, Smartprix, Flipkart)
    - Dynamic data retrieval for frontend
    - Product and pricing analytics
    """
    
    def __init__(self, connection_string: str = None, database_name: str = "competition_tracker"):
        """Initialize database connection and collections"""
        if connection_string is None:
            # Use Atlas connection from environment
            from config import config
            connection_string = config.get_mongodb_url()
            database_name = config.DATABASE_NAME
        
        self.client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
        self.db = self.client[database_name]
        
        # Core collections
        self.users = self.db.users
        self.products = self.db.products
        self.price_history = self.db.price_history
        self.scraping_logs = self.db.scraping_logs
        
        # Scraping output collections
        self.amazon_data = self.db.amazon_scraping_data
        self.smartprix_data = self.db.smartprix_scraping_data
        self.flipkart_data = self.db.flipkart_scraping_data
        self.flipkart_reviews = self.db.flipkart_reviews
        
        # Analytics collections
        self.analytics_cache = self.db.analytics_cache
        self.price_alerts = self.db.price_alerts
        self.user_sessions = self.db.user_sessions
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        logger.info(f"Connected to MongoDB Atlas: {database_name}")

    async def setup_database(self):
        """Create indexes and initial setup for optimal performance"""
        try:
            # Users collection indexes
            await self.users.create_index("email", unique=True)
            await self.users.create_index("username", unique=True)
            await self.users.create_index("created_at")
            
            # Products collection indexes
            await self.products.create_index("product_id", unique=True)
            await self.products.create_index("asin", sparse=True)
            await self.products.create_index("smartprix_id", sparse=True)
            await self.products.create_index("flipkart_id", sparse=True)
            await self.products.create_index([("brand", 1), ("category", 1)])
            await self.products.create_index("metadata.status")
            await self.products.create_index("metadata.last_updated")
            
            # Price history indexes
            await self.price_history.create_index([
                ("product_id", 1), 
                ("platform", 1), 
                ("timestamp", -1)
            ])
            
            # Scraping data indexes
            await self.amazon_data.create_index("scraped_at")
            await self.smartprix_data.create_index("scraped_at")
            await self.flipkart_data.create_index("scraped_at")
            await self.flipkart_reviews.create_index("product_id")
            await self.flipkart_reviews.create_index("scraped_at")
            
            # User sessions with TTL (expire after 7 days)
            await self.user_sessions.create_index(
                "expires_at", 
                expireAfterSeconds=0
            )
            
            # Scraping logs with TTL (expire after 30 days)
            await self.scraping_logs.create_index(
                "timestamp", 
                expireAfterSeconds=30*24*60*60
            )
            
            logger.info("✅ Database indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            return False

    # ==================== USER AUTHENTICATION ====================
    
    async def create_user(self, user_data: Dict) -> Dict:
        """
        Create a new user account
        
        Args:
            user_data: {
                "username": str,
                "email": str,
                "password": str,
                "full_name": str (optional),
                "role": str (optional, default: "user")
            }
            
        Returns:
            {"success": bool, "user_id": str, "message": str}
        """
        try:
            # Check if user already exists
            existing_user = await self.users.find_one({
                "$or": [
                    {"email": user_data["email"]},
                    {"username": user_data["username"]}
                ]
            })
            
            if existing_user:
                return {
                    "success": False,
                    "message": "User with this email or username already exists"
                }
            
            # Hash password
            hashed_password = self.pwd_context.hash(user_data["password"])
            
            # Create user document
            user_doc = {
                "username": user_data["username"],
                "email": user_data["email"],
                "password": hashed_password,
                "full_name": user_data.get("full_name", ""),
                "role": user_data.get("role", "user"),
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": None,
                "preferences": {
                    "notifications": True,
                    "email_alerts": True,
                    "dashboard_theme": "light"
                }
            }
            
            result = await self.users.insert_one(user_doc)
            
            logger.info(f"✅ User created: {user_data['username']}")
            return {
                "success": True,
                "user_id": str(result.inserted_id),
                "message": "User created successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating user: {e}")
            return {
                "success": False,
                "message": f"Error creating user: {str(e)}"
            }
    
    async def authenticate_user(self, username: str, password: str) -> Dict:
        """
        Authenticate user login
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            {"success": bool, "user": dict, "message": str}
        """
        try:
            # Find user by username or email
            user = await self.users.find_one({
                "$or": [
                    {"username": username},
                    {"email": username}
                ]
            })
            
            if not user:
                return {
                    "success": False,
                    "message": "User not found"
                }
            
            if not user.get("is_active", True):
                return {
                    "success": False,
                    "message": "Account is deactivated"
                }
            
            # Verify password
            if not self.pwd_context.verify(password, user["password"]):
                return {
                    "success": False,
                    "message": "Invalid password"
                }
            
            # Update last login
            await self.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            # Remove password from response
            user_data = {k: v for k, v in user.items() if k != "password"}
            user_data["_id"] = str(user_data["_id"])
            
            logger.info(f"✅ User authenticated: {username}")
            return {
                "success": True,
                "user": user_data,
                "message": "Authentication successful"
            }
            
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return {
                "success": False,
                "message": "Authentication failed"
            }
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID (without password)"""
        try:
            user = await self.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user_data = {k: v for k, v in user.items() if k != "password"}
                user_data["_id"] = str(user_data["_id"])
                return user_data
            return None
        except Exception as e:
            logger.error(f"❌ Error getting user: {e}")
            return None

    # ==================== SCRAPING DATA STORAGE ====================
    
    async def store_amazon_scraping_data(self, scraping_data: Dict) -> str:
        """
        Store Amazon scraping results
        
        Args:
            scraping_data: Complete Amazon scraping output
            
        Returns:
            Scraping session ID
        """
        try:
            scraping_doc = {
                "platform": "amazon",
                "scraped_at": datetime.utcnow(),
                "search_terms": scraping_data.get("search_terms", []),
                "total_products": scraping_data.get("total_products", 0),
                "products": scraping_data.get("products", []),
                "errors": scraping_data.get("errors", []),
                "scraping_status": scraping_data.get("success", False),
                "metadata": {
                    "scraper_version": "v1.0",
                    "execution_time": scraping_data.get("execution_time", 0)
                }
            }
            
            result = await self.amazon_data.insert_one(scraping_doc)
            
            # Also store individual products in main products collection
            if scraping_data.get("products"):
                for product in scraping_data["products"]:
                    await self.store_amazon_product(product)
            
            logger.info(f"✅ Amazon scraping data stored: {scraping_data.get('total_products', 0)} products")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Error storing Amazon data: {e}")
            return None
    
    async def store_smartprix_scraping_data(self, scraping_data: Dict) -> str:
        """Store Smartprix scraping results"""
        try:
            scraping_doc = {
                "platform": "smartprix",
                "scraped_at": datetime.utcnow(),
                "product_urls": scraping_data.get("product_urls", []),
                "total_products": scraping_data.get("total_products", 0),
                "products": scraping_data.get("products", []),
                "errors": scraping_data.get("errors", []),
                "scraping_status": scraping_data.get("success", False),
                "metadata": {
                    "scraper_version": "v2.0",
                    "execution_time": scraping_data.get("execution_time", 0)
                }
            }
            
            result = await self.smartprix_data.insert_one(scraping_doc)
            
            # Store individual products
            if scraping_data.get("products"):
                for product in scraping_data["products"]:
                    await self.store_smartprix_product(product)
            
            logger.info(f"✅ Smartprix scraping data stored: {scraping_data.get('total_products', 0)} products")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Error storing Smartprix data: {e}")
            return None
    
    async def store_flipkart_reviews_data(self, reviews_data: Dict) -> str:
        """
        Store Flipkart reviews scraping results
        
        Args:
            reviews_data: {
                "product_id": str,
                "product_name": str,
                "reviews": List[Dict],
                "total_reviews": int,
                "scraping_url": str
            }
            
        Returns:
            Review session ID
        """
        try:
            reviews_doc = {
                "platform": "flipkart",
                "scraped_at": datetime.utcnow(),
                "product_id": reviews_data.get("product_id"),
                "product_name": reviews_data.get("product_name"),
                "scraping_url": reviews_data.get("scraping_url", ""),
                "total_reviews": len(reviews_data.get("reviews", [])),
                "reviews": reviews_data.get("reviews", []),
                "metadata": {
                    "scraper_version": "v1.0",
                    "pages_scraped": reviews_data.get("pages_scraped", 1)
                }
            }
            
            result = await self.flipkart_reviews.insert_one(reviews_doc)
            
            # Also create/update product entry
            await self.store_flipkart_product_info({
                "product_id": reviews_data.get("product_id"),
                "product_name": reviews_data.get("product_name"),
                "total_reviews": len(reviews_data.get("reviews", [])),
                "last_review_update": datetime.utcnow()
            })
            
            logger.info(f"✅ Flipkart reviews stored: {reviews_data.get('product_name')} - {len(reviews_data.get('reviews', []))} reviews")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Error storing Flipkart reviews: {e}")
            return None
    
    async def store_flipkart_product_info(self, product_data: Dict) -> str:
        """Store/update Flipkart product information"""
        try:
            # Check if product exists
            existing_product = await self.products.find_one({
                "flipkart_id": product_data["product_id"]
            })
            
            if existing_product:
                # Update existing
                await self.products.update_one(
                    {"flipkart_id": product_data["product_id"]},
                    {
                        "$set": {
                            "platforms.flipkart.total_reviews": product_data.get("total_reviews", 0),
                            "platforms.flipkart.last_review_update": product_data.get("last_review_update"),
                            "metadata.updated_at": datetime.utcnow()
                        }
                    }
                )
                return str(existing_product["_id"])
            else:
                # Create new product
                product_doc = {
                    "product_id": str(ObjectId()),
                    "flipkart_id": product_data["product_id"],
                    "name": product_data["product_name"],
                    "brand": self._extract_brand(product_data["product_name"]),
                    "category": self._extract_category_from_name(product_data["product_name"]),
                    "platforms": {
                        "flipkart": {
                            "product_id": product_data["product_id"],
                            "total_reviews": product_data.get("total_reviews", 0),
                            "last_review_update": product_data.get("last_review_update"),
                            "url": f"https://www.flipkart.com/product/pid={product_data['product_id']}"
                        }
                    },
                    "metadata": {
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "status": "active",
                        "data_quality_score": 0.8
                    }
                }
                
                result = await self.products.insert_one(product_doc)
                return str(result.inserted_id)
                
        except Exception as e:
            logger.error(f"❌ Error storing Flipkart product: {e}")
            return None

    # ==================== DYNAMIC DATA RETRIEVAL FOR FRONTEND ====================
    
    async def get_products_for_frontend(self, 
                                      limit: int = 20, 
                                      offset: int = 0,
                                      category: str = None,
                                      search: str = None) -> Dict:
        """
        Get products data formatted for frontend consumption
        
        Args:
            limit: Number of products to return
            offset: Number of products to skip (pagination)
            category: Filter by category
            search: Search in product names
            
        Returns:
            {
                "products": List[Dict],
                "total": int,
                "page": int,
                "per_page": int,
                "has_next": bool
            }
        """
        try:
            # Build query
            query = {"metadata.status": "active"}
            
            if category:
                query["category"] = category
            
            if search:
                query["name"] = {"$regex": search, "$options": "i"}
            
            # Get total count
            total = await self.products.count_documents(query)
            
            # Get products with pagination
            products_cursor = self.products.find(query).skip(offset).limit(limit).sort("metadata.updated_at", -1)
            products = await products_cursor.to_list(length=limit)
            
            # Format for frontend
            formatted_products = []
            for product in products:
                formatted_product = {
                    "id": str(product["_id"]),
                    "product_id": product.get("product_id"),
                    "name": product.get("name"),
                    "brand": product.get("brand"),
                    "category": product.get("category"),
                    "platforms": {},
                    "pricing_summary": {
                        "lowest_price": None,
                        "highest_price": None,
                        "best_platform": None
                    },
                    "last_updated": product.get("metadata", {}).get("updated_at")
                }
                
                # Process platform data
                platforms = product.get("platforms", {})
                prices = []
                
                for platform_name, platform_data in platforms.items():
                    formatted_product["platforms"][platform_name] = {
                        "price": platform_data.get("current_price"),
                        "original_price": platform_data.get("original_price"),
                        "rating": platform_data.get("rating"),
                        "reviews": platform_data.get("reviews_count") or platform_data.get("total_reviews"),
                        "url": platform_data.get("url"),
                        "availability": platform_data.get("availability", "unknown")
                    }
                    
                    if platform_data.get("current_price"):
                        prices.append({
                            "platform": platform_name,
                            "price": platform_data["current_price"]
                        })
                
                # Calculate pricing summary
                if prices:
                    sorted_prices = sorted(prices, key=lambda x: x["price"])
                    formatted_product["pricing_summary"] = {
                        "lowest_price": sorted_prices[0]["price"],
                        "highest_price": sorted_prices[-1]["price"],
                        "best_platform": sorted_prices[0]["platform"]
                    }
                
                formatted_products.append(formatted_product)
            
            return {
                "products": formatted_products,
                "total": total,
                "page": (offset // limit) + 1,
                "per_page": limit,
                "has_next": offset + limit < total
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting products for frontend: {e}")
            return {
                "products": [],
                "total": 0,
                "page": 1,
                "per_page": limit,
                "has_next": False,
                "error": str(e)
            }
    
    async def get_product_details_for_frontend(self, product_id: str) -> Dict:
        """Get detailed product information for frontend"""
        try:
            product = await self.products.find_one({"_id": ObjectId(product_id)})
            
            if not product:
                return {"error": "Product not found"}
            
            # Get price history
            price_history = await self.price_history.find({
                "product_id": product.get("product_id")
            }).sort("timestamp", -1).limit(30).to_list(30)
            
            # Get reviews if available
            reviews_data = await self.flipkart_reviews.find_one({
                "product_id": product.get("flipkart_id")
            }, sort=[("scraped_at", -1)])
            
            # Format detailed response
            detailed_product = {
                "id": str(product["_id"]),
                "product_id": product.get("product_id"),
                "name": product.get("name"),
                "brand": product.get("brand"),
                "category": product.get("category"),
                "platforms": product.get("platforms", {}),
                "price_history": [
                    {
                        "platform": ph["platform"],
                        "price": ph["price"],
                        "timestamp": ph["timestamp"].isoformat()
                    }
                    for ph in price_history
                ],
                "reviews": {
                    "total": reviews_data.get("total_reviews", 0) if reviews_data else 0,
                    "recent_reviews": reviews_data.get("reviews", [])[:5] if reviews_data else [],
                    "last_updated": reviews_data.get("scraped_at").isoformat() if reviews_data else None
                },
                "analytics": product.get("pricing_analytics", {}),
                "last_updated": product.get("metadata", {}).get("updated_at")
            }
            
            return detailed_product
            
        except Exception as e:
            logger.error(f"❌ Error getting product details: {e}")
            return {"error": str(e)}
    
    async def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics for frontend"""
        try:
            stats = {
                "total_products": await self.products.count_documents({"metadata.status": "active"}),
                "total_users": await self.users.count_documents({"is_active": True}),
                "platforms": {
                    "amazon": await self.products.count_documents({"platforms.amazon": {"$exists": True}}),
                    "smartprix": await self.products.count_documents({"platforms.smartprix": {"$exists": True}}),
                    "flipkart": await self.products.count_documents({"platforms.flipkart": {"$exists": True}})
                },
                "recent_activity": {
                    "products_updated_today": await self.products.count_documents({
                        "metadata.updated_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0)}
                    }),
                    "scraping_sessions_today": await self.scraping_logs.count_documents({
                        "timestamp": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0)}
                    })
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting dashboard stats: {e}")
            return {"error": str(e)}

    # ==================== LEGACY METHODS (Updated) ====================
    
    async def store_amazon_product(self, product_data: Dict) -> str:
        """Store Amazon product data (enhanced version)"""
        try:
            # Extract ASIN from link
            asin = self._extract_asin(product_data.get('link', ''))
            
            # Parse prices
            price_whole = str(product_data.get('price_whole', '0')).replace(',', '').replace('₹', '')
            price_fraction = str(product_data.get('price_fraction', '00'))
            
            try:
                current_price = float(f"{price_whole}.{price_fraction}") if price_whole and price_whole != '0' else 0.0
            except ValueError:
                current_price = 0.0
            
            # Parse original price
            original_price_str = str(product_data.get('list_price', '₹0')).replace('₹', '').replace(',', '')
            try:
                original_price = float(original_price_str) if original_price_str and original_price_str != '0' else current_price
            except ValueError:
                original_price = current_price
            
            # Parse rating and reviews
            rating_text = product_data.get('rating', '0 out of 5 stars')
            try:
                rating = float(rating_text.split()[0]) if 'out of' in rating_text else 0.0
            except (ValueError, IndexError):
                rating = 0.0
            
            reviews_text = str(product_data.get('reviews', '0')).replace(',', '')
            try:
                reviews_count = int(reviews_text) if reviews_text.isdigit() else 0
            except ValueError:
                reviews_count = 0
            
            # Create/update product document
            product_doc = {
                "product_id": asin or str(ObjectId()),
                "asin": asin,
                "name": product_data.get('title', '').strip(),
                "brand": self._extract_brand(product_data.get('title', '')),
                "category": "electronics",
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
            
            # Upsert product
            result = await self.products.update_one(
                {"asin": asin} if asin else {"name": product_doc["name"]},
                {"$set": product_doc},
                upsert=True
            )
            
            product_id = str(result.upserted_id) if result.upserted_id else product_doc["product_id"]
            
            # Store price history
            if current_price > 0:
                await self._store_price_point(product_id, "amazon", current_price, original_price)
            
            return product_id
            
        except Exception as e:
            logger.error(f"❌ Error storing Amazon product: {e}")
            return None

    # ==================== HELPER METHODS ====================
    
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
    
    def _extract_asin(self, amazon_url: str) -> str:
        """Extract ASIN from Amazon URL"""
        import re
        if not amazon_url:
            return None
        match = re.search(r'/dp/([A-Z0-9]{10})', amazon_url)
        return match.group(1) if match else None
    
    def _extract_brand(self, product_name: str) -> str:
        """Extract brand from product name"""
        if not product_name:
            return "Unknown"
        
        common_brands = ['Apple', 'Samsung', 'OnePlus', 'Xiaomi', 'iPhone', 'MacBook', 'Dell', 'HP', 'Lenovo', 'Sony', 'LG']
        product_name_lower = product_name.lower()
        
        for brand in common_brands:
            if brand.lower() in product_name_lower:
                return brand
        return "Unknown"
    
    def _extract_category_from_name(self, product_name: str) -> str:
        """Extract category from product name"""
        if not product_name:
            return "electronics"
            
        categories = {
            'mobile': ['mobile', 'phone', 'smartphone', 'iphone', 'galaxy'],
            'laptop': ['laptop', 'macbook', 'notebook', 'thinkpad'],
            'tablet': ['tablet', 'ipad'],
            'headphones': ['headphones', 'earphones', 'earbuds', 'airpods'],
            'watch': ['watch', 'smartwatch']
        }
        
        name_lower = product_name.lower()
        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        return "electronics"
    
    def _calculate_data_quality(self, product_data: Dict) -> float:
        """Calculate data quality score (0-1)"""
        if not product_data:
            return 0.0
            
        checks = [
            bool(product_data.get('title')),
            bool(product_data.get('price_whole')),
            bool(product_data.get('link')),
            bool(product_data.get('rating')),
        ]
        
        score = sum(checks) / len(checks)
        return round(score, 2)

    async def close(self):
        """Close database connection"""
        self.client.close()
        logger.info("Database connection closed")


# ==================== MIGRATION AND UTILITY FUNCTIONS ====================

async def migrate_existing_json_data():
    """Migrate existing JSON data to new MongoDB Atlas structure"""
    db = CompetitionTrackerDB()
    await db.setup_database()
    
    try:
        # Migrate existing Amazon data
        try:
            with open('competitor_intelligence_db.json', 'r', encoding='utf-8') as f:
                amazon_data = json.load(f)
            
            logger.info(f"Migrating {len(amazon_data)} Amazon products...")
            
            migration_result = {
                "search_terms": ["macbook", "smartphone"],  # example
                "total_products": len(amazon_data),
                "products": amazon_data,
                "success": True,
                "execution_time": 0
            }
            
            await db.store_amazon_scraping_data(migration_result)
            
        except FileNotFoundError:
            logger.info("No existing Amazon JSON file found")
        
        # Migrate existing Flipkart reviews
        try:
            with open('flipkart_reviews_db.json', 'r', encoding='utf-8') as f:
                flipkart_data = json.load(f)
            
            logger.info(f"Migrating {len(flipkart_data)} Flipkart review sets...")
            
            for review_set in flipkart_data:
                await db.store_flipkart_reviews_data(review_set)
                
        except FileNotFoundError:
            logger.info("No existing Flipkart reviews JSON file found")
        
        logger.info("✅ Migration completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
    
    await db.close()


if __name__ == "__main__":
    # Run migration
    import asyncio
    asyncio.run(migrate_existing_json_data())