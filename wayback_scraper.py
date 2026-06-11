"""
Wayback Machine Reddit Community Scraper
-----------------------------------------
Usage:
    python wayback_scraper.py https://www.reddit.com/r/Coronavirus/

Output:
    - Prints all captured archive links with their dates
    - Prints capture count per month
    - Saves results to wayback_results.json
"""

import sys
import json
import re
import time
from collections import defaultdict
from urllib.request import urlopen, Request
from urllib.parse import quote, urlencode
from urllib.error import HTTPError, URLError


# ── Helpers ────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/120.0 Safari/537.36"
    )
}

def fetch(url: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except (HTTPError, URLError) as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt + 1}/{retries} after error: {e}")
                time.sleep(2)
            else:
                raise


def normalize_reddit_url(user_input: str) -> str:
    """
    Accept any of:
        https://www.reddit.com/r/Coronavirus
        https://www.reddit.com/r/Coronavirus/
        reddit.com/r/Coronavirus
        r/Coronavirus
        Coronavirus
    and return the canonical wiki/rules page URL.
    """
    user_input = user_input.strip().rstrip("/")

    # Extract subreddit name
    m = re.search(r"(?:r/)?([A-Za-z0-9_]+)$", user_input)
    if not m:
        raise ValueError(f"Could not parse subreddit from: {user_input!r}")
    
    subreddit = m.group(1)
    # Target the wiki/rules page (most commonly archived)
    return f"https://www.reddit.com/r/{subreddit}/wiki/rules/"


# ── CDX API (structured, reliable) ────────────────────────────────────────────

def fetch_cdx(target_url: str) -> list[dict]:
    """
    Query the Wayback CDX API for all captures of a URL.
    Returns list of dicts: {timestamp, url, statuscode}
    """
    params = urlencode({
        "url":      target_url,
        "output":   "json",
        "fl":       "timestamp,original,statuscode",
        "filter":   "statuscode:200",
        "collapse": "timestamp:8",   # deduplicate to 1 per day
        "limit":    "1000",
    })
    cdx_url = f"http://web.archive.org/cdx/search/cdx?{params}"

    print(f"\nQuerying CDX API for: {target_url}")
    raw = fetch(cdx_url)
    rows = json.loads(raw)

    # First row is the header ["timestamp","original","statuscode"]
    if not rows or rows[0][0] == "timestamp":
        rows = rows[1:]

    results = []
    for row in rows:
        timestamp, original, statuscode = row
        results.append({
            "date":       timestamp,                            # e.g. "20200331"
            "url":        f"https://web.archive.org/web/{timestamp}/{original}",
            "statuscode": statuscode,
        })

    return results


# ── Group by month ─────────────────────────────────────────────────────────────

MONTH_ABBR = {
    "01": "JAN", "02": "FEB", "03": "MAR", "04": "APR",
    "05": "MAY", "06": "JUN", "07": "JUL", "08": "AUG",
    "09": "SEP", "10": "OCT", "11": "NOV", "12": "DEC",
}

def group_by_month(captures: list[dict]) -> dict:
    """
    Returns {
        "2020": {"JAN": [...captures...], "FEB": [...], ...},
        "2021": {...},
        ...
    }
    """
    grouped = defaultdict(lambda: defaultdict(list))
    for c in captures:
        ts = c["date"]          # "20200331123456" or "20200331"
        year  = ts[:4]
        month = MONTH_ABBR.get(ts[4:6], ts[4:6])
        grouped[year][month].append(c)
    return {y: dict(m) for y, m in sorted(grouped.items())}


# ── Display ────────────────────────────────────────────────────────────────────

def display(captures: list[dict], by_month: dict):
    print("\n" + "=" * 65)
    print("ALL CAPTURED LINKS")
    print("=" * 65)
    for c in captures:
        print(f"  {c['date'][:8]}  →  {c['url']}")

    print("\n" + "=" * 65)
    print("CAPTURES PER MONTH")
    print("=" * 65)
    for year, months in by_month.items():
        print(f"\n  ── {year} ──")
        for month_abbr in ["JAN","FEB","MAR","APR","MAY","JUN",
                           "JUL","AUG","SEP","OCT","NOV","DEC"]:
            items = months.get(month_abbr, [])
            count = len(items)
            bar   = "█" * count
            print(f"    {month_abbr}  {count:>3}  {bar}")

    print(f"\n  Total captures: {len(captures)}")


# ── Save JSON ──────────────────────────────────────────────────────────────────

def save_json(captures: list[dict], by_month: dict, path: str = "wayback_results.json"):
    # Build a clean monthly summary
    monthly_summary = {}
    for year, months in by_month.items():
        monthly_summary[year] = {
            month: {
                "count": len(items),
                "links": [c["url"] for c in items],
            }
            for month, items in months.items()
        }

    output = {
        "total_captures": len(captures),
        "captures": captures,
        "monthly_summary": monthly_summary,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Results saved to: {path}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python wayback_scraper.py <reddit_community_url>")
        print("Example: python wayback_scraper.py https://www.reddit.com/r/Coronavirus/")
        sys.exit(1)

    user_input  = sys.argv[1]
    target_url  = normalize_reddit_url(user_input)

    captures    = fetch_cdx(target_url)
    by_month    = group_by_month(captures)

    display(captures, by_month)
    save_json(captures, by_month)


if __name__ == "__main__":
    main()
