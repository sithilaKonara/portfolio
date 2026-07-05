#!/usr/bin/env python3
"""
scripts/fetch-credly.py

Scrapes the public Credly profile page and extracts badge data
from the embedded JSON (Next.js __NEXT_DATA__ script tag).
No auth required — works on any public profile.

Usage:
    python3 scripts/fetch-credly.py --username sithila-konara

Store your Credly username as a GitHub secret: CREDLY_USERNAME
"""

import argparse, json, sys, re, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).parent.parent
OUT  = ROOT / "src" / "data" / "badges.json"

# ── Parser: extract __NEXT_DATA__ JSON from the page ─────────
class NextDataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._in_next = False
        self.next_data = None

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            attrs_dict = dict(attrs)
            if attrs_dict.get("id") == "__NEXT_DATA__":
                self._in_next = True

    def handle_data(self, data):
        if self._in_next and self.next_data is None:
            try:
                self.next_data = json.loads(data)
            except Exception:
                pass
            self._in_next = False


# ── Date formatter ────────────────────────────────────────────
def fmt_date(raw: str):
    if not raw:
        return None
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").strftime("%b %d, %Y")
    except Exception:
        return raw[:10]


# ── Main fetch ────────────────────────────────────────────────
def fetch(username: str):
    url = f"https://www.credly.com/users/{username}/badges"
    print(f"[Credly] Scraping public profile: {url}\n")

    req = urllib.request.Request(url, headers={
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        print(f"  ✗ HTTP {e.code}: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"  ✗ Failed to fetch page: {e}")
        sys.exit(1)

    # ── Extract __NEXT_DATA__ ─────────────────────────────────
    parser = NextDataParser()
    parser.feed(html)

    if not parser.next_data:
        # Fallback: try regex extraction
        match = re.search(
            r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            html, re.DOTALL
        )
        if match:
            try:
                parser.next_data = json.loads(match.group(1))
            except Exception:
                pass

    if not parser.next_data:
        print("  ✗ Could not find __NEXT_DATA__ in page — Credly may have changed their page structure.")
        sys.exit(1)

    # ── Navigate to badge list in the JSON tree ───────────────
    # Path: props.pageProps.badges  OR  props.pageProps.data.badges
    page_props = (
        parser.next_data
        .get("props", {})
        .get("pageProps", {})
    )

    raw_badges = (
        page_props.get("badges")
        or page_props.get("data", {}).get("badges")
        or []
    )

    if not raw_badges:
        # Try one more known path
        raw_badges = page_props.get("initialState", {}).get("badges", {}).get("data", [])

    if not raw_badges:
        print("  ✗ Badge list not found in page data. Dumping page_props keys for debugging:")
        print(f"     {list(page_props.keys())}")
        # Write empty file so job doesn't fail the build
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text("[]")
        sys.exit(0)

    # ── Transform into our schema ─────────────────────────────
    badges = []
    for item in raw_badges:
        template        = item.get("badge_template") or {}
        issuer_entities = (item.get("issuer") or {}).get("entities") or []
        issuer          = ", ".join(
            e["entity"]["name"]
            for e in issuer_entities
            if (e.get("entity") or {}).get("name")
        )

        issued_raw  = item.get("issued_at_date") or ""
        expires_raw = item.get("expires_at_date") or ""

        badges.append({
            "id":          item.get("id"),
            "name":        template.get("name"),
            "description": template.get("description"),
            "imageUrl":    item.get("image_url"),
            "badgeUrl":    f"https://www.credly.com/badges/{item.get('id')}/public_url",
            "issuer":      issuer,
            "issuedAt":    fmt_date(issued_raw),
            "issuedRaw":   issued_raw[:10] if issued_raw else None,
            "expiresAt":   fmt_date(expires_raw),
            "expired":     item.get("expired", False),
            "skills":      [s["name"] for s in (template.get("skills") or [])],
            "level":       template.get("level"),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(badges, indent=2, ensure_ascii=False))
    print(f"  ✓ {len(badges)} badges written → {OUT.relative_to(ROOT)}")

    issuers = list({b["issuer"] for b in badges if b["issuer"]})
    print(f"  ✓ Issuers: {', '.join(issuers[:5])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Credly public profile badges")
    parser.add_argument("--username", required=True, help="Credly username (from profile URL)")
    args = parser.parse_args()
    fetch(args.username)