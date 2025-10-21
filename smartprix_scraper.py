import asyncio
from urllib.parse import quote
import json
import os

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

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
    
    search_keywords = [word.lower() for word in product_name.split()]

    for it in items:
        title = it.get("title", "").strip()
        if not title:
            continue
        
        if not all(keyword in title.lower() for keyword in search_keywords):
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

def save_report_to_database(report_data: list, filename="smartprix_intelligence_db.json"):
    if not report_data:
        print("  -> No data to save.")
        return
        
    print(f"\n💾 Saving report to our intelligence database ('{filename}')...")
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
            
    print(f"  -> ✅ Report successfully saved.")


if __name__ == "__main__":
    try:
        query = input("Enter Product Name to spy on (e.g., 'Macbook M3', 'OnePlus Nord CE 5'): ")
        results = asyncio.run(scrape_smartprix(query))

        if results:
            print("\n--- 🕵️ SPY REPORT ---")
            for i, p in enumerate(results, 1):
                print(f"\n--- Item {i} ---")
                print(f"  Title: {p['product_title']}")
                print(f"  Price: {p['price']}")
                print(f"  User Score: {p['user_score']}")
                print(f"  Key Specs: {p['key_specs'][:4]}")
                print(f"  Link: {p['product_link']}")
            
            save_report_to_database(results)

        else:
            print("\n--- End of Report: No relevant items found. ---")

    except KeyboardInterrupt:
        print("\n\n-- Operation aborted by user. --")
