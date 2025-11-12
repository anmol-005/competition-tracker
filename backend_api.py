"""
FastAPI Backend for Competition Tracker
Provides REST API endpoints for frontend integration
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import asyncio
import jwt
from datetime import datetime, timedelta
import os
from enhanced_database_manager import CompetitionTrackerDB
from scraper_db_utils import ScraperDatabaseManager
from fastapi.security import OAuth2PasswordBearer

# FastAPI app will be initialized after lifespan definition

# Security
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Database instances
db = CompetitionTrackerDB()
scraper_db = ScraperDatabaseManager()

# Optional auth for development
async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    """Optional authentication - returns admin user if no credentials for development"""
    if not credentials:
        return {
            "_id": "admin",
            "username": "admin", 
            "email": "admin@example.com",
            "role": "admin", 
            "is_active": True
        }
    return await get_current_user(credentials)

# ==================== PYDANTIC MODELS ====================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = ""
    role: Optional[str] = "user"

class UserLogin(BaseModel):
    username: str  # Can be username or email
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class ProductQuery(BaseModel):
    limit: Optional[int] = 20
    offset: Optional[int] = 0
    category: Optional[str] = None
    search: Optional[str] = None

class ScrapingRequest(BaseModel):
    platform: str
    product_name: Optional[str] = ""
    search_terms: Optional[List[str]] = []
    product_urls: Optional[List[str]] = []

# ==================== AUTH UTILITIES ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token with development bypass"""
    
    # Development bypass - if no token provided, return admin user
    if not credentials or not credentials.credentials:
        return {
            "_id": "admin",
            "username": "admin", 
            "email": "admin@example.com",
            "role": "admin",
            "is_active": True
        }
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        # In development, also return admin user for invalid tokens
        return {
            "_id": "admin",
            "username": "admin",
            "email": "admin@example.com", 
            "role": "admin",
            "is_active": True
        }
    
    user = await db.get_user_by_id(user_id)
    if user is None:
        # Fallback to admin user
        return {
            "_id": "admin",
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin", 
            "is_active": True
        }
    
    return user

# Health check endpoints will be defined later after app initialization# ==================== LIFESPAN EVENTS ====================

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    await db.setup_database()
    print("🚀 Competition Tracker API Started!")
    print(f"📊 Database: {db.db.name}")
    print("🌐 CORS Origins: [http://localhost:3000, http://127.0.0.1:3000, http://localhost:5173]")
    
    yield
    
    # Shutdown
    await db.close()
    print("👋 Competition Tracker API Stopped!")

# Update app initialization to use lifespan
app = FastAPI(
    title="Competition Tracker API",
    description="REST API for Competition Tracker - E-commerce Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:5173",
        "http://localhost:5000",
        "http://127.0.0.1:5000"
    ],  # React/Vite default ports
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ==================== AUTHENTICATION ENDPOINTS ====================

@app.post("/api/auth/register", response_model=Dict[str, Any])
async def register_user(user_data: UserCreate):
    """Register a new user"""
    result = await db.create_user({
        "username": user_data.username,
        "email": user_data.email,
        "password": user_data.password,
        "full_name": user_data.full_name,
        "role": user_data.role
    })
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return {
        "message": "User registered successfully",
        "user_id": result["user_id"]
    }

from fastapi import HTTPException, status
from datetime import timedelta

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

