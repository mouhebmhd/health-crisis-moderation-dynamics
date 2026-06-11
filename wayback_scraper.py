"""
Wayback Machine Reddit Community Scraper
-----------------------------------------
Usage:
    python wayback_scraper.py https://www.reddit.com/r/Coronavirus/wiki/rules/
    python wayback_scraper.py https://www.reddit.com/r/Coronavirus/
    python wayback_scraper.py r/Coronavirus

The script targets the wiki/rules page of the subreddit by default.
If you pass the full wiki URL directly, it uses that as-is.

Output:
    - Prints all captured archive links with their dates
    - Prints capture count per month / year
    - Saves results to wayback_results.json
"""

import sys
import json
import re
import time
from collections import defaultdict
from urllib.request import urlopen, Request
from urllib.parse import urlencode
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


def build_target_url(user_input: str) -> str:
    """
    Accepts any of:
        https://www.reddit.com/r/Coronavirus/wiki/rules/   → used as-is
        https://www.reddit.com/r/Coronavirus/              → appends wiki/rules/
        https://www.reddit.com/r/Coronavirus               → appends wiki/rules/
        reddit.com/r/Coronavirus                           → appends wiki/rules/
        r/Coronavirus                                      → builds full URL
        Coronavirus                                        → builds full URL
    """
    s = user_input.strip()

    # If it already contains 'wiki' somewhere, use it as-is (just normalise scheme)
    if "wiki" in s.lower():
        if not s.startswith("http"):
            s = "https://" + s.lstrip("/")
        return s.rstrip("/") + "/"

    # Otherwise extract subreddit name and point at wiki/rules
    m = re.search(r"r/([A-Za-z0-9_]+)", s)
    if m:
        sub = m.group(1)
    else:
        # Bare name like "Coronavirus"
        sub = s.split("/")[-1]

    return f"https://www.reddit.com/r/{sub}/wiki/rules/"


# ── CDX API ────────────────────────────────────────────────────────────────────

def fetch_cdx(target_url: str) -> list:
    """
    Query the Wayback CDX API.
    Returns list of dicts: {date, url, statuscode}
    """
    # Try with and without filter in case of statuscode variations
    variants = [
        {"filter": "statuscode:200"},
        {},   # no filter — catch redirects / all statuses
    ]

    for extra in variants:
        params = {
            "url":      target_url,
            "output":   "json",
            "fl":       "timestamp,original,statuscode",
            "collapse": "timestamp:8",
            "limit":    "1000",
        }
        params.update(extra)

        cdx_url = "https://web.archive.org/cdx/search/cdx?" + urlencode(params)
        print(f"  CDX request: {cdx_url}")

        raw = fetch(cdx_url)
        rows = json.loads(raw) if raw.strip() else []

        # Drop header row if present
        if rows and rows[0][0] == "timestamp":
            rows = rows[1:]

        if rows:
            print(f"  → {len(rows)} captures found.")
            return [
                {
                    "date":       r[0],
                    "url":        f"https://web.archive.org/web/{r[0]}/{r[1]}",
                    "statuscode": r[2],
                }
                for r in rows
            ]

        print(f"  → 0 captures with params {extra}, trying next variant...")

    print("\n  ⚠ No captures found for this URL.")
    print("  Tip: Check the URL is correct and was actually archived.")
    print(f"  You can verify manually: https://web.archive.org/web/*/{target_url}")
    return []


# ── Group by month ─────────────────────────────────────────────────────────────

MONTH_ABBR = {
    "01": "JAN", "02": "FEB", "03": "MAR", "04": "APR",
    "05": "MAY", "06": "JUN", "07": "JUL", "08": "AUG",
    "09": "SEP", "10": "OCT", "11": "NOV", "12": "DEC",
}
MONTH_ORDER = ["JAN","FEB","MAR","APR","MAY","JUN",
               "JUL","AUG","SEP","OCT","NOV","DEC"]

def group_by_month(captures: list) -> dict:
    grouped = defaultdict(lambda: defaultdict(list))
    for c in captures:
        ts    = c["date"]
        year  = ts[:4]
        month = MONTH_ABBR.get(ts[4:6], ts[4:6])
        grouped[year][month].append(c)
    return {y: dict(m) for y, m in sorted(grouped.items())}


# ── Display ────────────────────────────────────────────────────────────────────

def display(captures: list, by_month: dict):
    print("\n" + "=" * 70)
    print("ALL CAPTURED LINKS")
    print("=" * 70)
    for c in captures:
        print(f"  {c['date'][:8]}  [{c['statuscode']}]  {c['url']}")

    print("\n" + "=" * 70)
    print("CAPTURES PER MONTH")
    print("=" * 70)
    for year, months in by_month.items():
        total_year = sum(len(v) for v in months.values())
        print(f"\n  ── {year}  (total: {total_year}) ──")
        for abbr in MONTH_ORDER:
            items = months.get(abbr, [])
            count = len(items)
            bar   = "█" * count
            print(f"    {abbr}  {count:>3}  {bar}")

    print(f"\n  Grand total captures: {len(captures)}")


# ── Save JSON ──────────────────────────────────────────────────────────────────

def save_json(captures: list, by_month: dict, path: str = "wayback_results.json"):
    monthly_summary = {
        year: {
            month: {
                "count": len(items),
                "links": [c["url"] for c in items],
            }
            for month, items in months.items()
        }
        for year, months in by_month.items()
    }

    output = {
        "total_captures": len(captures),
        "captures":       captures,
        "monthly_summary": monthly_summary,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Saved to: {path}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage:   python wayback_scraper.py <reddit_url>")
        print("Example: python wayback_scraper.py https://www.reddit.com/r/Coronavirus/wiki/rules/")
        print("         python wayback_scraper.py r/Coronavirus")
        sys.exit(1)

    user_input = sys.argv[1]
    target_url = build_target_url(user_input)

    print(f"\n→ Target URL : {target_url}")
    print(f"→ Wayback    : https://web.archive.org/web/*/{target_url}")

    captures = fetch_cdx(target_url)

    if captures:
        by_month = group_by_month(captures)
        display(captures, by_month)
        save_json(captures, by_month)
    else:
        # Still save an empty result
        save_json([], {})

if __name__ == "__main__":
    main()