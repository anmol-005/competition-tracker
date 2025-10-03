import asyncio
from urllib.parse import quote
import json

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def scrape_amazon(product_name: str, max_items: int = 5, retries: int = 3):
    search_url = f"https://www.amazon.in/s?k={quote(product_name)}"
    browser_cfg = BrowserConfig(headless=False) 

    schema = {
        "name": "AmazonSearchResult",
        "baseSelector": "div.s-main-slot div[data-component-type='s-search-result']",
        "fields": [
            # This selector is more robust. It looks for the text within any <span>
            # that is inside an <a>, which is a direct child of an <h2>.
            {"name": "title", "selector": "h2 a span.a-text-normal", "type": "text"},
            
            {"name": "price_whole", "selector": "span.a-price-whole", "type": "text"},
            {"name": "price_fraction", "selector": "span.a-price-fraction", "type": "text"},
            {"name": "rating", "selector": "span.a-icon-alt", "type": "text"},
            {"name": "reviews", "selector": "span.a-size-base.s-underline-text", "type": "text"},
            {"name": "link", "selector": "a.a-link-normal.s-no-outline", "type": "attribute", "attribute": "href"}
        ]
    }



    extraction_strategy = JsonCssExtractionStrategy(schema)
    run_cfg = CrawlerRunConfig(extraction_strategy=extraction_strategy)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for attempt in range(1, retries + 1):
            result = await crawler.arun(url=search_url, config=run_cfg)

            if result.extracted_content and result.extracted_content.strip() not in ("[]", ""):
                break
            else:
                print(f"⚠️ Attempt {attempt} failed. Retrying...")
                await asyncio.sleep(3)

        if not result.extracted_content or result.extracted_content.strip() in ("[]", ""):
            with open("amazon_debug.html", "w", encoding="utf-8") as f:
                f.write(result.html)
            print("❌ Still blocked. Saved raw HTML to amazon_debug.html for inspection.")
            return []

    # Parse extracted JSON
    try:
        items = json.loads(result.extracted_content)
    except Exception:
        items = []

    cleaned = []
    for it in items[:max_items]:
        price = None
        if it.get("price_whole"):
            frac = it.get("price_fraction", "")
            price = it["price_whole"] + (("." + frac) if frac else "")
        link = it.get("link")
        if link and link.startswith("/"):
            link = "https://www.amazon.in" + link

        cleaned.append({
            "title": it.get("title"),
            "price": price,
            "rating": it.get("rating"),
            "reviews": it.get("reviews"),
            "link": link
        })

    return cleaned

if __name__ == "__main__":
    query = input("Enter Product Name: ")
    results = asyncio.run(scrape_amazon(query))

    for i, p in enumerate(results, 1):
        print(f"\nItem {i}")
        print(" Price:", p["price"])
        print(" Rating:", p["rating"])
        print(" Reviews:", p["reviews"])
        print(" Link:", p["link"])
