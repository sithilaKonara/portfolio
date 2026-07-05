#!/usr/bin/env python3
"""
scripts/fetch-credly.py
Fetches public Credly badges and writes src/data/badges.json

Usage:
    python3 scripts/fetch-credly.py --user-id YOUR_UUID
"""

import argparse, json, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT  = ROOT / "src" / "data" / "badges.json"

def fetch(user_id: str):
    url = f"https://www.credly.com/api/v1/users/{user_id}/badges?page=1&page_size=48&sort=-state_updated_at"
    req = urllib.request.Request(url, headers={
        "Accept":     "application/json",
        "User-Agent": "Mozilla/5.0",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)

    badges = []
    for item in data.get("data", []):
        template = item.get("badge_template", {})
        issuer_entities = item.get("issuer", {}).get("entities", [])
        issuer = ", ".join(e["entity"]["name"] for e in issuer_entities if e.get("entity"))

        badges.append({
            "id":          item.get("id"),
            "name":        template.get("name"),
            "description": template.get("description"),
            "imageUrl":    item.get("image_url"),
            "badgeUrl":    f"https://www.credly.com/badges/{item.get('id')}/public_url",
            "issuer":      issuer,
            "issuedAt":    item.get("issued_at_date"),
            "expiresAt":   item.get("expires_at_date"),
            "skills":      [s["name"] for s in template.get("skills", [])],
        })

    OUT.write_text(json.dumps(badges, indent=2, ensure_ascii=False))
    print(f"✓ {len(badges)} badges → {OUT.relative_to(ROOT)}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--user-id", required=True, help="Credly UUID from DevTools network tab")
    args = p.parse_args()
    fetch(args.user_id)