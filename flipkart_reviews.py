import asyncio
import json
import os
import re

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# Import database utilities
from scraper_db_utils import db_manager


async def scrape_product_name(url: str, retries: int = 3) -> str:
    """
    Scrapes just the product name from the review page.
    """
    print("\n🕵️  Extracting product name...")
    browser_cfg = BrowserConfig(headless=False)
    
    # This schema is designed to find the single product title on the page.
    schema = {
        "name": "ProductName",
        "baseSelector": "body", # Look at the whole page
        "fields": [
            # Multiple selectors for product name - Flipkart changes these frequently
            {"name": "product_name", "selector": "div.Vu3-9u, span.B_NuCI, h1.x-product-title-label, span._35KyD6", "type": "text"},
        ]
    }
    extraction_strategy = JsonCssExtractionStrategy(schema)
    run_cfg = CrawlerRunConfig(extraction_strategy=extraction_strategy)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for attempt in range(1, retries + 1):
            result = await crawler.arun(url=url, config=run_cfg)
            if result and result.extracted_content and result.extracted_content.strip() not in ("[]", ""):
                try:
                    # The result is a list with one item: [{'product_name': 'The Name'}]
                    data = json.loads(result.extracted_content)
                    if data and data[0].get("product_name"):
                        print(f"  -> ✅ Product Name Found: '{data[0]['product_name']}'")
                        return data[0]['product_name']
                except (json.JSONDecodeError, IndexError):
                    continue # Try again on failure
    
    print("  -> ⚠️ Could not extract product name.")
    return "Unknown Product"


async def scrape_flipkart_reviews(url: str, max_reviews: int = 10, retries: int = 3):
    """
    Scrapes product reviews from a single Flipkart URL using the crawl4ai library.
    """
    print(f"🕵️  Deploying scraper for Flipkart URL: {url[:70]}...")
    
    browser_cfg = BrowserConfig(headless=False)

    schema = {
        "name": "FlipkartReviews",
        "baseSelector": "div._1AtVbE, div.EKFha-, div._16PBlm",
        "fields": [
            {"name": "rating", "selector": "div.XQDdHH, div._3LWZlK, div.hGSR34 div._3LWZlK", "type": "text"},
            {"name": "summary", "selector": "p.z9E0IG, p._2-N8zT, div._2-N8zT", "type": "text"},
            {"name": "text", "selector": "div.ZmyHeo div div, div.t-ZTKy div div, div._16PBlm div", "type": "text"},
            {"name": "name", "selector": "p._2NsDsF.AwS1CA, p._2sc7ZR._2V5EHH, div._2V5EHH", "type": "text"}
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema)
    run_cfg = CrawlerRunConfig(extraction_strategy=extraction_strategy)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = None
        for attempt in range(1, retries + 1):
            print(f"  -> Scraper is on attempt {attempt}/{retries}...")
            result = await crawler.arun(url=url, config=run_cfg)

            if result and result.extracted_content and result.extracted_content.strip() not in ("[]", ""):
                print("  -> ✅ Reviews gathered successfully!")
                break
            else:
                print(f"  -> ⚠️ Attempt {attempt} failed. Retrying...")
                await asyncio.sleep(3)

    if not result or not result.extracted_content or result.extracted_content.strip() in ("[]", ""):
        debug_filename = "flipkart_scraper_blocked.html"
        with open(debug_filename, "w", encoding="utf-8") as f:
            f.write(result.html if result else "No HTML content received.")
        print(f"❌ Scraper was blocked or found no content. Saved raw HTML to '{debug_filename}' for inspection.")
        return []

    try:
        reviews = json.loads(result.extracted_content)
    except json.JSONDecodeError:
        print("  -> ❌ Failed to decode the gathered review data.")
        return []

    print(f"\n📝 Found {len(reviews)} reviews on this page.")
    return reviews[:max_reviews]

async def save_report_to_database(product_report: dict, filename="flipkart_reviews_db.json"):
    """
    Save report to both MongoDB and JSON file (backup)
    """
    if not product_report or not product_report.get("reviews"):
        print("\nNo new data to save.")
        return False
        
    print(f"\n💾 Saving report to MongoDB database...")
    
    # Connect to database and store data
    success = False
    try:
        if await db_manager.connect():
            success = await db_manager.store_flipkart_reviews_data(product_report)
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
    
    # Add the new product report to our list of products
    database.append(product_report)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=4, ensure_ascii=False)
            
    print(f"  -> ✅ JSON backup saved successfully. Total product reports in DB: {len(database)}")
    return True

async def main():
    """
    Main function to orchestrate the scraping of multiple pages for a single product.
    """
    user_url = input("Enter the Flipkart product review URL: ")
    
    if not user_url or "flipkart.com" not in user_url:
        print("❌ Invalid Flipkart URL provided. Exiting.")
        return

    pid_match = re.search(r"pid=([A-Z0-9]+)", user_url)
    if not pid_match:
        print("❌ Could not find a Product ID (pid) in the URL. Exiting.")
        return
    product_id = pid_match.group(1)

    base_product_review_url = user_url.split('&page=')[0]
    print(f"✅ Using base URL for scraping: {base_product_review_url}")
    
    # Scrape the product name once from the first page
    product_name = await scrape_product_name(base_product_review_url)

    pages_to_scrape = 3
    all_reviews = []

    for page_num in range(1, pages_to_scrape + 1):
        page_url = f"{base_product_review_url}&page={page_num}"
        print(f"\n--- Scraping Page {page_num} of {pages_to_scrape} ---")
        
        results = await scrape_flipkart_reviews(page_url)
        if results:
            all_reviews.extend(results)
        else:
            print(f"No reviews found on page {page_num}. This might be the last page.")
            break
        
        if page_num < pages_to_scrape:
            await asyncio.sleep(2)

    if all_reviews:
        # Create a structured report for this product
        product_report = {
            "product_id": product_id,
            "product_name": product_name,
            "reviews": all_reviews
        }

        print("\n--- 📊 FLIPKART REVIEW REPORT ---")
        print(f"Product: {product_report['product_name']} (ID: {product_report['product_id']})")
        print(f"--- Total Reviews Scraped: {len(all_reviews)} ---")
        
        # Save the single, structured report to the database file
        await save_report_to_database(product_report)
    else:
        print("\n--- End of Report: No reviews found or scraping failed. ---")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n-- Operation aborted by user. --")

