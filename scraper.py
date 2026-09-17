import asyncio
import json
import re
from html import unescape
import aiohttp
from bs4 import BeautifulSoup

BASE_URL = "https://plus.medex.com.bd/brands?__m_asn=Roar%20Zone&page={}"
TOTAL_PAGES = 847
CONCURRENCY_LIMIT = 20
OUTPUT_FILE = "list.json"

def parse_generics(generic_str: str) -> list:
    if not generic_str:
        return []
    # Split by comma ',', plus '+', or ampersand '&'
    parts = re.split(r'[,+&]', generic_str)
    return [p.strip() for p in parts if p.strip()]

def parse_page_html(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("a", class_="brand-card")
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

    return results

async def fetch_page(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, page: int, retries: int = 3) -> tuple:
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
                        items = parse_page_html(html)
                        return page, items
                    else:
                        print(f"Warning: Page {page} returned status {response.status}. Attempt {attempt+1}/{retries}")
            except Exception as e:
                print(f"Error fetching page {page} on attempt {attempt+1}/{retries}: {e}")
            await asyncio.sleep(1 * (attempt + 1))

    print(f"Failed to fetch page {page} after {retries} attempts.")
    return page, []

async def main():
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY_LIMIT)

    print(f"Starting scraper for {TOTAL_PAGES} pages...")
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_page(session, semaphore, page) for page in range(1, TOTAL_PAGES + 1)]
        results = await asyncio.gather(*tasks)

    # Sort pages in order
    results.sort(key=lambda x: x[0])

    all_medicines = []
    for page, items in results:
        all_medicines.extend(items)

    print(f"Total medicines scraped: {len(all_medicines)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_medicines, f, ensure_ascii=False, indent=2)

    print(f"Successfully saved output to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
