#!/usr/bin/env python3
"""
scripts/fetch-credly.py
Fetches public Credly badges and writes src/data/badges.json

Usage:
    python3 scripts/fetch-credly.py --user-id YOUR_UUID

Your UUID: b97fb7c2-3a3d-48ac-b1ad-5c9a970e8ffd
Store it as a GitHub secret: CREDLY_USER_ID
"""

import argparse, json, sys, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT  = ROOT / "src" / "data" / "badges.json"

def fetch(user_id: str):
    print(f"[Credly] Fetching badges for user ID: {user_id}\n")

    badges = []
    page   = 1

    while True:
        url = (
            f"https://www.credly.com/api/v1/users/{user_id}/badges"
            f"?page={page}&page_size=48&sort=-state_updated_at"
        )
        print(f"  → Fetching page {page}: {url}")

        req = urllib.request.Request(url, headers={
            "Accept":          "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer":         f"https://www.credly.com/users/{user_id}/badges",
            "Origin":          "https://www.credly.com",
            "X-Requested-With": "XMLHttpRequest",
        })

        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            print(f"  ✗ HTTP {e.code}: {e.reason}")
            sys.exit(1)
        except Exception as e:
            print(f"  ✗ Error: {e}")
            sys.exit(1)

        items = data.get("data", [])
        if not items:
            break

        for item in items:
            template        = item.get("badge_template", {})
            issuer_entities = item.get("issuer", {}).get("entities", [])
            issuer          = ", ".join(
                e["entity"]["name"]
                for e in issuer_entities
                if e.get("entity")
            )

            # Format dates to readable string
            issued_raw  = item.get("issued_at_date") or ""
            expires_raw = item.get("expires_at_date") or ""

            def fmt_date(raw: str) -> str:
                if not raw:
                    return None
                try:
                    return datetime.strptime(raw[:10], "%Y-%m-%d").strftime("%b %d, %Y")
                except Exception:
                    return raw[:10]

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
                "skills":      [s["name"] for s in template.get("skills", [])],
                "level":       template.get("level"),
            })

        # Check if there are more pages
        metadata   = data.get("metadata", {})
        total_count = metadata.get("total_count", 0)
        if len(badges) >= total_count:
            break

        page += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(badges, indent=2, ensure_ascii=False))
    print(f"\n  ✓ {len(badges)} badges written → {OUT.relative_to(ROOT)}")

    # Print summary
    issuers = list({b["issuer"] for b in badges if b["issuer"]})
    print(f"  ✓ Issuers: {', '.join(issuers[:5])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Credly badge data")
    parser.add_argument("--user-id", required=True, help="Credly user UUID")
    args = parser.parse_args()
    fetch(args.user_id)