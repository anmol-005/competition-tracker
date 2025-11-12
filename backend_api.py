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
from fastapi.security import OAuth2PasswordBearer
from mail import send_price_alert

# Initialize FastAPI app
app = FastAPI(
    title="Competition Tracker API",
    description="REST API for Competition Tracker - E-commerce Intelligence Platform",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],  # React/Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Database instance
db = CompetitionTrackerDB()

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
    """Get current authenticated user from JWT token"""
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
        raise credentials_exception
    
    user = await db.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user

# ==================== STARTUP/SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await db.setup_database()
    print("🚀 Competition Tracker API Started!")
    print(f"📊 Database: {db.db.name}")
    print(f"🌐 CORS Origins: {app.middleware[0].allow_origins}")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await db.close()
    print("👋 Competition Tracker API Stopped!")

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
    current_user: dict = Depends(get_current_user)
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
    current_user: dict = Depends(get_current_user)
):
    """Get detailed product information"""
    result = await db.get_product_details_for_frontend(product_id)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result

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

@app.get("/send-alert")
def trigger_price_alert():
    """Endpoint that triggers sending the email."""
    try:
        send_price_alert()
        return {"success": True, "message": "Email sent successfully!"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== SCRAPING ENDPOINTS ====================

@app.post("/api/scraping/amazon", response_model=Dict[str, Any])
async def trigger_amazon_scraping(
    request: ScrapingRequest,
    current_user: dict = Depends(get_current_user)
):
    """Trigger Amazon scraping"""
    if request.platform != "amazon":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid platform for this endpoint"
        )
    
    if not request.search_terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search terms are required for Amazon scraping"
        )
    
    try:
        # Import and run Amazon scraper
        from amazon_scraper import scrape_amazon
        
        results = {
            "search_terms": request.search_terms,
            "total_products": 0,
            "products": [],
            "errors": [],
            "success": True,
            "execution_time": 0
        }
        
        start_time = datetime.utcnow()
        
        for search_term in request.search_terms:
            try:
                scraper_result = await scrape_amazon(search_term, max_items=10)
                if scraper_result and scraper_result.get("products"):
                    results["products"].extend(scraper_result["products"])
                    results["total_products"] += len(scraper_result["products"])
            except Exception as e:
                results["errors"].append(f"Error scraping '{search_term}': {str(e)}")
        
        results["execution_time"] = (datetime.utcnow() - start_time).total_seconds()
        
        # Store results in database
        session_id = await db.store_amazon_scraping_data(results)
        
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
    current_user: dict = Depends(get_current_user)
):
    """Trigger Smartprix scraping"""
    if request.platform != "smartprix":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid platform for this endpoint"
        )
    
    if not request.product_urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product URLs are required for Smartprix scraping"
        )
    
    try:
        # Import and run Smartprix scraper
        from smartprix_scraper import SmartprixScraper
        
        results = {
            "product_urls": request.product_urls,
            "total_products": 0,
            "products": [],
            "errors": [],
            "success": True,
            "execution_time": 0
        }
        
        start_time = datetime.utcnow()
        
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
        
        results["execution_time"] = (datetime.utcnow() - start_time).total_seconds()
        
        # Store results in database
        session_id = await db.store_smartprix_scraping_data(results)
        
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

