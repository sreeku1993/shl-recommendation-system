import requests
from bs4 import BeautifulSoup
import json
import time
import re

BASE_URL = "https://www.shl.com"
CATALOG_URL = "https://www.shl.com/products/product-catalog/?start={}&type=1"

HEADERS = {"User-Agent": "Mozilla/5.0"}

def extract_duration(text):
    match = re.search(r'(\d+)', text)
    return int(match.group(1)) if match else 0


def scrape_catalog_page(start):
    url = CATALOG_URL.format(start)
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    assessments = []

    rows = soup.find_all("tr", attrs={"data-entity-id": True})

    for row in rows:

        link_tag = row.find("a")
        if not link_tag:
            continue

        name = link_tag.text.strip()
        url = BASE_URL + link_tag["href"]

        cols = row.find_all("td")

        # Column 2 = Remote
        remote_support = bool(cols[1].find("span", class_="catalogue__circle -yes"))

        # Column 3 = Adaptive
        adaptive_support = bool(cols[2].find("span", class_="catalogue__circle -yes"))

        # Column 4 = Test Type
        key_span = cols[3].find("span", class_="product-catalogue__key")
        test_type = key_span.text.strip() if key_span else ""

        assessments.append({
            "name": name,
            "url": url,
            "remote_support": remote_support,
            "adaptive_support": adaptive_support,
            "test_type": test_type
        })

    return assessments


def scrape_detail_page(assessment):
    response = requests.get(assessment["url"], headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    description = ""
    desc_tag = soup.find("h4", string="Description")
    if desc_tag:
        description = desc_tag.find_next("p").text.strip()

    duration = 0
    dur_tag = soup.find("h4", string="Assessment length")
    if dur_tag:
        duration_text = dur_tag.find_next("p").text.strip()
        duration = extract_duration(duration_text)

    assessment["description"] = description
    assessment["duration"] = duration

    return assessment


def main():
    all_assessments = []

    for start in range(0, 400, 12):
        print(f"Scraping catalog page start={start}")
        page_assessments = scrape_catalog_page(start)
        all_assessments.extend(page_assessments)
        time.sleep(1)

    print(f"Collected {len(all_assessments)} catalog entries")

    enriched = []

    for i, assessment in enumerate(all_assessments):
        print(f"[{i+1}/{len(all_assessments)}] {assessment['name']}")
        try:
            full_data = scrape_detail_page(assessment)
            enriched.append(full_data)
            time.sleep(1)
        except Exception as e:
            print("Error:", e)

    with open("data/assessments.json", "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2)

    print("Scraping complete.")


if __name__ == "__main__":
    main()