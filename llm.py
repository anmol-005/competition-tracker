import asyncio
import sys
import os
import google.generativeai as genai
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import List, Dict, Any
import json

# Load environment variables
load_dotenv()

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import DatabaseConfig

class PricePredictionLLM:
    def __init__(self):
        # Initialize Google AI with API key
        genai.configure(api_key=os.getenv("API"))
        
        # Use current available models from the API
        model_options = [
            'gemini-2.0-flash',  # Latest stable model
            'gemini-2.5-flash',  # Alternative stable model
            'gemini-flash-latest',  # Generic latest flash model
            'gemini-pro-latest'  # Generic latest pro model
        ]
        self.model = None
        
        for model_name in model_options:
            try:
                self.model = genai.GenerativeModel(model_name)
                print(f"✅ Using Google AI model: {model_name}")
                break
            except Exception as e:
                print(f"⚠️ Failed to initialize {model_name}: {e}")
                continue
        
        if self.model is None:
            print("❌ All Google AI models failed to initialize")
            self.model = None
        else:
            # Test model with a simple query
            self.test_model()
            
        # Initialize MongoDB connection
        self.db_config = DatabaseConfig()
        self.mongodb_uri = self.db_config.get_mongodb_url()
        self.database_name = self.db_config.DATABASE_NAME
        self.client = None
        self.db = None
    
    def test_model(self):
        """Test if the Google AI model is working with a simple query"""
        if self.model is None:
            return False
        
        try:
            response = self.model.generate_content("Say 'Hello' in one word.")
            if response and response.text:
                print("✅ Google AI model is working correctly!")
                return True
            else:
                print("⚠️ Google AI model initialized but not responding properly")
                return False
        except Exception as e:
            print(f"❌ Google AI model test failed: {e}")
            return False
    
    async def connect_to_database(self):
        """Connect to MongoDB database"""
        try:
            self.client = AsyncIOMotorClient(self.mongodb_uri)
            self.db = self.client[self.database_name]
            # Test connection
            await self.client.admin.command('ping')
            print("✅ Connected to MongoDB successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
    
    async def get_scraping_data(self) -> Dict[str, List[Dict]]:
        """Fetch latest scraping data from Amazon, Smartprix, and Flipkart collections"""
        try:
            # Get Amazon scraping data
            amazon_collection = self.db['amazon_scraping_data']
            amazon_data = await amazon_collection.find().sort("_id", -1).limit(10).to_list(length=10)
            
            # Get Smartprix scraping data  
            smartprix_collection = self.db['smartprix_scraping_data']
            smartprix_data = await smartprix_collection.find().sort("_id", -1).limit(10).to_list(length=10)
            
            # Get Flipkart scraping data
            flipkart_collection = self.db['flipkart_scraping_data']
            flipkart_data = await flipkart_collection.find().sort("_id", -1).limit(10).to_list(length=10)
            

            
            return {
                'amazon': amazon_data,
                'smartprix': smartprix_data,
                'flipkart': flipkart_data
            }
        except Exception as e:
            print(f"❌ Error fetching scraping data: {e}")
            return {'amazon': [], 'smartprix': [], 'flipkart': []}
    
    def extract_product_info(self, product: Dict, source: str) -> Dict[str, Any]:
        """Extract relevant product information for price prediction"""
        try:
            if source == 'amazon':
                return {
                    'name': product.get('product_title', product.get('name', 'Unknown Product')),
                    'price': self.extract_price(product.get('selling_price', '0')),
                    'rating': product.get('star_rating', 'N/A'),
                    'reviews': product.get('review_count', 'N/A'),
                    'source': 'Amazon',
                    'asin': product.get('asin', 'N/A')
                }
            elif source == 'smartprix':
                return {
                    'name': product.get('product_title', product.get('title', 'Unknown Product')),
                    'price': self.extract_price(product.get('price', '0')),
                    'rating': product.get('user_score', 'N/A'),
                    'source': 'Smartprix',
                    'url': product.get('product_link', 'N/A')
                }
            elif source == 'flipkart':
                return {
                    'name': product.get('product_title', 'Unknown Product'),
                    'price': self.extract_price(product.get('selling_price', '0')),
                    'rating': product.get('star_rating', 'N/A'),
                    'reviews': product.get('review_count', 'N/A'),
                    'source': 'Flipkart',
                    'url': product.get('product_link', 'N/A')
                }
        except Exception as e:

            return None
    
    def extract_price(self, price_str: str) -> float:
        """Extract numeric price from price string"""
        try:
            if isinstance(price_str, (int, float)):
                return float(price_str)
            
            # Remove currency symbols and commas
            price_clean = str(price_str).replace('₹', '').replace(',', '').replace('Rs.', '').replace(' ', '')
            
            # Extract first number found
            import re
            numbers = re.findall(r'\d+', price_clean)
            if numbers:
                return float(''.join(numbers[:2]))  # Handle prices like "1,23,456"
            return 0.0
        except:
            return 0.0
    
    def find_similar_products(self, amazon_data: List[Dict], smartprix_data: List[Dict], flipkart_data: List[Dict]) -> List[Dict]:
        """Find products that might be the same across different platforms"""
        similar_products = []
        
        # Process each platform's data separately
        platforms_data = {
            'amazon': [self.extract_product_info(p, 'amazon') for p in amazon_data],
            'smartprix': [self.extract_product_info(p, 'smartprix') for p in smartprix_data],
            'flipkart': [self.extract_product_info(p, 'flipkart') for p in flipkart_data]
        }
        
        # Clean data - remove None entries and zero prices
        for platform in platforms_data:
            platforms_data[platform] = [p for p in platforms_data[platform] if p and p['price'] > 0]
        

        
        # Process products for cross-platform matching
        
        # Find cross-platform matches
        processed_matches = set()
        
        # Compare Amazon products with other platforms
        for amazon_product in platforms_data['amazon']:
            amazon_name = amazon_product['name']
            amazon_key = amazon_name.lower()
            if amazon_key in processed_matches:
                continue
                
            current_match = {'platforms': [amazon_product], 'name': amazon_name}
            
            # Look for matches in Smartprix
            smartprix_found = False
            for smartprix_product in platforms_data['smartprix']:
                if self.is_similar_product(amazon_name, smartprix_product['name']):
                    current_match['platforms'].append(smartprix_product)
                    smartprix_found = True
                    break  # Only take first match from each platform
            
            # Look for matches in Flipkart
            flipkart_found = False
            for flipkart_product in platforms_data['flipkart']:
                if self.is_similar_product(amazon_name, flipkart_product['name']):
                    current_match['platforms'].append(flipkart_product)
                    flipkart_found = True
                    break  # Only take first match from each platform
            
            # ✅ RELAXED: Include if found on 1 or more platforms (was 2+)
            if len(current_match['platforms']) >= 1:
                # Calculate price statistics
                prices = [p['price'] for p in current_match['platforms']]
                current_match['min_price'] = min(prices)
                current_match['max_price'] = max(prices)
                current_match['price_range'] = max(prices) - min(prices)
                current_match['avg_price'] = sum(prices) / len(prices)
                current_match['platform_count'] = len(current_match['platforms'])
                
                similar_products.append(current_match)
                processed_matches.add(amazon_key)
        
        # Also check Smartprix products that weren't matched with Amazon
        for smartprix_product in platforms_data['smartprix']:
            smartprix_name = smartprix_product['name'].lower()
            if smartprix_name in processed_matches:
                continue
                
            current_match = {'platforms': [smartprix_product], 'name': smartprix_product['name']}
            
            # Look for matches in Flipkart only (Amazon already checked above)
            for flipkart_product in platforms_data['flipkart']:
                if self.is_similar_product(smartprix_name, flipkart_product['name'].lower()):
                    current_match['platforms'].append(flipkart_product)
                    break  # Only take first match
            
            # ✅ RELAXED: Include single-platform products to increase data availability
            if len(current_match['platforms']) >= 1:
                # Calculate price statistics
                prices = [p['price'] for p in current_match['platforms']]
                current_match['min_price'] = min(prices)
                current_match['max_price'] = max(prices)
                current_match['price_range'] = max(prices) - min(prices) if len(prices) > 1 else 0
                current_match['avg_price'] = sum(prices) / len(prices)
                current_match['platform_count'] = len(current_match['platforms'])
                
                similar_products.append(current_match)
                processed_matches.add(smartprix_name)
        
        # ✅ NEW: Also add single-platform products from Flipkart that weren't matched
        for flipkart_product in platforms_data['flipkart']:
            flipkart_name = flipkart_product['name'].lower()
            if flipkart_name not in processed_matches:
                current_match = {
                    'platforms': [flipkart_product], 
                    'name': flipkart_product['name'],
                    'min_price': flipkart_product['price'],
                    'max_price': flipkart_product['price'],
                    'price_range': 0,
                    'avg_price': flipkart_product['price'],
                    'platform_count': 1
                }
                similar_products.append(current_match)
                processed_matches.add(flipkart_name)
        
        # Sort products: 3-platform products first, then by price range (more interesting products first)
        similar_products.sort(key=lambda x: (-x['platform_count'], -x['price_range']))
        
        return similar_products
    
    def is_similar_product(self, name1: str, name2: str) -> bool:
        """Check if two product names represent similar products with flexible matching criteria"""
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        # Extract complete product specifications
        specs1 = self.extract_product_specs(name1_lower)
        specs2 = self.extract_product_specs(name2_lower)
        
        # ✅ RELAXED MATCHING: Multiple matching strategies
        
        # Strategy 1: Direct text similarity (for cases where specs extraction fails)
        if self._fuzzy_name_match(name1_lower, name2_lower):
            return True
        
        # Strategy 2: Brand and model matching (relaxed storage/RAM requirements)
        if specs1['brand'] and specs2['brand'] and specs1['model'] and specs2['model']:
            # Core match: same brand and model
            core_match = (
                specs1['brand'] == specs2['brand'] and
                specs1['model'] == specs2['model']
            )
            
            if core_match:
                # ✅ RELAXED: Storage matching is now optional
                storage_compatible = True
                if specs1['storage'] and specs2['storage']:
                    # Both have storage: must match
                    storage_compatible = specs1['storage'] == specs2['storage']
                # If only one has storage info, still consider compatible
                
                # ✅ RELAXED: RAM matching is now optional for laptops
                ram_compatible = True
                if (specs1['category'] == 'laptop' and specs2['category'] == 'laptop'):
                    if specs1['ram'] and specs2['ram']:
                        # Both have RAM: must match
                        ram_compatible = specs1['ram'] == specs2['ram']
                    # If only one has RAM info, still consider compatible
                
                return storage_compatible and ram_compatible
        
        # Strategy 3: Fallback brand-only matching for similar product families
        if specs1['brand'] and specs2['brand'] and specs1['brand'] == specs2['brand']:
            # Same brand: check if product names are very similar
            return self._brand_family_match(name1_lower, name2_lower, specs1['brand'])
        
        return False
    
    def _fuzzy_name_match(self, name1: str, name2: str) -> bool:
        """Check if product names are very similar using fuzzy matching"""
        # Remove common words that don't affect product identity
        stopwords = ['with', 'and', 'or', 'the', 'smartphone', 'mobile', 'phone', 'laptop', 'computer', 'pc']
        
        def clean_name(name):
            words = name.split()
            return ' '.join([w for w in words if w not in stopwords])
        
        clean1 = clean_name(name1)
        clean2 = clean_name(name2)
        
        # Calculate similarity ratio
        import difflib
        similarity = difflib.SequenceMatcher(None, clean1, clean2).ratio()
        
        # ✅ RELAXED: Consider 75% similarity as match (was 100% exact match)
        return similarity >= 0.75
    
    def _brand_family_match(self, name1: str, name2: str, brand: str) -> bool:
        """Check if products from same brand are similar enough"""
        # For same brand, check if they share key model identifiers
        if brand in ['apple', 'samsung', 'oneplus', 'xiaomi', 'google']:
            # Extract model numbers/names
            import re
            
            # Look for model numbers or identifiers
            model_patterns = [
                r'\b(\d+)\b',  # Numbers like 15, 14, 13
                r'\b(pro|plus|mini|ultra|max|air)\b',  # Variants
                r'\b([a-z]\d+)\b',  # Like S24, A54
            ]
            
            models1 = set()
            models2 = set()
            
            for pattern in model_patterns:
                models1.update(re.findall(pattern, name1))
                models2.update(re.findall(pattern, name2))
            
            # If they share any model identifiers, consider them similar
            return bool(models1.intersection(models2))
        
        # For other brands, use word overlap
        words1 = set(name1.split())
        words2 = set(name2.split())
        overlap = words1.intersection(words2)
        
        # ✅ RELAXED: 40% word overlap indicates similar products
        min_words = min(len(words1), len(words2))
        if min_words > 0:
            overlap_ratio = len(overlap) / min_words
            return overlap_ratio >= 0.4
        
        return False
    
    def extract_product_specs(self, product_name: str) -> dict:
        """Extract comprehensive product specifications for exact matching"""
        import re
        
        specs = {
            'brand': '',
            'model': '',
            'storage': '',
            'ram': '',
            'category': ''
        }
        
        name_lower = product_name.lower()
        
        # Brand detection with comprehensive patterns
        brand_patterns = {
            'apple': [r'\b(apple|iphone|ipad|macbook|airpods)\b'],
            'samsung': [r'\b(samsung|galaxy)\b'],
            'oneplus': [r'\b(oneplus|one\s*plus)\b'],
            'xiaomi': [r'\b(xiaomi|redmi|mi)\b'],
            'google': [r'\b(google|pixel)\b'],
            'oppo': [r'\b(oppo)\b'],
            'realme': [r'\b(realme)\b'],
            'vivo': [r'\b(vivo)\b'],
            'nothing': [r'\b(nothing)\b'],
            'asus': [r'\b(asus|rog)\b'],
            'hp': [r'\b(hp)\b'],
            'dell': [r'\b(dell)\b'],
            'lenovo': [r'\b(lenovo|thinkpad)\b']
        }
        
        # Find brand
        for brand, patterns in brand_patterns.items():
            for pattern in patterns:
                if re.search(pattern, name_lower):
                    specs['brand'] = brand
                    break
            if specs['brand']:
                break
        
        # Model extraction based on brand
        if specs['brand'] == 'apple':
            # iPhone models: iPhone 15, iPhone 14 Pro, etc.
            iphone_match = re.search(r'iphone\s*(\d+)(?:\s*(pro|plus|mini))?', name_lower)
            if iphone_match:
                model = f"iphone {iphone_match.group(1)}"
                if iphone_match.group(2):
                    model += f" {iphone_match.group(2)}"
                specs['model'] = model
                specs['category'] = 'phone'
            
            # MacBook models: MacBook Air M3, MacBook Pro M2, etc.
            macbook_match = re.search(r'macbook\s*(air|pro)?\s*(m\d+)?', name_lower)
            if macbook_match:
                model = "macbook"
                if macbook_match.group(1):
                    model += f" {macbook_match.group(1)}"
                if macbook_match.group(2):
                    model += f" {macbook_match.group(2)}"
                specs['model'] = model
                specs['category'] = 'laptop'
            
            # iPad models
            ipad_match = re.search(r'ipad(?:\s*(air|pro|mini))?(?:\s*(\d+))?', name_lower)
            if ipad_match:
                model = "ipad"
                if ipad_match.group(1):
                    model += f" {ipad_match.group(1)}"
                if ipad_match.group(2):
                    model += f" {ipad_match.group(2)}"
                specs['model'] = model
                specs['category'] = 'tablet'
        
        elif specs['brand'] == 'samsung':
            # Galaxy models: Galaxy S24, Galaxy Note 20, Galaxy A54, etc.
            galaxy_match = re.search(r'galaxy\s*([a-z]+\s*\d+)(?:\s*(plus|ultra|fe))?', name_lower)
            if galaxy_match:
                model = f"galaxy {galaxy_match.group(1)}"
                if galaxy_match.group(2):
                    model += f" {galaxy_match.group(2)}"
                specs['model'] = model
                specs['category'] = 'phone'
        
        elif specs['brand'] == 'oneplus':
            # OnePlus models: OnePlus 12, OnePlus Nord 3, etc.
            oneplus_match = re.search(r'(?:oneplus|one\s*plus)\s*(\w+(?:\s*\d+)?)', name_lower)
            if oneplus_match:
                specs['model'] = f"oneplus {oneplus_match.group(1)}"
                specs['category'] = 'phone'
        
        elif specs['brand'] == 'xiaomi':
            # Xiaomi/Redmi models: Xiaomi 14, Redmi Note 13, etc.
            xiaomi_match = re.search(r'(xiaomi|redmi|mi)\s*(\w+(?:\s*\d+)?)', name_lower)
            if xiaomi_match:
                brand_variant = xiaomi_match.group(1)
                model_num = xiaomi_match.group(2)
                specs['model'] = f"{brand_variant} {model_num}"
                specs['category'] = 'phone'
        
        elif specs['brand'] == 'google':
            # Pixel models: Pixel 8, Pixel 7 Pro, etc.
            pixel_match = re.search(r'pixel\s*(\d+)(?:\s*(pro|xl))?', name_lower)
            if pixel_match:
                model = f"pixel {pixel_match.group(1)}"
                if pixel_match.group(2):
                    model += f" {pixel_match.group(2)}"
                specs['model'] = model
                specs['category'] = 'phone'
        
        # Storage extraction - more comprehensive patterns
        storage_patterns = [
            r'(\d+)\s*tb',  # 1TB, 2TB, etc.
            r'(\d+)\s*gb',  # 128GB, 256GB, 512GB, etc.
        ]
        
        for pattern in storage_patterns:
            match = re.search(pattern, name_lower)
            if match:
                size = match.group(1)
                unit = 'tb' if 'tb' in pattern else 'gb'
                specs['storage'] = f"{size}{unit}"
                break
        
        # RAM extraction for laptops
        if specs['category'] == 'laptop':
            ram_patterns = [
                r'(\d+)\s*gb\s*(ram|memory|unified)',
                r'(\d+)\s*gb.*?(ram|memory)',
            ]
            
            for pattern in ram_patterns:
                match = re.search(pattern, name_lower)
                if match:
                    specs['ram'] = f"{match.group(1)}gb"
                    break
        
        return specs

    def extract_storage(self, product_name: str) -> str:
        """Extract storage capacity from product name"""
        import re
        
        # Look for storage patterns: 128GB, 256 GB, 512gb, 1TB, 1 TB, etc.
        storage_patterns = [
            r'(\d+)\s*tb',  # 1TB, 2TB, etc.
            r'(\d+)\s*gb',  # 128GB, 256GB, 512GB, etc.
        ]
        
        name_lower = product_name.lower()
        
        for pattern in storage_patterns:
            match = re.search(pattern, name_lower)
            if match:
                size = match.group(1)
                unit = 'tb' if 'tb' in pattern else 'gb'
                return f"{size}{unit}"
        
        return ""
    
    def extract_ram(self, product_name: str) -> str:
        """Extract RAM capacity from product name (for laptops)"""
        import re
        
        name_lower = product_name.lower()
        
        # Look for RAM patterns: 8GB RAM, 16 GB Memory, 24GB Unified Memory, etc.
        ram_patterns = [
            r'(\d+)\s*gb\s*(ram|memory|unified)',
            r'(\d+)\s*gb.*?(ram|memory)',
        ]
        
        for pattern in ram_patterns:
            match = re.search(pattern, name_lower)
            if match:
                return f"{match.group(1)}gb"
        
        return ""
    
    def _extract_price_from_ai_response(self, ai_text: str, product_data: Dict) -> int:
        """Extract recommended price from AI response text"""
        import re
        
        # Look for price patterns in the AI response
        price_patterns = [
            r'₹([\d,]+)',  # ₹1,23,456
            r'Rs\.?\s*([\d,]+)',  # Rs. 123456 or Rs 123456
            r'rupees?\s*([\d,]+)',  # rupees 123456
            r'price.*?(\d[\d,]+)',  # price: 123456
            r'recommend.*?(\d[\d,]+)',  # recommend 123456
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, ai_text, re.IGNORECASE)
            for match in matches:
                try:
                    # Clean and convert to int
                    price_str = match.replace(',', '')
                    price = int(float(price_str))
                    # Validate price is reasonable
                    if 100 <= price <= 10000000:  # Between ₹100 and ₹1 crore
                        return price
                except (ValueError, TypeError):
                    continue
        
        # If no valid price found in AI text, use fallback
        return int(product_data['min_price'] * 0.95)
    
    async def generate_price_prediction(self, product_data: Dict) -> Dict[str, Any]:
        """Generate price prediction using Google AI"""
        platforms = product_data['platforms']
        product_name = product_data['name']
        
        # Estimate cost (70% of lowest competitor price)
        estimated_cost = product_data['min_price'] * 0.7
        
        # Fallback manual analysis if AI model is not available
        if not self.model:
            recommended_price = int(product_data['min_price'] * 0.95)
            return {
                "predicted_price": recommended_price,
                "decision": "price_cut" if recommended_price < product_data['avg_price'] else "hold",
                "llm_rationale": f"⚠️ AI Model Not Available - Manual Analysis: Recommended ₹{recommended_price:,} (5% below lowest competitor ₹{product_data['min_price']:,} while maintaining healthy margins above estimated cost ₹{estimated_cost:,.0f})",
                "source": "manual_fallback",
                "product_name": product_name,
                "price_range": {
                    "min": product_data['min_price'],
                    "max": product_data['max_price'],
                    "avg": product_data['avg_price']
                }
            }
        
        try:
            
            # Build platform data for prompt
            platform_info = ""
            for platform in platforms:
                platform_info += f"- {platform['source']} Price: ₹{platform['price']:,.0f}"
                if platform.get('rating') and platform.get('rating') != 'N/A':
                    platform_info += f" | Rating: {platform['rating']}"
                if platform.get('reviews') and platform.get('reviews') != 'N/A':
                    platform_info += f" | Reviews: {platform['reviews']}"
                platform_info += "\n"
            
            prompt = f"""
            Multi-Platform Product Analysis for Price Optimization:
            
            Product: {product_name}
            
            Current Market Data Across Platforms:
            {platform_info}
            
            Price Analysis:
            - Lowest Price: ₹{product_data['min_price']:,.0f}
            - Highest Price: ₹{product_data['max_price']:,.0f}
            - Price Range: ₹{product_data['price_range']:,.0f}
            - Average Price: ₹{product_data['avg_price']:,.0f}
            - Estimated Cost: ₹{estimated_cost:,.0f}
            - Available on {len(platforms)} platforms: {', '.join([p['source'] for p in platforms])}
            
            Based on this comprehensive multi-platform market data, suggest an optimal selling price that:
            1. Ensures profitability (above cost)
            2. Remains competitive across all platforms
            3. Considers market positioning
            4. Maximizes profit margins
            
            Provide the recommended price in rupees with brief reasoning (max 3 lines).
            """
            
            # Try API call with improved error handling
            try:
                response = self.model.generate_content(prompt)
                if response and response.text:
                    # Parse AI response to extract recommended price
                    ai_text = response.text
                    recommended_price = self._extract_price_from_ai_response(ai_text, product_data)
                    
                    return {
                        "predicted_price": recommended_price,
                        "decision": "price_cut" if recommended_price < product_data['avg_price'] else "hold",
                        "llm_rationale": f"🤖 AI Recommendation: {ai_text[:200]}..." if len(ai_text) > 200 else f"🤖 AI Recommendation: {ai_text}",
                        "source": "google_ai",
                        "product_name": product_name,
                        "price_range": {
                            "min": product_data['min_price'],
                            "max": product_data['max_price'], 
                            "avg": product_data['avg_price']
                        }
                    }
                else:
                    # Handle empty response - fallback to manual analysis
                    pass
            except Exception as api_error:
                error_msg = str(api_error)
                if "429" in error_msg or "Resource exhausted" in error_msg:
                    # Rate limit - try once more after brief pause
                    import time
                    time.sleep(1)
                    try:
                        response = self.model.generate_content(prompt)
                        if response and response.text:
                            ai_text = response.text
                            recommended_price = self._extract_price_from_ai_response(ai_text, product_data)
                            return {
                                "predicted_price": recommended_price,
                                "decision": "price_cut" if recommended_price < product_data['avg_price'] else "hold", 
                                "llm_rationale": f"🤖 AI Recommendation (Retry): {ai_text[:200]}..." if len(ai_text) > 200 else f"🤖 AI Recommendation: {ai_text}",
                                "source": "google_ai_retry"
                            }
                    except:
                        pass  # Fall through to manual analysis
            
            # If all API attempts failed, provide manual analysis
            recommended_price = int(product_data['min_price'] * 0.95)
            return {
                "predicted_price": recommended_price,
                "decision": "price_cut" if recommended_price < product_data['avg_price'] else "hold",
                "llm_rationale": f"⚠️ AI Model temporarily unavailable - Manual Analysis: Recommended ₹{recommended_price:,} (5% below lowest competitor). Positioned just below the lowest market price to ensure competitive advantage while maintaining healthy profit margins above estimated cost ₹{estimated_cost:,.0f}.",
                "source": "manual_api_fallback",
                "product_name": product_name,
                "price_range": {
                    "min": product_data['min_price'],
                    "max": product_data['max_price'],
                    "avg": product_data['avg_price']
                }
            }
            
        except Exception as e:
            print(f"❌ Critical error in prediction: {e}")
            # Emergency fallback
            emergency_price = int(product_data.get('min_price', 1000) * 0.98)
            return {
                "predicted_price": emergency_price,
                "decision": "error",
                "llm_rationale": f"❌ Error generating prediction for {product_name}: {str(e)}. Emergency fallback price: ₹{emergency_price:,}",
                "source": "error_fallback",
                "product_name": product_name,
                "error": str(e)
            }
    
    async def run_price_analysis(self):
        """Main function to run price analysis"""
        print("🚀 Starting Price Prediction Analysis...")
        print("=" * 50)
        
        # Connect to database
        if not await self.connect_to_database():
            return
        
        # Get scraping data
        scraping_data = await self.get_scraping_data()
        
        if not scraping_data['amazon'] and not scraping_data['smartprix'] and not scraping_data['flipkart']:
            print("❌ No scraping data found. Please run scrapers first.")
            return
        
        # Find similar products across all three sources
        similar_products = self.find_similar_products(
            scraping_data['amazon'], 
            scraping_data['smartprix'],
            scraping_data['flipkart']
        )
        
        if not similar_products:
            print("❌ No similar products found across platforms.")
            print("💡 Try running scrapers to get comparable product data.")
            return
        
        # ✅ IMPROVED: Separate products by platform count (now including single-platform)
        three_platform_products = [p for p in similar_products if p['platform_count'] == 3]
        two_platform_products = [p for p in similar_products if p['platform_count'] == 2]
        single_platform_products = [p for p in similar_products if p['platform_count'] == 1]
        
        # ✅ RELAXED: Accept any products for analysis (was requiring 2+ platforms)
        if not three_platform_products and not two_platform_products and not single_platform_products:
            print("❌ No products found for analysis.")
            print("💡 Try running all scrapers to get more comprehensive data.")
            return
        
        print(f"📊 RELAXED MATCHING RESULTS:")
        if three_platform_products:
            print(f"🌟 {len(three_platform_products)} products on ALL 3 platforms")
        if two_platform_products:
            print(f"🔵 {len(two_platform_products)} products on 2 platforms")
        if single_platform_products:
            print(f"🟡 {len(single_platform_products)} products on single platforms")
        print(f"✅ Total analyzable products: {len(similar_products)}")
        print("=" * 60)
        
        # ✅ IMPROVED: Process products in priority order but include single-platform
        products_to_analyze = []
        if three_platform_products:
            products_to_analyze.extend(three_platform_products[:3])  # Top 3 three-platform products
        if two_platform_products and len(products_to_analyze) < 5:
            remaining_slots = 5 - len(products_to_analyze)
            products_to_analyze.extend(two_platform_products[:remaining_slots])
        if single_platform_products and len(products_to_analyze) < 5:
            remaining_slots = 5 - len(products_to_analyze)
            products_to_analyze.extend(single_platform_products[:remaining_slots])
            products_to_analyze.extend(two_platform_products[:remaining_slots])
        
        # Generate predictions for selected products
        for i, product in enumerate(products_to_analyze, 1):
            platform_badge = "🌟 3-Platform" if product['platform_count'] == 3 else "🔵 2-Platform"
            print(f"\n{platform_badge} Product #{i}")
            print(f"Product: {product['name']}")
            
            # Display prices from all platforms
            for platform in product['platforms']:
                rating_info = f" | Rating: {platform['rating']}" if platform.get('rating') and platform['rating'] != 'N/A' else ""
                reviews_info = f" | Reviews: {platform['reviews']}" if platform.get('reviews') and platform['reviews'] != 'N/A' else ""
                print(f"{platform['source']}: ₹{platform['price']:,.0f}{rating_info}{reviews_info}")
            
            print(f"Price Range: ₹{product['price_range']:,.0f} (₹{product['min_price']:,.0f} - ₹{product['max_price']:,.0f})")
            print(f"Average Price: ₹{product['avg_price']:,.0f}")
            platform_list = ', '.join([p['source'] for p in product['platforms']])
            print(f"Available on: {product['platform_count']} platforms ({platform_list})")
            
            print("\n🤖 AI Price Recommendation:")
            prediction = await self.generate_price_prediction(product)
            print(prediction)
            print("=" * 60)
        
        # Close database connection
        if self.client:
            self.client.close()
            print("\n🔌 Database connection closed")

# Main execution
async def main():
    llm = PricePredictionLLM()
    await llm.run_price_analysis()

if __name__ == "__main__":
    asyncio.run(main())


