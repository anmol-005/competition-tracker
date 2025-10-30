import asyncio
from urllib.parse import quote
import json
import os

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# Import database utilities
from scraper_db_utils import db_manager

async def scrape_smartprix(product_name: str, max_items: int = 10):
    """
    Deploys a Digital Spy to scrape product intelligence from Smartprix.
    """
    print(f"🕵️  Deploying Digital Spy for: '{product_name}' on Smartprix...")
    search_url = f"https://www.smartprix.com/products/?q={quote(product_name)}"
    
    browser_cfg = BrowserConfig(headless=False)

    schema = {
        "name": "SmartprixIntelligence",
        "baseSelector": "div.sm-product",
        "fields": [
            {"name": "title", "selector": "a.name h2", "type": "text"},
            {"name": "price", "selector": "span.price", "type": "text"},
            {"name": "score", "selector": "div.score b", "type": "text"},
            # ⭐ FIX: Grab the entire spec block as a single text chunk
            {"name": "specs_text", "selector": "ul.sm-feat.specs", "type": "text"},
            {"name": "link", "selector": "a.name", "type": "attribute", "attribute": "href"}
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema)
    run_cfg = CrawlerRunConfig(extraction_strategy=extraction_strategy)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=search_url, config=run_cfg)

    if not result or not result.extracted_content or result.extracted_content.strip() in ("[]", ""):
        debug_filename = "smartprix_spy_blocked.html"
        with open(debug_filename, "w", encoding="utf-8") as f:
            f.write(result.html if result else "No HTML content received.")
        print(f"❌ Spy was blocked or no results found. Saved raw HTML to '{debug_filename}'.")
        return []

    try:
        items = json.loads(result.extracted_content)
    except json.JSONDecodeError:
        print("  -> ❌ Failed to decode the gathered intelligence.")
        return []

    cleaned_report = []
    print("\n📝 Cleaning and compiling the intelligence report...")
    
    # Clean the product name by removing quotes and extra spaces
    clean_product_name = product_name.strip().strip('"').strip("'")
    search_keywords = [word.lower() for word in clean_product_name.split()]
    
    # Separate brand and model keywords for better filtering
    brand_keyword = search_keywords[0] if search_keywords else ""
    other_keywords = search_keywords[1:] if len(search_keywords) > 1 else []
    
    print(f"  -> Filtering for brand '{brand_keyword}' and keywords: {other_keywords}")

    for it in items:
        title = it.get("title", "").strip()
        if not title:
            continue
        
        title_lower = title.lower()
        
        # Check if brand keyword is present
        if brand_keyword and brand_keyword not in title_lower:
            continue
            
        # Check if other keywords are present
        if other_keywords and not all(keyword in title_lower for keyword in other_keywords):
            continue
        
        link = it.get("link")
        if link and link.startswith("/"):
            link = "https://www.smartprix.com" + link
            
        # ⭐ FIX: Split the raw specs text into a clean list
        specs_list = []
        specs_raw_text = it.get("specs_text", "")
        if specs_raw_text:
            # Split by newline and remove any empty lines
            specs_list = [spec.strip() for spec in specs_raw_text.split('\n') if spec.strip()]

        cleaned_report.append({
            "product_title": title,
            "price": it.get("price"),
            "user_score": it.get("score"),
            "key_specs": specs_list, # Use the new, cleaned list
            "product_link": link
        })
        
        if len(cleaned_report) >= max_items:
            break

    print("  -> ✅ Report compiled.")
    return cleaned_report