@app.post("/api/scraping/flipkart-reviews", response_model=Dict[str, Any])
async def trigger_flipkart_reviews_scraping(
    request: Dict[str, str],  # {"product_url": "flipkart_url"}
    current_user: dict = Depends(get_current_user)
):
    """Trigger Flipkart reviews scraping"""
    product_url = request.get("product_url")
    
    if not product_url or "flipkart.com" not in product_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid Flipkart product URL is required"
        )
    
    try:
        # Import and run Flipkart reviews scraper
        from flipkart_reviews import scrape_flipkart_reviews, scrape_product_name
        import re
        
        # Extract product ID
        pid_match = re.search(r"pid=([A-Z0-9]+)", product_url)
        if not pid_match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not find Product ID in URL"
            )
        
        product_id = pid_match.group(1)
        
        # Scrape product name and reviews
        product_name = await scrape_product_name(product_url)
        
        all_reviews = []
        pages_to_scrape = 3
        
        for page_num in range(1, pages_to_scrape + 1):
            page_url = f"{product_url.split('&page=')[0]}&page={page_num}"
            reviews = await scrape_flipkart_reviews(page_url, max_reviews=10)
            
            if reviews:
                all_reviews.extend(reviews)
            else:
                break  # No more reviews
        
        # Store results in database
        reviews_data = {
            "product_id": product_id,
            "product_name": product_name,
            "reviews": all_reviews,
            "scraping_url": product_url,
            "pages_scraped": min(page_num, pages_to_scrape)
        }
        
        session_id = await db.store_flipkart_reviews_data(reviews_data)
        
        return {
            "message": "Flipkart reviews scraping completed",
            "session_id": session_id,
            "product_name": product_name,
            "total_reviews": len(all_reviews),
            "pages_scraped": reviews_data["pages_scraped"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reviews scraping failed: {str(e)}"
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
    current_user: dict = Depends(get_current_user)
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

    try:
        # 2) Try to import and run your LLM wrapper
        # PricePredictionLLM is defined in llm.py (see llm.py file). :contentReference[oaicite:4]{index=4}
        from llm import PricePredictionLLM

        llm = PricePredictionLLM()
        # If your LL M requires DB connect, it has connect_to_database() — handle if needed
        try:
            # try to initialize/connect if method exists
            if hasattr(llm, "connect_to_database"):
                await llm.connect_to_database()
        except Exception:
            # non-fatal - continue if connection is unnecessary
            pass

        # The llm class in your repo calls generate_price_prediction(product) in examples.
        if hasattr(llm, "generate_price_prediction"):
            # make sure we pass a minimal product payload expected by the LLM
            llm_input = {
                "name": product.get("name"),
                "platforms": product.get("platforms", {}),
                "pricing_summary": product.get("pricing_summary", {})
            }
            # call it and expect an awaitable result
            ml_result = await llm.generate_price_prediction(llm_input)
            # Normalize result into response_payload
            response_payload.update({
                "source": "llm",
                "predicted_price": ml_result.get("predicted_price") if isinstance(ml_result, dict) else ml_result,
                "decision": ml_result.get("decision") if isinstance(ml_result, dict) else None,
                "llm_rationale": ml_result.get("llm_rationale") if isinstance(ml_result, dict) else str(ml_result),
                "ml_details": ml_result
            })
            return {"success": True, "prediction": response_payload}
        else:
            # No generate_price_prediction method — fall through to heuristic
            raise RuntimeError("LLM class exists but no 'generate_price_prediction' method found")

    except Exception as e:
        # If LLM fails, do a quick heuristic fallback so the frontend always gets something useful
        tb = traceback.format_exc()
        # quick heuristic: predicted = round(0.98 * competitor_avg) or current price if no competitor data
        try:
            # collect competitor numeric prices from platforms
            platform_prices = []
            for p_name, p in (product.get("platforms") or {}).items():
                price = p.get("price") or p.get("current_price") or None
                if isinstance(price, (int, float)):
                    platform_prices.append(float(price))
            competitor_avg = (sum(platform_prices) / len(platform_prices)) if platform_prices else None

            our_price = product.get("pricing_summary", {}).get("lowest_price")
            if competitor_avg:
                predicted = round(competitor_avg * 0.98)
            elif our_price:
                predicted = our_price
            else:
                predicted = None

            decision = None
            if predicted and our_price:
                decision = "price_cut" if predicted < our_price else "hold"

            llm_rationale = (
                f"Fallback heuristic used. Competitor average: "
                f"₹{competitor_avg:.2f}." if competitor_avg else "Fallback heuristic used: insufficient competitor data."
            )

            response_payload.update({
                "source": "heuristic",
                "predicted_price": predicted,
                "decision": decision,
                "llm_rationale": llm_rationale,
                "ml_details": {"error": str(e), "traceback": tb}
            })
            return {"success": True, "prediction": response_payload, "warning": "LLM failed, used heuristic fallback."}
        except Exception as e2:
            # final fallback error
            return {"success": False, "error": "Prediction failed", "details": str(e2), "traceback": tb}


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