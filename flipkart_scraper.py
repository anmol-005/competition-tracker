import asyncio
from urllib.parse import quote
import json
import os

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# Import database utilities
from scraper_db_utils import db_manager

async def scrape_flipkart(product_name: str, max_items: int = 10, retries: int = 3):
    print(f"🕵️  Deploying Digital Spy for: '{product_name}' on Flipkart.com...")
    search_url = f"https://www.flipkart.com/search?q={quote(product_name)}"
    
    browser_cfg = BrowserConfig(
        headless=False,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    schema = {
        "name": "FlipkartIntelligence",
        "baseSelector": "div[data-id], div._13oc-S, div._1AtVbE",
        "fields": [
            {"name": "title", "selector": "div.KzDlHZ, a.IRpwTa, div._4rR01T, div.s1Q9rs", "type": "text"},
            {"name": "price", "selector": "div._30jeq3._1_WHN1, div._1_WHN1, div.Nx9bqj", "type": "text"},
            {"name": "original_price", "selector": "div.yRaY8j.ZYYwLA, div._3I9_wc._27UcVY, div._3auQ3N", "type": "text"},
            {"name": "discount", "selector": "div._3Ay6Sb._31Dcoz, div._3Ay6Sb, span._2Tpdn3", "type": "text"},
            {"name": "rating", "selector": "div._3LWZlK, div.XQDdHH, span._2_R_DZ", "type": "text"},
            {"name": "reviews", "selector": "span._2_R_DZ:last-child, span.Wphh3N", "type": "text"},
            {"name": "link", "selector": "a.IRpwTa, a._1fQZEK, a.s1Q9rs", "type": "attribute", "attribute": "href"},
            {"name": "image", "selector": "img._396cs4, img._2r_T1I", "type": "attribute", "attribute": "src"}
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema)
    run_cfg = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        delay_before_return_html=3,
        wait_for="css:div[data-id], div._13oc-S",
        js_code=[
            "window.scrollTo(0, document.body.scrollHeight/4);",
            "await new Promise(resolve => setTimeout(resolve, 2000));",
            "window.scrollTo(0, document.body.scrollHeight/2);"
        ]
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = None
        for attempt in range(1, retries + 1):
            print(f"  -> Spy is on attempt {attempt}/{retries}...")
            
            # Add random delay between attempts
            if attempt > 1:
                delay = attempt * 2
                print(f"  -> Waiting {delay} seconds before retry...")
                await asyncio.sleep(delay)
            
            result = await crawler.arun(url=search_url, config=run_cfg)

            if result and result.extracted_content and result.extracted_content.strip() not in ("[]", ""):
                print("  -> ✅ Intelligence gathered successfully!")
                break
            else:
                print(f"  -> ⚠️ Attempt {attempt} failed. Retrying...")
                # Check if we got HTML content (might be blocked page)
                if result and result.html:
                    print(f"  -> Received HTML content: {len(result.html)} characters")
                await asyncio.sleep(3)

    if not result or not result.extracted_content or result.extracted_content.strip() in ("[]", ""):
        debug_filename = "flipkart_spy_blocked.html"
        with open(debug_filename, "w", encoding="utf-8") as f:
            f.write(result.html if result else "No HTML content received.")
        print(f"❌ Spy was blocked. Saved raw HTML to '{debug_filename}' for inspection.")
        return []

    try:
        items = json.loads(result.extracted_content)
    except json.JSONDecodeError:
        print("  -> ❌ Failed to decode the gathered intelligence.")
        return []

    cleaned_report = []
    print("\n📝 Cleaning and compiling the intelligence report...")
    
    # ⭐ FINAL UPDATE: Brand-aware filtering logic
    # Clean the product name by removing quotes and extra spaces
    clean_product_name = product_name.strip().strip('"').strip("'")
    all_keywords = [word.lower() for word in clean_product_name.split()]
    
    # For products like "iPhone 15", we want to check for both "iphone" and "15"
    # The first word is assumed to be the brand (iPhone, MacBook, etc.)
    # The rest are model identifiers that should be present
    brand_keyword = all_keywords[0] if all_keywords else ""
    other_core_keywords = all_keywords[1:] if len(all_keywords) > 1 else []
    
    print(f"  -> Rule 1: Title must contain brand '{brand_keyword}' and keywords: {other_core_keywords}")

    EXCLUSION_KEYWORDS = [
        'protector', 'glass', 'case', 'cover', 'charger', 'cable', 
        'tempered', 'screen', 'guard', 'holder', 'stand', 'skin'
    ]
    print(f"  -> Rule 2: Title must NOT contain accessory words like {EXCLUSION_KEYWORDS[:3]}")


    for it in items:
        title = it.get("title", "").strip()
        if not title:
            continue
        
        title_lower = title.lower()

        # Rule 1: Check if brand and core keywords are in the title
        if brand_keyword and brand_keyword not in title_lower:
            print(f"  -> FILTERED OUT: '{title[:60]}...' (Missing brand keyword: {brand_keyword})")
            continue
            
        if other_core_keywords and not all(keyword in title_lower for keyword in other_core_keywords):
            missing_keywords = [k for k in other_core_keywords if k not in title_lower]
            print(f"  -> FILTERED OUT: '{title[:60]}...' (Missing keywords: {missing_keywords})")
            continue

        # Rule 2: Check if any accessory keywords are in the title
        if any(exclude_word in title_lower for exclude_word in EXCLUSION_KEYWORDS):
            print(f"  -> FILTERED OUT: '{title[:60]}...' (Is an accessory)")
            continue

        price = it.get("price", "").strip()
        original_price = it.get("original_price", "").strip()
        discount = it.get("discount", "").strip()
        
        link = it.get("link")
        if link and link.startswith("/"):
            link = "https://www.flipkart.com" + link

        cleaned_report.append({
            "product_title": title,
            "selling_price": price,
            "original_price_mrp": original_price,
            "discount_percentage": discount,
            "star_rating": (it.get("rating") or "N/A").strip(),
            "review_count": it.get("reviews", "N/A"),
            "product_link": link
        })
        
        if len(cleaned_report) >= max_items:
            break

    print("  -> ✅ Report compiled with relevant items.")
    return cleaned_report

async def save_report_to_database(report_data: list, search_query: str, filename="competitor_intelligence_db.json"):
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
            success = await db_manager.store_flipkart_scraping_data(report_data, search_query)
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
    """Main function to run Flipkart scraper with database integration"""
    try:
        query = input("Enter Product Name to spy on: ")
        results = await scrape_flipkart(query)

        if results:
            print("\n--- 🕵️ SPY REPORT ---")
            for i, p in enumerate(results, 1):
                print(f"\n--- Item {i} ---")
                print(f"  Title: {p['product_title']}")
                print(f"  Selling Price: {p['selling_price']}")
                if p['original_price_mrp']:
                    print(f"  ‼️ DISCOUNT DETECTED: Was {p['original_price_mrp']}")
                if p.get('discount_percentage'):
                    print(f"  💰 Discount: {p['discount_percentage']}")
                print(f"  Rating: {p['star_rating']}")
                print(f"  Reviews: {p['review_count']}")
                print(f"  Link: {p['product_link']}")
            
            await save_report_to_database(results, query)

        else:
            print("\n--- End of Report: No relevant items found or spy was blocked. ---")

    except KeyboardInterrupt:
        print("\n\n-- Operation aborted by user. --")

if __name__ == "__main__":
    asyncio.run(main())
