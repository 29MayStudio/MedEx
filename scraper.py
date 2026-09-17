import asyncio
import json
import re
from html import unescape
import aiohttp
from bs4 import BeautifulSoup

BASE_URL = "https://plus.medex.com.bd/brands?__m_asn=Roar%20Zone&page={}"
BATCH_SIZE = 20
CONCURRENCY_LIMIT = 20
OUTPUT_FILE = "list.json"

def parse_generics(generic_str: str) -> list:
    if not generic_str:
        return []
    # Split by comma ',', plus '+', or ampersand '&'
    parts = re.split(r'[,+&]', generic_str)
    return [p.strip() for p in parts if p.strip()]

def parse_page_html(html: str) -> tuple[list, bool]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("a", class_="brand-card")

    # Check if page indicates no brands found or contains no brand cards
    is_empty = len(cards) == 0 or "no brands found" in html.lower()

    results = []
    for card in cards:
        # Brand Name
        brand_elem = card.find("span", class_="brand-card__name")
        brand_name = brand_elem.get_text(strip=True) if brand_elem else ""

        # Dosage Form
        dosage_img = card.find("img", class_="dosage-icon")
        dosage_form = ""
        if dosage_img:
            dosage_form = dosage_img.get("title") or dosage_img.get("alt") or ""

        # Power / Strength
        strength_elem = card.find("div", class_="brand-card__strength")
        power = strength_elem.get_text(strip=True) if strength_elem else ""

        # Generic Name(s)
        generic_elem = card.find("div", class_="brand-card__generic")
        raw_generic = generic_elem.get_text(strip=True) if generic_elem else ""
        generic_names = parse_generics(raw_generic)

        # Manufacturer / Producer
        company_elem = card.find("div", class_="brand-card__company")
        manufacturer = company_elem.get_text(strip=True) if company_elem else ""

        results.append({
            "brand_name": brand_name,
            "power": power,
            "generic_names": generic_names,
            "manufacturer": manufacturer,
            "dosage_form": dosage_form
        })

    return results, is_empty

async def fetch_page(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, page: int, retries: int = 3) -> tuple[int, list, bool]:
    url = BASE_URL.format(page)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with semaphore:
        for attempt in range(retries):
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        html = await response.text()
                        items, is_empty = parse_page_html(html)
                        return page, items, is_empty
                    else:
                        print(f"Warning: Page {page} returned status {response.status}. Attempt {attempt+1}/{retries}")
            except Exception as e:
                print(f"Error fetching page {page} on attempt {attempt+1}/{retries}: {e}")
            await asyncio.sleep(1 * (attempt + 1))

    print(f"Failed to fetch page {page} after {retries} attempts.")
    return page, [], False

async def main():
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY_LIMIT)

    print("Starting dynamic scraper...")
    all_medicines = []
    current_page = 1
    stop_scraping = False

    async with aiohttp.ClientSession(connector=connector) as session:
        while not stop_scraping:
            pages_to_fetch = list(range(current_page, current_page + BATCH_SIZE))
            tasks = [fetch_page(session, semaphore, page) for page in pages_to_fetch]
            batch_results = await asyncio.gather(*tasks)

            # Sort batch results by page number
            batch_results.sort(key=lambda x: x[0])

            for page_num, items, is_empty in batch_results:
                if is_empty:
                    print(f"Reached page {page_num} with no medicine data or 'No Brands Found.'. Stopping scraper.")
                    stop_scraping = True
                    break
                all_medicines.extend(items)

            if not stop_scraping:
                current_page += BATCH_SIZE

    print(f"Total medicines scraped: {len(all_medicines)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_medicines, f, ensure_ascii=False, indent=2)

    print(f"Successfully saved output to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