class SmartprixScraper:
    """Async context manager that can scrape individual Smartprix product pages.

    Designed to be used with `async with SmartprixScraper() as scraper:` from
    `backend_api.py`. Exposes `scrape_product(url)` which returns a dict with
    a `success` boolean and product payload on success.
    """

    def __init__(self, headless: bool = True):
        self.browser_cfg = BrowserConfig(headless=headless)
        self.crawler = None

    async def __aenter__(self):
        self.crawler = AsyncWebCrawler(config=self.browser_cfg)
        await self.crawler.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc, tb)

    async def scrape_product(self, product_url: str) -> dict:
        """Scrape a single Smartprix product page and return a structured dict.

        Returns: {"success": bool, "product": {...}} or {"success": False, "error": "..."}
        """
        if not product_url:
            return {"success": False, "error": "No URL provided"}

        # Define a forgiving schema that captures typical product page fields
        schema = {
            "name": "SmartprixProduct",
            "fields": [
                {"name": "product_title", "selector": "h1, h1[itemprop='name']", "type": "text"},
                {"name": "price", "selector": "span.price, .price, [data-price]", "type": "text"},
                {"name": "user_score", "selector": "div.score b, .score b, .rating", "type": "text"},
                {"name": "specs_text", "selector": "ul.sm-feat.specs, .specs, ul.specs", "type": "text"},
                {"name": "image", "selector": "img.featured, img.product-image, img:first-of-type", "type": "attribute", "attribute": "src"},
                {"name": "link", "selector": "link[rel='canonical'], a[href*='smartprix.com']", "type": "attribute", "attribute": "href"}
            ]
        }

        extraction_strategy = JsonCssExtractionStrategy(schema)
        run_cfg = CrawlerRunConfig(extraction_strategy=extraction_strategy)

        try:
            result = await self.crawler.arun(url=product_url, config=run_cfg)

            if not result or not result.extracted_content or result.extracted_content.strip() in ("[]", ""):
                return {"success": False, "error": "No content extracted or crawler blocked"}

            items = json.loads(result.extracted_content)
            if not items:
                return {"success": False, "error": "No items extracted from product page"}

            raw = items[0]

            # Build product payload similar to CLI output
            title = raw.get("product_title", "").strip() if raw.get("product_title") else raw.get("title", "").strip()
            link = raw.get("link") or product_url
            if link and link.startswith("/"):
                link = "https://www.smartprix.com" + link

            specs_raw_text = raw.get("specs_text", "")
            specs_list = [s.strip() for s in specs_raw_text.split('\n') if s.strip()] if specs_raw_text else []

            product = {
                "product_title": title,
                "price": raw.get("price"),
                "user_score": raw.get("user_score"),
                "key_specs": specs_list,
                "product_link": link,
                "image": raw.get("image")
            }

            return {"success": True, "product": product}

        except Exception as e:
            return {"success": False, "error": str(e)}

async def save_report_to_database(report_data: list, search_query: str, filename="smartprix_intelligence_db.json"):
    """
    Save report to both MongoDB and JSON file (backup)
    """
    if not report_data:
        print("  -> No data to save.")
        return False
        
    print(f"\n💾 Saving report to MongoDB database...")
    
    # Connect to database and store data
    success = False
    try:
        if await db_manager.connect():
            success = await db_manager.store_smartprix_scraping_data(report_data, search_query)
            await db_manager.close()
            
            if success:
                print(f"  -> ✅ Report successfully saved to MongoDB database.")
            else:
                print(f"  -> ⚠️ Failed to save to MongoDB, saving to JSON backup instead.")
        else:
            print(f"  -> ⚠️ Database connection failed, saving to JSON backup instead.")
    except Exception as e:
        print(f"  -> ⚠️ Database error: {e}. Saving to JSON backup instead.")
    
    # Always save to JSON as backup
    print(f"\n💾 Saving backup to JSON file ('{filename}')...")
    database = []
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                database = json.load(f)
            except json.JSONDecodeError:
                database = []
    
    database.extend(report_data)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=4, ensure_ascii=False)
            
    print(f"  -> ✅ JSON backup saved successfully.")
    return True


async def main():
    """Main function to run Smartprix scraper with database integration"""
    try:
        query = input("Enter Product Name to spy on (e.g., 'Macbook M3', 'OnePlus Nord CE 5'): ")
        results = await scrape_smartprix(query)

        if results:
            print("\n--- 🕵️ SPY REPORT ---")
            for i, p in enumerate(results, 1):
                print(f"\n--- Item {i} ---")
                print(f"  Title: {p['product_title']}")
                print(f"  Price: {p['price']}")
                print(f"  User Score: {p['user_score']}")
                print(f"  Key Specs: {p['key_specs'][:4]}")
                print(f"  Link: {p['product_link']}")
            
            await save_report_to_database(results, query)

        else:
            print("\n--- End of Report: No relevant items found. ---")

    except KeyboardInterrupt:
        print("\n\n-- Operation aborted by user. --")

if __name__ == "__main__":
    asyncio.run(main())
