import asyncio
from urllib.parse import quote
import json
import os

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def scrape_amazon(product_name: str, max_items: int = 10, retries: int = 3):
    print(f"🕵️  Deploying Digital Spy for: '{product_name}' on Amazon.in...")
    search_url = f"https://www.amazon.in/s?k={quote(product_name)}"
    
    browser_cfg = BrowserConfig(headless=False)

    schema = {
        "name": "AmazonIntelligence",
        "baseSelector": "div.s-main-slot div[data-component-type='s-search-result']",
        "fields": [
            {"name": "title", "selector": "a h2 span", "type": "text"},
            {"name": "price_whole", "selector": "span.a-price-whole", "type": "text"},
            {"name": "price_fraction", "selector": "span.a-price-fraction", "type": "text"},
            {"name": "list_price", "selector": "span.a-price.a-text-price span.a-offscreen", "type": "text"},
            {"name": "rating", "selector": "span.a-icon-alt", "type": "text"},
            {"name": "reviews", "selector": "span.a-size-base.s-underline-text", "type": "text"},
            {"name": "link", "selector": "a.a-link-normal.s-no-outline", "type": "attribute", "attribute": "href"}
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema)
    run_cfg = CrawlerRunConfig(extraction_strategy=extraction_strategy)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = None
        for attempt in range(1, retries + 1):
            print(f"  -> Spy is on attempt {attempt}/{retries}...")
            result = await crawler.arun(url=search_url, config=run_cfg)

            if result and result.extracted_content and result.extracted_content.strip() not in ("[]", ""):
                print("  -> ✅ Intelligence gathered successfully!")
                break
            else:
                print(f"  -> ⚠️ Attempt {attempt} failed. Retrying...")
                await asyncio.sleep(3)

    if not result or not result.extracted_content or result.extracted_content.strip() in ("[]", ""):
        debug_filename = "amazon_spy_blocked.html"
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
    all_keywords = [word.lower() for word in product_name.split()]
    
    # The first word is assumed to be the brand and might be missing from the title.
    # The rest of the non-numeric words are the *true* core keywords.
    other_core_keywords = [k for k in all_keywords[1:] if not k.isnumeric()]
    
    print(f"  -> Rule 1: Title must contain these keywords: {other_core_keywords}")

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

        # Rule 1: Check if ALL *other* core keywords are in the title
        if not all(keyword in title_lower for keyword in other_core_keywords):
            print(f"  -> FILTERED OUT: '{title[:60]}...' (Missing a core keyword)")
            continue

        # Rule 2: Check if any accessory keywords are in the title
        if any(exclude_word in title_lower for exclude_word in EXCLUSION_KEYWORDS):
            print(f"  -> FILTERED OUT: '{title[:60]}...' (Is an accessory)")
            continue

        price = None
        if it.get("price_whole"):
            frac = it.get("price_fraction", "")
            price = it["price_whole"] + (("." + frac) if frac else "")
        
        link = it.get("link")
        if link and link.startswith("/"):
            link = "https://www.amazon.in" + link

        cleaned_report.append({
            "product_title": title,
            "selling_price": price,
            "original_price_mrp": it.get("list_price"),
            "star_rating": it.get("rating", "N/A").strip(),
            "review_count": it.get("reviews", "N/A"),
            "product_link": link
        })
        
        if len(cleaned_report) >= max_items:
            break

    print("  -> ✅ Report compiled with relevant items.")
    return cleaned_report

def save_report_to_database(report_data: list, filename="competitor_intelligence_db.json"):
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
        query = input("Enter Product Name to spy on: ")
        results = asyncio.run(scrape_amazon(query))

        if results:
            print("\n--- 🕵️ SPY REPORT ---")
            for i, p in enumerate(results, 1):
                print(f"\n--- Item {i} ---")
                print(f"  Title: {p['product_title']}")
                print(f"  Selling Price: {p['selling_price']}")
                if p['original_price_mrp']:
                    print(f"  ‼️ DISCOUNT DETECTED: Was {p['original_price_mrp']}")
                print(f"  Rating: {p['star_rating']}")
                print(f"  Reviews: {p['review_count']}")
                print(f"  Link: {p['product_link']}")
            
            save_report_to_database(results)

        else:
            print("\n--- End of Report: No relevant items found or spy was blocked. ---")

    except KeyboardInterrupt:
        print("\n\n-- Operation aborted by user. --")