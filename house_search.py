"""
house_search.py

Daily house-search bot:
1. Calls Parse.bot's Domain.com.au wrapper API (search_properties_for_sale)
2. Filters against criteria set below
3. Compares against previously-seen listings (seen_listings.json)
4. Sends a Telegram message for each NEW matching listing

Environment variables required (set as GitHub Actions secrets):
    PARSE_API_KEY       - Parse.bot API key
    TELEGRAM_BOT_TOKEN  - Telegram bot token from BotFather
    TELEGRAM_CHAT_ID    - Your numeric Telegram chat ID
"""

import os
import sys
import json
import requests

# ── SEARCH CRITERIA — edit these to match what you're looking for ──────────
SEARCHES = [
    {
        "location": "sydney-nsw-2000",   # suburb-state-postcode slug
        "min_price": 800000,
        "max_price": 1200000,
        "min_bedrooms": 3,
        "min_bathrooms": 2,
        "property_type": "house",
    },
    # Add more dicts here for additional suburbs/criteria.
    # e.g. {"location": "newtown-nsw-2042", "max_price": 1000000, "min_bedrooms": 2, "property_type": "house"},
]

SEEN_FILE = "seen_listings.json"
PARSE_BASE_URL = "https://api.parse.bot/scraper/974154e5-ea89-4a21-b5a4-dff744547193"


def load_seen_ids():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen_ids(seen_ids):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen_ids), f, indent=2)


def search_listings(api_key, criteria):
    """Call Parse.bot's search_properties_for_sale endpoint with given criteria."""
    params = {k: v for k, v in criteria.items() if v is not None}
    headers = {"X-API-Key": api_key}
    url = f"{PARSE_BASE_URL}/search_properties_for_sale"

    resp = requests.get(url, headers=headers, params=params, timeout=30)

    if resp.status_code == 401:
        raise RuntimeError(
            "401 Unauthorized — API key is likely invalid or truncated. "
            "Go to Parse.bot dashboard and click 'Create API Key' for a fresh full-length key."
        )
    resp.raise_for_status()

    data = resp.json()
    return data.get("data", {}).get("results", [])


def send_telegram_message(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    resp = requests.post(
        url,
        data={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False},
        timeout=15,
    )
    resp.raise_for_status()


def format_listing_message(listing, criteria):
    address = listing.get("listingModel", {}).get("displayAddress", "Unknown address")
    url_path = listing.get("listingModel", {}).get("url", "")
    full_url = f"https://www.domain.com.au{url_path}" if url_path.startswith("/") else url_path
    suburb = criteria.get("location", "")

    lines = [
        "🏠 <b>New listing match!</b>",
        f"<b>{address}</b>",
        f"Search: {suburb}",
    ]
    if full_url:
        lines.append(full_url)
    return "\n".join(lines)


def main():
    api_key = os.environ.get("PARSE_API_KEY")
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    missing = [name for name, val in [
        ("PARSE_API_KEY", api_key),
        ("TELEGRAM_BOT_TOKEN", bot_token),
        ("TELEGRAM_CHAT_ID", chat_id),
    ] if not val]
    if missing:
        print(f"ERROR: missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    seen_ids = load_seen_ids()
    new_seen_ids = set(seen_ids)
    total_new = 0

    for criteria in SEARCHES:
        try:
            results = search_listings(api_key, criteria)
        except Exception as e:
            print(f"ERROR searching {criteria.get('location')}: {e}", file=sys.stderr)
            continue

        print(f"Search '{criteria.get('location')}': {len(results)} results returned")

        for listing in results:
            listing_id = str(listing.get("id"))
            if not listing_id or listing_id in seen_ids:
                continue

            # Skip off-the-plan "project" listings if you only want resale houses.
            # Comment this out if you want projects included too.
            if listing.get("listingType") == "project":
                new_seen_ids.add(listing_id)
                continue

            message = format_listing_message(listing, criteria)
            try:
                send_telegram_message(bot_token, chat_id, message)
                print(f"Notified: {listing_id}")
                total_new += 1
            except Exception as e:
                print(f"ERROR sending Telegram message for {listing_id}: {e}", file=sys.stderr)
                continue  # don't mark as seen if notification failed — retry next run

            new_seen_ids.add(listing_id)

    save_seen_ids(new_seen_ids)
    print(f"Done. {total_new} new listing(s) notified this run.")


if __name__ == "__main__":
    main()