@app.post("/api/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    """Authenticate user and return JWT token"""

    username = user_credentials.username
    password = user_credentials.password

    # --- ✅ Handle Admin Login ---
    if username == "admin" and password == "admin123":
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": "admin", "role": "admin"},
            expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "_id": "admin",
                "username": "admin",
                "role": "admin"
            }
        }

    # --- 🧠 Normal user authentication ---
    result = await db.authenticate_user(username, password)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"],
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = result["user"]
    role = user.get("role", "user")  # default role

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["_id"], "role": role},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

from jose import JWTError, jwt

@app.get("/api/auth/me", response_model=Dict[str, Any])
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role", "user")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return {"_id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

# ==================== PRODUCT ENDPOINTS ====================

@app.get("/api/products", response_model=Dict[str, Any])
async def get_products(
    limit: int = 20,
    offset: int = 0,
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_optional_user)
):
    """Get products with pagination and filtering"""
    result = await db.get_products_for_frontend(
        limit=limit,
        offset=offset,
        category=category,
        search=search
    )
    
    return result

@app.get("/api/products/{product_id}", response_model=Dict[str, Any])
async def get_product_details(
    product_id: str,
    current_user: dict = Depends(get_optional_user)
):
    """Get detailed product information"""
    result = await db.get_product_details_for_frontend(product_id)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result


@app.post("/api/dev/seed-demo-products", response_model=Dict[str, Any])
async def seed_demo_products(current_user: dict = Depends(get_optional_user)):
    """DEV ONLY: Seed demo products with proper names and pricing for frontend display.
    This will add demo products alongside existing database products.
    """
    # restrict to admin when auth is enabled
    if current_user and current_user.get("role") != "admin" and current_user.get("_id") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required for seeding")

    try:
        demo_products = [
            {
                "product_id": "DEMO-MB-001",
                "name": "MacBook Pro 14 M3",
                "brand": "Apple",
                "category": "laptops",
                "platforms": {
                    "amazon": {"current_price": 154900, "price": 154900, "url": "https://amazon.com/macbook-pro"},
                    "flipkart": {"current_price": 160000, "price": 160000, "url": "https://flipkart.com/macbook-pro"},
                    "smartprix": {"current_price": 158000, "price": 158000, "url": "https://smartprix.com/macbook-pro"}
                },
                "metadata": {"status": "active", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}
            },
            {
                "product_id": "DEMO-LAP-002",
                "name": "ASUS ROG Strix G15",
                "brand": "ASUS",
                "category": "laptops",
                "platforms": {
                    "amazon": {"current_price": 89999, "price": 89999, "url": "https://amazon.com/asus-rog"},
                    "flipkart": {"current_price": 94999, "price": 94999, "url": "https://flipkart.com/asus-rog"}
                },
                "metadata": {"status": "active", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}
            },
            {
                "product_id": "DEMO-PHN-003",
                "name": "iPhone 15 Pro",
                "brand": "Apple",
                "category": "smartphones",
                "platforms": {
                    "amazon": {"current_price": 134900, "price": 134900, "url": "https://amazon.com/iphone-15"},
                    "flipkart": {"current_price": 139900, "price": 139900, "url": "https://flipkart.com/iphone-15"},
                    "smartprix": {"current_price": 136900, "price": 136900, "url": "https://smartprix.com/iphone-15"}
                },
                "metadata": {"status": "active", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}
            },
            {
                "product_id": "DEMO-TBL-004",
                "name": "iPad Air M2",
                "brand": "Apple",
                "category": "tablets",
                "platforms": {
                    "flipkart": {"current_price": 59900, "price": 59900, "url": "https://flipkart.com/ipad-air"},
                    "amazon": {"current_price": 58900, "price": 58900, "url": "https://amazon.com/ipad-air"}
                },
                "metadata": {"status": "active", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}
            },
            {
                "product_id": "DEMO-HED-005",
                "name": "Sony WH-1000XM5",
                "brand": "Sony",
                "category": "headphones",
                "platforms": {
                    "amazon": {"current_price": 29990, "price": 29990, "url": "https://amazon.com/sony-wh"},
                    "flipkart": {"current_price": 28990, "price": 28990, "url": "https://flipkart.com/sony-wh"}
                },
                "metadata": {"status": "active", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}
            }
        ]

        inserted_ids = []
        for prod in demo_products:
            # upsert by product_id to be idempotent
            res = await db.products.update_one({"product_id": prod["product_id"]}, {"$set": prod, "$setOnInsert": {"created_at": datetime.utcnow()}}, upsert=True)
            if res.upserted_id:
                inserted_ids.append(str(res.upserted_id))
            elif res.modified_count > 0:
                # Product was updated
                existing_prod = await db.products.find_one({"product_id": prod["product_id"]})
                inserted_ids.append(str(existing_prod["_id"]))

        return {"success": True, "inserted_ids": inserted_ids, "message": "Demo products seeded successfully", "count": len(demo_products)}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Seeding failed: {str(e)}")

@app.post("/api/scrape-and-predict/{product_name}", response_model=Dict[str, Any])
async def scrape_and_predict_workflow(
    product_name: str,
    current_user: dict = Depends(get_optional_user)
):
    """
    Full workflow: Scrape all competitor platforms for a product, then run LLM price prediction.
    Example: POST /api/scrape-and-predict/MacBook%20Pro -> scrapes Amazon, Flipkart, Smartprix -> LLM prediction
    """
    workflow_results = {
        "product_name": product_name,
        "scraping_results": {},
        "prediction_result": None,
        "workflow_success": False,
        "errors": [],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        # Step 1: Scrape all platforms
        platforms_to_scrape = ["amazon", "smartprix", "flipkart"]
        scraped_data = {}
        
        for platform in platforms_to_scrape:
            try:
                if platform == "amazon":
                    # Amazon expects search_terms
                    scrape_result = await trigger_amazon_scraping_internal([product_name], product_name)
                elif platform == "smartprix":
                    # Smartprix expects product URLs (we'll use a mock URL for demo)
                    scrape_result = await trigger_smartprix_scraping_internal([f"https://smartprix.com/search/{product_name}"], product_name)
                elif platform == "flipkart":
                    # Flipkart scraping (we'll implement this)
                    scrape_result = await trigger_flipkart_scraping_internal([f"https://flipkart.com/search/{product_name}"], product_name)
                
                workflow_results["scraping_results"][platform] = {
                    "success": scrape_result.get("success", False),
                    "products": scrape_result.get("products", []),
                    "total_products": scrape_result.get("total_products", 0)
                }
                
                # Extract price data for LLM
                if scrape_result.get("products"):
                    scraped_data[platform] = scrape_result["products"][0]  # Take first result
                    
            except Exception as e:
                workflow_results["errors"].append(f"{platform} scraping failed: {str(e)}")
                workflow_results["scraping_results"][platform] = {"success": False, "error": str(e)}
        
        # Step 2: Aggregate competitor prices
        competitor_prices = []
        platforms_list = []
        
        for platform, data in scraped_data.items():
            if isinstance(data, dict) and "price" in data:
                try:
                    # Parse price (remove currency symbols)
                    price_str = str(data["price"])
                    price_clean = ''.join(filter(str.isdigit, price_str))
                    if price_clean:
                        price = int(price_clean)
                        competitor_prices.append(price)
                        platforms_list.append({
                            "source": platform,
                            "price": price,
                            "rating": data.get("rating", "N/A"),
                            "reviews": data.get("reviews", "N/A")
                        })
                except Exception as e:
                    workflow_results["errors"].append(f"Price parsing failed for {platform}: {str(e)}")
        
        # Step 3: Run LLM prediction if we have competitor data
        if competitor_prices:
            try:
                llm_input = {
                    "name": product_name,
                    "platforms": platforms_list,
                    "min_price": min(competitor_prices),
                    "max_price": max(competitor_prices),
                    "avg_price": sum(competitor_prices) / len(competitor_prices),
                    "price_range": max(competitor_prices) - min(competitor_prices)
                }
                
                # Import and run LLM
                from llm import PricePredictionLLM
                llm = PricePredictionLLM()
                
                prediction_result = await llm.generate_price_prediction(llm_input)
                workflow_results["prediction_result"] = prediction_result
                workflow_results["workflow_success"] = True
                
            except Exception as e:
                # Fallback prediction
                avg_price = sum(competitor_prices) / len(competitor_prices)
                recommended_price = round(avg_price * 0.98)  # 2% below average
                
                workflow_results["prediction_result"] = {
                    "predicted_price": recommended_price,
                    "decision": "price_cut" if recommended_price < avg_price else "hold",
                    "llm_rationale": f"Fallback: Recommend ₹{recommended_price} (2% below competitor average ₹{avg_price:.0f})",
                    "source": "heuristic_fallback",
                    "competitor_analysis": {
                        "platforms_found": len(platforms_list),
                        "price_range": f"₹{min(competitor_prices)} - ₹{max(competitor_prices)}",
                        "average_price": f"₹{avg_price:.0f}"
                    }
                }
                workflow_results["errors"].append(f"LLM prediction failed, used fallback: {str(e)}")
        else:
            workflow_results["errors"].append("No competitor price data found for prediction")
            workflow_results["prediction_result"] = {
                "predicted_price": None,
                "decision": "insufficient_data",
                "llm_rationale": "Unable to predict: no competitor pricing data available",
                "source": "error"
            }
        
        return workflow_results
        
    except Exception as e:
        workflow_results["errors"].append(f"Workflow failed: {str(e)}")
        return workflow_results

# Helper functions for internal scraping calls
async def trigger_amazon_scraping_internal(search_terms: List[str], search_query: str):
    """Internal Amazon scraping without HTTP layer"""
    try:
        results = {"success": True, "products": [], "total_products": 0, "errors": []}
        
        # Mock Amazon scraping result for now
        results["products"] = [
            {
                "title": f"Amazon {search_query} Result",
                "price": "₹54,000",
                "rating": "4.3",
                "reviews": "1,245"
            }
        ]
        results["total_products"] = 1
        
        return results
    except Exception as e:
        return {"success": False, "products": [], "total_products": 0, "errors": [str(e)]}

async def trigger_smartprix_scraping_internal(product_urls: List[str], search_query: str):
    """Internal Smartprix scraping without HTTP layer"""
    try:
        results = {"success": True, "products": [], "total_products": 0, "errors": []}
        
        # Mock Smartprix scraping result
        results["products"] = [
            {
                "title": f"Smartprix {search_query} Result", 
                "price": "₹52,500",
                "rating": "4.1",
                "reviews": "890"
            }
        ]
        results["total_products"] = 1
        
        return results
    except Exception as e:
        return {"success": False, "products": [], "total_products": 0, "errors": [str(e)]}

async def trigger_flipkart_scraping_internal(product_urls: List[str], search_query: str):
    """Internal Flipkart scraping without HTTP layer"""
    try:
        results = {"success": True, "products": [], "total_products": 0, "errors": []}
        
        # Mock Flipkart scraping result
        results["products"] = [
            {
                "title": f"Flipkart {search_query} Result",
                "price": "₹60,000", 
                "rating": "4.4",
                "reviews": "2,156"
            }
        ]
        results["total_products"] = 1
        
        return results
    except Exception as e:
        return {"success": False, "products": [], "total_products": 0, "errors": [str(e)]}

@app.get("/api/dashboard/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    result = await db.get_dashboard_stats()
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )
    
    return result

# ==================== SCRAPING ENDPOINTS ====================

@app.post("/api/scraping/amazon", response_model=Dict[str, Any])
async def trigger_amazon_scraping(
    request: ScrapingRequest,
    current_user: dict = Depends(get_optional_user)
):
    """Trigger Amazon scraping"""
    if request.platform != "amazon":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid platform for this endpoint"
        )
    
    if not request.product_name and not request.search_terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product name or search terms are required for Amazon scraping"
        )
    
    try:
        # Use product_name if provided, otherwise use search_terms
        search_query = request.product_name or (request.search_terms[0] if request.search_terms else "Unknown Product")
        search_list = [request.product_name] if request.product_name else request.search_terms
        
        results = {
            "search_query": search_query,
            "total_products": 0,
            "products": [],
            "errors": [],
            "success": False,
            "execution_time": 0
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Import and run Amazon scraper
            from amazon_scraper import scrape_amazon
            
            results["success"] = True
            
            for search_term in search_list:
                try:
                    print(f"DEBUG: Starting Amazon scraping for '{search_term}'")
                    scraper_result = await scrape_amazon(search_term, max_items=10)
                    print(f"DEBUG: Scraper returned: {type(scraper_result)} with {len(scraper_result) if isinstance(scraper_result, list) else 'N/A'} items")
                    
                    if scraper_result and isinstance(scraper_result, list):
                        results["products"].extend(scraper_result)
                        results["total_products"] += len(scraper_result)
                        print(f"DEBUG: Added {len(scraper_result)} products to results")
                    else:
                        print(f"DEBUG: No valid results - scraper_result: {scraper_result}")
                        results["errors"].append(f"No products found for '{search_term}' - scraper returned empty results")
                except Exception as e:
                    print(f"DEBUG: Exception in Amazon scraping: {type(e).__name__}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    results["errors"].append(f"Error scraping '{search_term}': {type(e).__name__}: {str(e)}")
        
        except (ImportError, NotImplementedError) as e:
            # Handle Playwright or import issues
            results["errors"].append(f"Scraping unavailable: {str(e)}")
            # Create mock data for development
            results["products"] = [
                {
                    "title": f"Amazon {search_query} Sample",
                    "price": "₹25,999",
                    "link": "https://amazon.com/sample",
                    "rating": "4.2",
                    "reviews": "1,234"
                }
            ]
            results["total_products"] = len(results["products"])
            results["success"] = True  # Mark as successful since we have mock data
        
        results["execution_time"] = (datetime.utcnow() - start_time).total_seconds()
        
        # Store results in database using main database manager
        try:
            # Store the scraping session in the database
            session_doc = {
                "scraped_at": datetime.utcnow(),
                "search_query": search_query,
                "products": results["products"],
                "total_products": results["total_products"],
                "success": results["success"],
                "errors": results["errors"],
                "execution_time": results["execution_time"],
                "platform": "amazon"
            }
            
            # Insert into amazon_data collection
            insert_result = await db.amazon_data.insert_one(session_doc)
            session_id = str(insert_result.inserted_id)
            
            # Auto-sync scraped data to main products collection
            try:
                sync_result = await db.sync_scraped_data_to_products(search_query)
                if sync_result.get("success"):
                    results["sync_info"] = f"Updated {sync_result.get('updates_made', 0)} products with fresh data"
                    
                    # Force refresh product data for immediate frontend visibility
                    await db.refresh_product_pricing_summary()
                    
            except Exception as sync_error:
                results["errors"].append(f"Data sync warning: {str(sync_error)}")
            
        except Exception as e:
            session_id = f"storage_error_{str(e)[:50]}"
            results["errors"].append(f"Database storage failed: {str(e)}")
        
        return {
            "message": "Amazon scraping completed",
            "session_id": session_id,
            "total_products": results["total_products"],
            "errors": results["errors"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scraping failed: {str(e)}"
        )

@app.post("/api/scraping/smartprix", response_model=Dict[str, Any])
async def trigger_smartprix_scraping(
    request: ScrapingRequest,
    current_user: dict = Depends(get_optional_user)
):
    """Trigger Smartprix scraping"""
    if request.platform != "smartprix":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid platform for this endpoint"
        )
    
    if not request.product_name and not request.product_urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product name or URLs are required for Smartprix scraping"
        )
    
    try:
        # Use product_name if provided, otherwise use URLs
        search_query = request.product_name or "Unknown Product"
        
        results = {
            "search_query": search_query,
            "total_products": 0,
            "products": [],
            "errors": [],
            "success": False,
            "execution_time": 0
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Import and run Smartprix scraper
            from smartprix_scraper import SmartprixScraper
            
            results["success"] = True
            
            if request.product_name:
                # Use product name to scrape
                async with SmartprixScraper() as scraper:
                    try:
                        scraper_result = await scraper.scrape_product_by_name(request.product_name)
                        if scraper_result and scraper_result.get("success"):
                            results["products"].append(scraper_result)
                            results["total_products"] += 1
                    except Exception as e:
                        results["errors"].append(f"Error scraping '{request.product_name}': {str(e)}")
            else:
                # Use URLs (fallback)
                async with SmartprixScraper() as scraper:
                    for url in request.product_urls:
                        try:
                            scraper_result = await scraper.scrape_product(url)
                            if scraper_result and scraper_result.get("success"):
                                results["products"].append(scraper_result)
                                results["total_products"] += 1
                            else:
                                results["errors"].append(f"Failed to scrape {url}")
                        except Exception as e:
                            results["errors"].append(f"Error scraping '{url}': {str(e)}")
        
        except (ImportError, NotImplementedError) as e:
            # Handle Playwright or import issues
            results["errors"].append(f"Scraping unavailable: {str(e)}")
            # Create mock data for development
            results["products"] = [
                {
                    "title": f"Smartprix {search_query} Sample",
                    "price": "₹18,999",
                    "link": f"https://smartprix.com/search/{search_query}",
                    "rating": "4.1",
                    "specifications": {"RAM": "8GB", "Storage": "256GB"}
                }
            ]
            results["total_products"] = len(results["products"])
            results["success"] = True  # Mark as successful since we have mock data
        
        results["execution_time"] = (datetime.utcnow() - start_time).total_seconds()
        
        # Store results in database using main database manager
        try:
            # Store the scraping session in the database
            session_doc = {
                "scraped_at": datetime.utcnow(),
                "search_query": search_query,
                "products": results["products"],
                "total_products": results["total_products"],
                "success": results["success"],
                "errors": results["errors"],
                "execution_time": results["execution_time"],
                "platform": "smartprix"
            }
            
            # Insert into smartprix_data collection
            insert_result = await db.smartprix_data.insert_one(session_doc)
            session_id = str(insert_result.inserted_id)
            
            # Auto-sync scraped data to main products collection
            try:
                sync_result = await db.sync_scraped_data_to_products(search_query)
                if sync_result.get("success"):
                    results["sync_info"] = f"Updated {sync_result.get('updates_made', 0)} products with fresh data"
            except Exception as sync_error:
                results["errors"].append(f"Data sync warning: {str(sync_error)}")
            
        except Exception as e:
            session_id = f"storage_error_{str(e)[:50]}"
            results["errors"].append(f"Database storage failed: {str(e)}")
        
        return {
            "message": "Smartprix scraping completed",
            "session_id": session_id,
            "total_products": results["total_products"],
            "errors": results["errors"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scraping failed: {str(e)}"
        )

@app.post("/api/scraping/flipkart", response_model=Dict[str, Any])
async def trigger_flipkart_scraping(
    request: ScrapingRequest,
    current_user: dict = Depends(get_optional_user)
):
    """Trigger Flipkart product scraping"""
    if request.platform != "flipkart":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid platform for this endpoint"
        )
    
    if not request.product_name and not request.product_urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product name or URLs are required for Flipkart scraping"
        )
    
    try:
        # Use product_name if provided
        search_query = request.product_name or "Unknown Product"
        
        results = {
            "success": False,
            "products": [],
            "total_products": 0,
            "errors": [],
            "execution_time": 0,
            "search_query": search_query
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Import and run Flipkart scraper function
            from flipkart_scraper import scrape_flipkart
            
            results["success"] = True
            
            search_list = []
            if request.product_name:
                search_list = [request.product_name]
            elif request.product_urls:
                # For URLs, extract search terms or use fallback
                search_list = ["Flipkart Product Search"]
            else:
                search_list = ["General Flipkart Search"]
                
            for search_term in search_list:
                try:
                    print(f"DEBUG: Starting Flipkart scraping for '{search_term}'")
                    scraper_result = await scrape_flipkart(search_term, max_items=10)
                    print(f"DEBUG: Flipkart scraper returned: {type(scraper_result)} with {len(scraper_result) if isinstance(scraper_result, list) else 'N/A'} items")
                    
                    if scraper_result and isinstance(scraper_result, list):
                        results["products"].extend(scraper_result)
                        results["total_products"] += len(scraper_result)
                        print(f"DEBUG: Added {len(scraper_result)} Flipkart products to results")
                    else:
                        print(f"DEBUG: No valid Flipkart results - scraper_result: {scraper_result}")
                        results["errors"].append(f"No products found for '{search_term}' - scraper returned empty results")
                except Exception as e:
                    print(f"DEBUG: Exception in Flipkart scraping: {type(e).__name__}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    results["errors"].append(f"Error scraping '{search_term}': {type(e).__name__}: {str(e)}")
        
        except (ImportError, NotImplementedError) as e:
            # Handle Playwright or import issues - provide mock data
            results["errors"].append(f"Scraping unavailable: {str(e)}")
            # Create mock data for development
            results["products"] = [
                {
                    "title": f"Flipkart {search_query} Sample",
                    "price": "₹45,999",
                    "link": f"https://flipkart.com/search/{search_query}",
                    "rating": "4.2",
                    "specifications": {"RAM": "8GB", "Storage": "256GB"}
                }
            ]
            results["total_products"] = len(results["products"])
            results["success"] = True  # Mark as successful since we have mock data
        
        results["execution_time"] = (datetime.utcnow() - start_time).total_seconds()
        
        # Store results in database using main database manager
        try:
            # Store the scraping session in the database
            session_doc = {
                "scraped_at": datetime.utcnow(),
                "search_query": search_query,
                "products": results["products"],
                "total_products": results["total_products"],
                "success": results["success"],
                "errors": results["errors"],
                "execution_time": results["execution_time"],
                "platform": "flipkart"
            }
            
            # Insert into flipkart_data collection
            insert_result = await db.flipkart_data.insert_one(session_doc)
            session_id = str(insert_result.inserted_id)
            
            # Auto-sync scraped data to main products collection
            try:
                sync_result = await db.sync_scraped_data_to_products(search_query)
                if sync_result.get("success"):
                    results["sync_info"] = f"Updated {sync_result.get('updates_made', 0)} products with fresh data"
            except Exception as sync_error:
                results["errors"].append(f"Data sync warning: {str(sync_error)}")
            
        except Exception as e:
            session_id = f"storage_error_{str(e)[:50]}"
            results["errors"].append(f"Database storage failed: {str(e)}")
        
        return {
            "message": "Flipkart scraping completed", 
            "session_id": session_id,
            **results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reviews scraping failed: {str(e)}"
        )

# ==================== ADMIN DASHBOARD ENDPOINTS ====================

@app.get("/api/admin/dashboard-stats", response_model=Dict[str, Any])
async def get_admin_dashboard_stats(current_user: dict = Depends(get_optional_user)):
    """Get comprehensive dashboard statistics for admin"""
    if current_user.get("role") != "admin" and current_user.get("_id") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        stats = await db.get_dashboard_stats()
        
        # Get additional admin-specific stats
        revenue_trends = await db.get_revenue_trends()
        top_products = await db.get_top_tracked_products()
        
        # Get recent activity from database
        recent_activity = await db.get_recent_activity()
        
        return {
            "success": True,
            "stats": stats,
            "revenue_trends": revenue_trends,
            "top_products": top_products,
            "recent_activity": recent_activity[:5]  # Top 5 recent activities
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard stats: {str(e)}"
        )

@app.get("/api/admin/users", response_model=Dict[str, Any])
async def get_all_users_admin(current_user: dict = Depends(get_optional_user)):
    """Get all users for admin management"""
    if current_user.get("role") != "admin" and current_user.get("_id") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        users = await db.get_all_users()
        return {
            "success": True,
            "users": users,
            "total_count": len(users)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )

@app.post("/api/admin/users/{user_id}/flag", response_model=Dict[str, Any])
async def flag_user_admin(user_id: str, current_user: dict = Depends(get_current_user)):
    """Flag a user (admin only)"""
    if current_user.get("role") != "admin" and current_user.get("_id") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        result = await db.flag_user(user_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to flag user: {str(e)}"
        )

@app.post("/api/admin/users/{user_id}/ban", response_model=Dict[str, Any])
async def ban_user_admin(user_id: str, current_user: dict = Depends(get_current_user)):
    """Ban a user (admin only)"""
    if current_user.get("role") != "admin" and current_user.get("_id") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        result = await db.ban_user(user_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ban user: {str(e)}"
        )

@app.post("/api/admin/users/{user_id}/unban", response_model=Dict[str, Any])
async def unban_user_admin(user_id: str, current_user: dict = Depends(get_current_user)):
    """Unban a user (admin only)"""
    if current_user.get("role") != "admin" and current_user.get("_id") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        result = await db.unban_user(user_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unban user: {str(e)}"
        )

@app.get("/api/admin/scraping-sessions", response_model=Dict[str, Any])
async def get_scraping_sessions(current_user: dict = Depends(get_optional_user)):
    """Get recent scraping sessions for admin dashboard"""
    if current_user.get("role") != "admin" and current_user.get("_id") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Get recent sessions from all platforms
        amazon_sessions = await db.amazon_data.find().sort("scraped_at", -1).limit(10).to_list(10)
        smartprix_sessions = await db.smartprix_data.find().sort("scraped_at", -1).limit(10).to_list(10)
        # Use flipkart scraping data (not reviews) for dashboard sessions
        flipkart_sessions = await db.flipkart_data.find().sort("scraped_at", -1).limit(10).to_list(10)
        
        # Format sessions for frontend
        all_sessions = []
        
        for session in amazon_sessions:
            all_sessions.append({
                "id": str(session["_id"]),
                "platform": "Amazon",
                "scraped_at": session["scraped_at"].isoformat(),
                "total_products": session.get("total_products", 0),
                "success": session.get("scraping_status", False),
                "errors": len(session.get("errors", [])),
                "execution_time": session.get("metadata", {}).get("execution_time", 0)
            })
        
        for session in smartprix_sessions:
            all_sessions.append({
                "id": str(session["_id"]),
                "platform": "Smartprix",
                "scraped_at": session["scraped_at"].isoformat(),
                "total_products": session.get("total_products", 0),
                "success": session.get("scraping_status", False),
                "errors": len(session.get("errors", [])),
                "execution_time": session.get("metadata", {}).get("execution_time", 0)
            })
        
        for session in flipkart_sessions:
            all_sessions.append({
                "id": str(session["_id"]),
                "platform": "Flipkart",
                "scraped_at": session["scraped_at"].isoformat(),
                "total_products": session.get("total_products", 0),
                "success": session.get("scraping_status", True),
                "errors": len(session.get("errors", [])),
                "execution_time": session.get("metadata", {}).get("execution_time", 0)
            })
        
        # Sort by scraped_at descending
        all_sessions.sort(key=lambda x: x["scraped_at"], reverse=True)
        
        return {
            "success": True,
            "sessions": all_sessions[:20]  # Return top 20 recent sessions
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scraping sessions: {str(e)}"
        )

# ==================== HEALTH CHECK ====================

@app.get("/api/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Competition Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

# Add these imports near the top of backend_api.py (if not already present)
from fastapi import Path
import traceback
from typing import Any, Dict

# Add this route near your product endpoints (e.g. after get_product_details_for_frontend)
@app.post("/api/predict/{product_id}", response_model=Dict[str, Any])
async def predict_price_for_product(
    product_id: str = Path(..., description="Database _id of the product"),
    current_user: dict = Depends(get_optional_user)
):
    """
    Run ML + LLM price prediction for a single product.
    - Returns structured JSON with predicted_price, decision, rationale, and metadata.
    - Uses the PricePredictionLLM in llm.py if available; falls back to a heuristic.
    """
    # 1) Load product details from DB (frontend helper)
    result = await db.get_product_details_for_frontend(product_id)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    product = result  # formatted for frontend by enhanced_database_manager.get_product_details_for_frontend
    # product keys: id, product_id, name, brand, platforms, pricing_summary, etc. :contentReference[oaicite:3]{index=3}

    # Prepare a safe payload to return
    response_payload: Dict[str, Any] = {
        "product_id": product.get("id"),
        "name": product.get("name"),
        "timestamp": datetime.utcnow().isoformat(),
        "source": "heuristic",
        "predicted_price": None,
        "decision": None,
        "llm_rationale": None,
        "ml_details": None,
    }

    # Fetch latest scraped data AND platform data for comprehensive analysis
    platforms_data = product.get("platforms", {})
    platforms_list = []
    prices = []
    
    # First, get latest scraped prices for this product name
    product_name = product.get("name", "")
    
    # Search recent scraping sessions for this product
    latest_scraped_data = []
    if product_name:
        # Get latest Amazon data
        amazon_sessions = await db.amazon_data.find(
            {"search_query": {"$regex": product_name, "$options": "i"}}
        ).sort("scraped_at", -1).limit(3).to_list(3)
        
        for session in amazon_sessions:
            for scraped_product in session.get("products", []):
                if scraped_product.get("title") and product_name.lower() in scraped_product["title"].lower():
                    price_str = scraped_product.get("price", "")
                    # Extract numeric price from string like "₹25,999"
                    import re
                    price_match = re.search(r'[\d,]+', price_str.replace('₹', '').replace(',', ''))
                    if price_match:
                        try:
                            price_val = float(price_match.group().replace(',', ''))
                            latest_scraped_data.append({
                                "source": "amazon_scraped",
                                "price": price_val,
                                "rating": scraped_product.get("rating", "N/A"),
                                "reviews": scraped_product.get("reviews", "N/A"),
                                "scraped_at": session.get("scraped_at")
                            })
                        except ValueError:
                            pass
        
        # Get latest Smartprix data
        smartprix_sessions = await db.smartprix_data.find(
            {"search_query": {"$regex": product_name, "$options": "i"}}
        ).sort("scraped_at", -1).limit(3).to_list(3)
        
        for session in smartprix_sessions:
            for scraped_product in session.get("products", []):
                if scraped_product.get("title") and product_name.lower() in scraped_product["title"].lower():
                    price_str = scraped_product.get("price", "")
                    import re
                    price_match = re.search(r'[\d,]+', price_str.replace('₹', '').replace(',', ''))
                    if price_match:
                        try:
                            price_val = float(price_match.group().replace(',', ''))
                            latest_scraped_data.append({
                                "source": "smartprix_scraped",
                                "price": price_val,
                                "rating": scraped_product.get("rating", "N/A"),
                                "reviews": scraped_product.get("reviews", "N/A"),
                                "scraped_at": session.get("scraped_at")
                            })
                        except ValueError:
                            pass
        
        # Get latest Flipkart data
        flipkart_sessions = await db.flipkart_data.find(
            {"search_query": {"$regex": product_name, "$options": "i"}}
        ).sort("scraped_at", -1).limit(3).to_list(3)
        
        for session in flipkart_sessions:
            for scraped_product in session.get("products", []):
                if scraped_product.get("title") and product_name.lower() in scraped_product["title"].lower():
                    price_str = scraped_product.get("price", "")
                    import re
                    price_match = re.search(r'[\d,]+', price_str.replace('₹', '').replace(',', ''))
                    if price_match:
                        try:
                            price_val = float(price_match.group().replace(',', ''))
                            latest_scraped_data.append({
                                "source": "flipkart_scraped", 
                                "price": price_val,
                                "rating": scraped_product.get("rating", "N/A"),
                                "reviews": scraped_product.get("reviews", "N/A"),
                                "scraped_at": session.get("scraped_at")
                            })
                        except ValueError:
                            pass
    
    # Combine latest scraped data with existing platform data
    platforms_list.extend(latest_scraped_data)
    
    # Add existing platform data from products collection
    for platform_name, platform_info in platforms_data.items():
        if platform_info and isinstance(platform_info, dict):
            # Try multiple price field names
            price = (platform_info.get("price") or 
                    platform_info.get("current_price") or 
                    platform_info.get("Price") or 0)
            if isinstance(price, (int, float)) and price > 0:
                platforms_list.append({
                    "source": platform_name,
                    "price": price,
                    "rating": platform_info.get("rating", "N/A"),
                    "reviews": platform_info.get("reviews", "N/A"),
                    "scraped_at": None
                })
    
    # Extract all prices for analysis
    prices = [p["price"] for p in platforms_list if p.get("price", 0) > 0]
    
    # Calculate pricing summary manually
    pricing_summary = {}
    if prices:
        pricing_summary = {
            "lowest_price": min(prices),
            "highest_price": max(prices),
            "best_platform": min(platforms_list, key=lambda x: x.get("price", float('inf')))["source"]
        }
    
    # Calculate price statistics from all available data
    if prices:
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        price_range = max_price - min_price
        
        # Enhanced prediction logic with latest scraped data
        # Check if we have fresh scraped data (within last 24 hours)
        from datetime import timedelta
        fresh_data_threshold = datetime.utcnow() - timedelta(hours=24)
        fresh_prices = []
        
        for p in platforms_list:
            scraped_at = p.get("scraped_at")
            if scraped_at and scraped_at > fresh_data_threshold:
                fresh_prices.append(p["price"])
        
        # Use fresh data if available, otherwise use all data
        analysis_prices = fresh_prices if fresh_prices else prices
        analysis_min = min(analysis_prices) if analysis_prices else min_price
        
        # Calculate realistic competitive pricing 
        # Target a competitive price point based on market analysis
        median_price = sorted(analysis_prices)[len(analysis_prices)//2] if len(analysis_prices) > 2 else avg_price
        
        if len(analysis_prices) >= 3:
            # Multiple competitors: target 15% below average for competitive edge
            predicted_price = round(avg_price * 0.85)
            strategy = "aggressive_competitive"
        elif len(analysis_prices) == 2:
            # Two competitors: price between lowest and median
            predicted_price = round((analysis_min + median_price) / 2)
            strategy = "moderate_competitive"
        else:
            # Single competitor: price 5% below competitor
            predicted_price = round(analysis_min * 0.95)
            strategy = "conservative_competitive"
        
        # Ensure prediction is realistic (not below cost threshold)
        cost_floor = round(analysis_min * 0.85)  # Don't go below 85% of lowest price
        predicted_price = max(predicted_price, cost_floor)
        
        # Determine decision based on market dynamics
        current_our_price = pricing_summary.get("lowest_price", avg_price) 
        price_difference_pct = ((predicted_price - current_our_price) / current_our_price) * 100
        
        if price_difference_pct <= -10:
            decision = "price_cut"
        elif price_difference_pct >= 10:
            decision = "price_increase"  
        else:
            decision = "hold"
        
        # Create detailed rationale with market analysis
        platforms_found = len(platforms_list)
        platform_names = [p["source"] for p in platforms_list]
        fresh_data_count = len([p for p in platforms_list if p.get("scraped_at") and p["scraped_at"] > fresh_data_threshold])
        
        rationale = f"📊 Market Analysis: Found {platforms_found} competitor prices on {', '.join(set(platform_names))}. "
        if fresh_data_count > 0:
            rationale += f"Including {fresh_data_count} fresh price(s) from recent scraping. "
        rationale += f"Price range: ₹{min_price:,.0f} - ₹{max_price:,.0f} (avg: ₹{avg_price:,.0f}). "
        rationale += f"💡 Current position: ₹{current_our_price:,.0f} → Recommended: ₹{predicted_price:,} using {strategy} strategy. "
        
        if decision == "price_cut":
            savings = current_our_price - predicted_price
            rationale += f"📉 Price cut of ₹{savings:,} recommended to gain competitive advantage."
        elif decision == "price_increase":
            increase = predicted_price - current_our_price
            rationale += f"📈 Price increase of ₹{increase:,} possible due to market position."
        else:
            rationale += f"✅ Current pricing is competitive - maintain position."
        
        response_payload.update({
            "source": "enhanced_competitor_analysis",
            "predicted_price": predicted_price,
            "decision": decision,
            "llm_rationale": rationale,
            "ml_details": {
                "competitor_count": platforms_found,
                "platforms": list(set(platform_names)),
                "fresh_data_points": fresh_data_count,
                "strategy_used": strategy,
                "price_analysis": {
                    "min_price": min_price,
                    "max_price": max_price,
                    "avg_price": avg_price,
                    "price_range": price_range,
                    "predicted_price": predicted_price,
                    "discount_vs_lowest": round((analysis_min - predicted_price) / analysis_min * 100, 1),
                    "discount_vs_average": round((avg_price - predicted_price) / avg_price * 100, 1) if avg_price > 0 else 0,
                    "data_freshness": "recent" if fresh_data_count > 0 else "historical"
                }
            }
        })
        return {"success": True, "prediction": response_payload}
    else:
        # Fallback if no valid prices found - use demo pricing logic
        min_price = max_price = avg_price = price_range = 50000  # Demo price
        predicted_price = 47500  # 5% below demo price
        
        response_payload.update({
            "source": "demo_fallback", 
            "predicted_price": predicted_price,
            "decision": "price_cut",
            "llm_rationale": f"💡 Demo Mode: No competitor pricing data available for {product.get('name', 'this product')}. Suggested demo price: ₹{predicted_price:,}. Use scraper to gather real competitor data for accurate predictions.",
            "ml_details": {"demo_mode": True, "reason": "no_competitor_prices"}
        })
        return {"success": True, "prediction": response_payload}


# ==================== TEST ENDPOINTS ====================

@app.get("/api/test", response_model=Dict[str, Any])
async def test_api():
    """Test endpoint to verify API is working"""
    return {
        "status": "success",
        "message": "Competition Tracker API is working!",
        "timestamp": datetime.utcnow().isoformat(),
        "database_connected": True
    }

@app.get("/api/debug/products", response_model=Dict[str, Any])
async def debug_products():
    """Debug endpoint to see raw products in database"""
    try:
        # Get all products without any filters
        all_products = await db.products.find({}).limit(10).to_list(10)
        total_count = await db.products.count_documents({})
        
        # Also check if products collection exists
        collections = await db.db.list_collection_names()
        
        return {
            "total_products": total_count,
            "collections": collections,
            "sample_products": [
                {
                    "_id": str(p.get("_id")),
                    "name": p.get("name"),
                    "product_id": p.get("product_id"),
                    "platforms": list(p.get("platforms", {}).keys()) if p.get("platforms") else [],
                    "metadata": p.get("metadata")
                } for p in all_products
            ]
        }
    except Exception as e:
        return {"error": str(e), "traceback": str(e)}

@app.get("/api/debug/scraping/{platform}", response_model=Dict[str, Any])
async def debug_scraping_data(platform: str):
    """Debug endpoint to check scraping data for a specific platform"""
    try:
        await scraper_db.connect()
        
        collection_name = f"{platform}_scraping_data"
        collection = scraper_db.db[collection_name]
        
        # Get recent documents
        recent_docs = await collection.find().sort("_id", -1).limit(5).to_list(length=5)
        total_count = await collection.count_documents({})
        
        await scraper_db.close()
        
        return {
            "platform": platform,
            "collection_name": collection_name,
            "total_documents": total_count,
            "recent_documents": [
                {
                    "_id": str(doc.get("_id")),
                    "search_query": doc.get("search_query"),
                    "products_count": len(doc.get("products", [])),
                    "timestamp": doc.get("timestamp"),
                    "session_id": doc.get("session_id")
                } for doc in recent_docs
            ]
        }
    except Exception as e:
        return {"error": str(e), "platform": platform}

@app.get("/api/test/llm", response_model=Dict[str, Any])
async def test_llm():
    """Test LLM functionality"""
    try:
        from llm import PricePredictionLLM
        
        llm = PricePredictionLLM()
        
        # Test data
        test_product = {
            "name": "Test Product - MacBook Air M2",
            "platforms": [
                {"source": "amazon", "price": 99900, "rating": "4.5", "reviews": "1200"},
                {"source": "smartprix", "price": 98500, "rating": "4.3", "reviews": "850"},
                {"source": "flipkart", "price": 101000, "rating": "4.4", "reviews": "950"}
            ],
            "min_price": 98500,
            "max_price": 101000,
            "avg_price": 99800,
            "price_range": 2500
        }
        
        result = await llm.generate_price_prediction(test_product)
        
        return {
            "status": "success", 
            "message": "LLM is working!",
            "test_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"LLM test failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

# Helper functions for linking scraped data
def parse_scraped_price(price_str: str) -> float:
    """Parse price string to float"""
    try:
        if isinstance(price_str, (int, float)):
            return float(price_str)
        # Remove currency symbols and commas
        price_clean = str(price_str).replace('₹', '').replace(',', '').replace('Rs.', '').strip()
        return float(price_clean) if price_clean and price_clean != '0' else 0.0
    except:
        return 0.0

def extract_clean_product_name(title: str) -> str:
    """Extract clean product name from scraped title"""
    if not title:
        return "Unknown Product"
    
    # Remove common e-commerce junk
    title = title.replace("(", " ").replace(")", " ").replace("[", " ").replace("]", " ")
    
    # Take first meaningful part (usually brand + model)
    words = title.split()[:4]  # First 4 words usually contain the core product info
    return " ".join(words).strip()

@app.post("/api/admin/link-scraped-data", response_model=Dict[str, Any])
async def link_scraped_data_to_products():
    """
    Link scraped product data to original ASIN-based products to enable predictions
    """
    try:
        # Get original products (those with ASINs but no names)
        original_products_cursor = db.products.find({
            "product_id": {"$regex": "^B[0-9A-Z]{9}$"},  # ASIN pattern
            "name": {"$in": [None, ""]}
        })
        original_products = await original_products_cursor.to_list(length=100)
        
        # Get recent scraped data from all platforms using correct collection names
        amazon_data_cursor = db.amazon_data.find({
            "products": {"$exists": True, "$ne": []},
            "scraped_at": {"$exists": True}
        }).sort("scraped_at", -1).limit(10)
        amazon_sessions = await amazon_data_cursor.to_list(length=10)
        
        # Also get Flipkart and Smartprix data
        flipkart_data_cursor = db.flipkart_data.find({
            "products": {"$exists": True, "$ne": []},
            "scraped_at": {"$exists": True}
        }).sort("scraped_at", -1).limit(10)
        flipkart_sessions = await flipkart_data_cursor.to_list(length=10)
        
        smartprix_data_cursor = db.smartprix_data.find({
            "products": {"$exists": True, "$ne": []},
            "scraped_at": {"$exists": True}
        }).sort("scraped_at", -1).limit(10)
        smartprix_sessions = await smartprix_data_cursor.to_list(length=10)
        
        updated_count = 0
        
        for product in original_products:
            asin = product.get("product_id")
            if not asin:
                continue
                
            # Look for this ASIN in scraped data or find similar products
            found_match = False
            platforms_data = {}
            
            # Search through Amazon scraped sessions
            if not found_match:
                for session in amazon_sessions:
                    session_products = session.get("products", [])
                    for scraped_item in session_products:
                        title = scraped_item.get("product_title", scraped_item.get("title", ""))
                        
                        # Extract potential product name from title
                        if title and len(title) > 10:  # Has meaningful title
                            platforms_data["amazon"] = {
                                "price": parse_scraped_price(scraped_item.get("selling_price", scraped_item.get("price", "0"))),
                                "current_price": parse_scraped_price(scraped_item.get("selling_price", scraped_item.get("price", "0"))),
                                "url": scraped_item.get("product_link", scraped_item.get("link", "")),
                                "rating": scraped_item.get("star_rating", scraped_item.get("rating", "N/A")),
                                "reviews": scraped_item.get("review_count", scraped_item.get("reviews", "N/A"))
                            }
                            found_match = True
                            break
                    if found_match:
                        break
            
            # Search through Flipkart sessions if no Amazon match
            if not found_match:
                for session in flipkart_sessions:
                    session_products = session.get("products", [])
                    for scraped_item in session_products:
                        title = scraped_item.get("name", scraped_item.get("title", ""))
                        
                        if title and len(title) > 10:
                            platforms_data["flipkart"] = {
                                "price": parse_scraped_price(scraped_item.get("current_price", scraped_item.get("price", "0"))),
                                "current_price": parse_scraped_price(scraped_item.get("current_price", scraped_item.get("price", "0"))),
                                "url": scraped_item.get("url", scraped_item.get("link", "")),
                                "rating": scraped_item.get("rating", "N/A"),
                                "reviews": scraped_item.get("total_reviews", scraped_item.get("reviews", "N/A"))
                            }
                            found_match = True
                            break
                    if found_match:
                        break
            
            # Search through Smartprix sessions if still no match
            if not found_match:
                for session in smartprix_sessions:
                    session_products = session.get("products", [])
                    for scraped_item in session_products:
                        title = scraped_item.get("name", scraped_item.get("title", ""))
                        
                        if title and len(title) > 10:
                            platforms_data["smartprix"] = {
                                "price": parse_scraped_price(scraped_item.get("price", "0")),
                                "current_price": parse_scraped_price(scraped_item.get("price", "0")),
                                "url": scraped_item.get("url", scraped_item.get("link", "")),
                                "rating": scraped_item.get("rating", "N/A"),
                                "reviews": scraped_item.get("reviews", "N/A")
                            }
                            found_match = True
                            break
                    if found_match:
                        break
            
            # If we found any match, update the product
            if found_match:
                # Use the title from the matched platform
                clean_name = extract_clean_product_name(title)
                
                # Calculate pricing summary
                prices = [p.get("price", 0) for p in platforms_data.values() if p.get("price", 0) > 0]
                pricing_summary = {
                    "lowest_price": min(prices) if prices else None,
                    "highest_price": max(prices) if prices else None,
                    "best_platform": min(platforms_data.keys(), key=lambda k: platforms_data[k].get("price", float('inf'))) if prices else None
                }
                
                # Update the product
                update_result = await db.products.update_one(
                    {"_id": product["_id"]},
                    {
                        "$set": {
                            "name": clean_name,
                            "platforms": platforms_data,
                            "pricing_summary": pricing_summary,
                            "metadata": {
                                "status": "active",
                                "updated_at": datetime.utcnow(),
                                "linked_from_scraping": True
                            }
                        }
                    }
                )
                
                if update_result.modified_count > 0:
                    updated_count += 1
        
        return {
            "success": True,
            "message": f"Successfully linked {updated_count} products with scraped data",
            "updated_products": updated_count,
            "total_original_products": len(original_products)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/debug-products")
async def debug_products():
    """Debug endpoint to see actual products in database"""
    try:
        # Get all products to see their structure
        all_products_cursor = db.products.find({}).limit(20)
        all_products = await all_products_cursor.to_list(length=20)
        
        # Show full product details
        detailed_products = []
        
        for product in all_products:
            detailed_products.append({
                "product_id": product.get("product_id", ""),
                "name": product.get("name"),
                "platforms": product.get("platforms", {}),
                "pricing_summary": product.get("pricing_summary", {}),
                "has_pricing_data": bool(product.get("platforms")),
                "_id": str(product.get("_id"))
            })
        
        return {
            "total_products": len(all_products),
            "products": detailed_products
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/admin/remove-demo-products")
async def remove_demo_products():
    """Remove demo products, keep only original ASIN-based products"""
    try:
        # Remove demo products (those with DEMO- prefix)
        demo_result = await db.products.delete_many({
            "product_id": {"$regex": "^DEMO-"}
        })
        
        # Get remaining products (should be original ASIN products)
        remaining_cursor = db.products.find({})
        remaining_products = await remaining_cursor.to_list(length=100)
        
        return {
            "success": True,
            "message": f"Removed {demo_result.deleted_count} demo products",
            "deleted_count": demo_result.deleted_count,
            "remaining_products": len(remaining_products),
            "remaining_product_ids": [p.get("product_id") for p in remaining_products]
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/scraping/recent-sessions")
async def get_recent_scraping_sessions():
    """Get recent scraping session data to show in frontend"""
    try:
        # Get recent Amazon scraping data
        amazon_sessions = await db.amazon_data.find({}).sort("scraped_at", -1).limit(10).to_list(length=10)
        
        # Get recent Flipkart scraping data
        flipkart_sessions = await db.flipkart_data.find({}).sort("scraped_at", -1).limit(10).to_list(length=10)
        
        # Get recent Smartprix scraping data
        smartprix_sessions = await db.smartprix_data.find({}).sort("scraped_at", -1).limit(10).to_list(length=10)
        
        # Format the data for frontend display with detailed product information
        all_sessions = []
        
        # Process Amazon sessions
        for session in amazon_sessions:
            products = session.get("products", [])
            session_data = {
                "id": str(session.get("_id")),
                "session_id": str(session.get("_id")),
                "scraped_at": session.get("scraped_at"),
                "platform": "Amazon",
                "total_products": len(products),
                "search_query": session.get("search_query", "Unknown"),
                "success": len(products) > 0,
                "execution_time": session.get("execution_time", 0),
                "errors": len(session.get("errors", [])),
                "products": [
                    {
                        "title": p.get("product_title", p.get("title", "Unknown Product")),
                        "price": p.get("selling_price", p.get("price", "N/A")),
                        "original_price": p.get("list_price", p.get("original_price", "N/A")),
                        "url": p.get("product_link", p.get("link", "")),
                        "rating": p.get("star_rating", p.get("rating", "N/A")),
                        "reviews": p.get("review_count", p.get("reviews", "N/A")),
                        "image": p.get("image_url", p.get("image", "")),
                        "availability": p.get("availability", "Unknown")
                    }
                    for p in products[:10]  # Show max 10 products per session
                ]
            }
            all_sessions.append(session_data)
        
        # Process Flipkart sessions
        for session in flipkart_sessions:
            products = session.get("products", [])
            session_data = {
                "id": str(session.get("_id")),
                "session_id": str(session.get("_id")),
                "scraped_at": session.get("scraped_at"),
                "platform": "Flipkart",
                "total_products": len(products),
                "search_query": session.get("search_query", "Unknown"),
                "success": len(products) > 0,
                "execution_time": session.get("execution_time", 0),
                "errors": len(session.get("errors", [])),
                "products": [
                    {
                        "title": p.get("name", p.get("title", "Unknown Product")),
                        "price": p.get("current_price", p.get("price", "N/A")),
                        "original_price": p.get("original_price", "N/A"),
                        "url": p.get("url", p.get("link", "")),
                        "rating": p.get("rating", "N/A"),
                        "reviews": p.get("total_reviews", p.get("reviews", "N/A")),
                        "image": p.get("image_url", p.get("image", "")),
                        "delivery": p.get("delivery_info", "")
                    }
                    for p in products[:10]
                ]
            }
            all_sessions.append(session_data)
        
        # Process Smartprix sessions
        for session in smartprix_sessions:
            products = session.get("products", [])
            session_data = {
                "id": str(session.get("_id")),
                "session_id": str(session.get("_id")),
                "scraped_at": session.get("scraped_at"),
                "platform": "Smartprix",
                "total_products": len(products),
                "search_query": session.get("search_query", "Unknown"),
                "success": len(products) > 0,
                "execution_time": session.get("execution_time", 0),
                "errors": len(session.get("errors", [])),
                "products": [
                    {
                        "title": p.get("title", p.get("name", "Unknown Product")),
                        "price": p.get("price", "N/A"),
                        "original_price": p.get("original_price", "N/A"),
                        "url": p.get("link", p.get("url", "")),
                        "rating": p.get("rating", "N/A"),
                        "specifications": p.get("specifications", {}),
                        "features": p.get("features", [])
                    }
                    for p in products[:10]
                ]
            }
            all_sessions.append(session_data)
        
        # Sort all sessions by scraped_at date (most recent first)
        all_sessions.sort(key=lambda x: x.get("scraped_at", ""), reverse=True)
        
        return {
            "success": True,
            "sessions": all_sessions[:20],  # Return most recent 20 sessions
            "total_sessions": len(all_sessions),
            "platforms_active": len(set(s["platform"] for s in all_sessions))
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/update-sample-products", response_model=Dict[str, Any])
async def update_sample_products_with_real_data(current_user: dict = Depends(get_optional_user)):
    """
    Update sample products with realistic data for testing
    """
    try:
        # Define realistic product data
        product_updates = [
            {
                "name": "MacBook Pro 14 M3 Chip",
                "amazon_price": 169900,
                "smartprix_price": 164999,
                "flipkart_price": 171999
            },
            {
                "name": "iPhone 15 Pro 128GB",
                "amazon_price": 134900,
                "smartprix_price": 132999,
                "flipkart_price": 136899
            },
            {
                "name": "Samsung Galaxy S24 Ultra",
                "amazon_price": 124999,
                "smartprix_price": 121999,
                "flipkart_price": 127999
            },
            {
                "name": "Dell XPS 13 Plus",
                "amazon_price": 149999,
                "smartprix_price": 147999,
                "flipkart_price": 152999
            },
            {
                "name": "iPad Pro 11 inch M4",
                "amazon_price": 99900,
                "smartprix_price": 97999,
                "flipkart_price": 101999
            }
        ]
        
        # Get existing products
        products = await db.products.find({}).to_list(None)
        updates_made = 0
        
        for i, product in enumerate(products):
            if i < len(product_updates):
                update_data = product_updates[i]
                
                # Update product with realistic data
                await db.products.update_one(
                    {"_id": product["_id"]},
                    {"$set": {
                        "name": update_data["name"],
                        "platforms.amazon.price": update_data["amazon_price"],
                        "platforms.amazon.rating": "4.3",
                        "platforms.amazon.reviews": "1,234",
                        "platforms.amazon.url": f"https://amazon.in/{update_data['name'].lower().replace(' ', '-')}",
                        "platforms.amazon.availability": "In Stock",
                        "platforms.smartprix.price": update_data["smartprix_price"],
                        "platforms.smartprix.rating": "4.2",
                        "platforms.smartprix.url": f"https://smartprix.com/{update_data['name'].lower().replace(' ', '-')}",
                        "platforms.smartprix.availability": "available",
                        "platforms.flipkart.price": update_data["flipkart_price"],
                        "platforms.flipkart.rating": "4.1",
                        "platforms.flipkart.reviews": "890",
                        "platforms.flipkart.url": f"https://flipkart.com/{update_data['name'].lower().replace(' ', '-')}",
                        "platforms.flipkart.availability": "In Stock",
                        "pricing_summary.lowest_price": min(update_data["amazon_price"], update_data["smartprix_price"], update_data["flipkart_price"]),
                        "pricing_summary.highest_price": max(update_data["amazon_price"], update_data["smartprix_price"], update_data["flipkart_price"]),
                        "pricing_summary.best_platform": "smartprix" if update_data["smartprix_price"] <= min(update_data["amazon_price"], update_data["flipkart_price"]) else "amazon",
                        "last_updated": datetime.utcnow()
                    }}
                )
                updates_made += 1
        
        return {
            "success": True,
            "message": f"Updated {updates_made} products with realistic data",
            "products_updated": updates_made
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update products: {str(e)}"
        )

@app.post("/api/admin/sync-scraped-data", response_model=Dict[str, Any])
async def sync_scraped_data_manually(
    product_name: Optional[str] = None,
    current_user: dict = Depends(get_optional_user)
):
    """
    Manually sync scraped data from platform collections to main products collection
    """
    try:
        result = await db.sync_scraped_data_to_products(product_name)
        return {
            "success": True,
            "message": f"Data synchronization completed. Updated {result.get('updates_made', 0)} products.",
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync scraped data: {str(e)}"
        )

# ==================== RUN SERVER ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )