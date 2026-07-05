#!/usr/bin/env python3
"""
scripts/fetch-credly.py – fetch public Credly badges via RSS (no auth)
Usage: python3 scripts/fetch-credly.py --user-id YOUR_UUID
"""

import argparse
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "src" / "data" / "badges.json"

def extract_image_from_description(desc: str) -> str:
    """Extract the first <img src="..."> from the description."""
    match = re.search(r'<img[^>]+src="([^"]+)"', desc)
    return match.group(1) if match else ""

def fetch(user_id: str):
    url = f"https://www.credly.com/users/{user_id}/badges.rss"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        xml_data = r.read().decode("utf-8")

    root = ET.fromstring(xml_data)
    channel = root.find("channel")
    if channel is None:
        raise ValueError("No channel found in RSS feed")

    badges = []
    for item in channel.findall("item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        pub_date = item.findtext("pubDate") or ""
        description = item.findtext("description") or ""

        image_url = extract_image_from_description(description)
        # Badge ID can be extracted from the link: /badges/<id>/
        badge_id = ""
        if link:
            m = re.search(r'/badges/([^/]+)/', link)
            if m:
                badge_id = m.group(1)

        badges.append({
            "id": badge_id,
            "name": title,
            "description": description[:300],   # truncate to keep JSON small
            "imageUrl": image_url,
            "badgeUrl": link,
            "issuer": "",                       # not available in RSS
            "issuedAt": pub_date,               # RSS pubDate is not the issue date, but close
            "expiresAt": None,
            "skills": [],                       # not available in RSS
        })

    OUT.write_text(json.dumps(badges, indent=2, ensure_ascii=False))
    print(f"✓ {len(badges)} badges → {OUT.relative_to(ROOT)}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--user-id", required=True)
    args = p.parse_args()
    print(f"Fetching Credly badges for user ID: {args.user_id}")
    fetch(args.user_id)