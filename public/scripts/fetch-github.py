#!/usr/bin/env python3
"""
scripts/fetch-github.py
Fetches public GitHub data and writes:
  src/data/repos.json
  src/data/github-stats.json

Usage:
    python3 scripts/fetch-github.py --username YOUR_GITHUB_USERNAME
    python3 scripts/fetch-github.py --username sithila --pat ghp_xxxxxxxxxxxx

Or via environment variable:
    GH_PAT=ghp_xxx python3 scripts/fetch-github.py --username sithila
"""

import argparse, json, os, sys, urllib.request, urllib.error
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Output paths ──────────────────────────────────────────────
ROOT      = Path(__file__).parent.parent
REPOS_OUT = ROOT / "src" / "data" / "repos.json"
STATS_OUT = ROOT / "src" / "data" / "github-stats.json"

# ── Language → hex colour map ─────────────────────────────────
LANG_COLORS = {
    "Python":     "#3572A5",
    "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A",
    "Go":         "#00ADD8",
    "Rust":       "#CE422B",
    "HCL":        "#844FBA",
    "Shell":      "#89E051",
    "Dockerfile": "#384D54",
    "HTML":       "#E34C26",
    "CSS":        "#563D7C",
    "Java":       "#B07219",
    "C++":        "#F34B7D",
}

# ── HTTP helper ───────────────────────────────────────────────
def gh_get(path: str, token: str, username: str, params: str = ""):
    url = f"https://api.github.com{path}?per_page=100{params}"
    headers = {
        "Accept":               "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent":           username,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print(f"  ✗ GitHub API {path}: HTTP {e.code}")
        return None

# ── Main ──────────────────────────────────────────────────────
def main(username: str, token: str):
    print(f"[GitHub] Fetching data for: {username}\n")

    # ── 1. Repos ──────────────────────────────────────────────
    print("→ Fetching public repositories...")
    raw = gh_get(f"/users/{username}/repos", token, username, "&type=public&sort=updated") or []

    repos = []
    total_stars = 0
    total_forks = 0
    lang_bytes: dict = defaultdict(int)

    for r in raw:
        if r.get("fork") or r.get("archived"):
            continue

        stars = r.get("stargazers_count", 0)
        forks = r.get("forks_count", 0)
        total_stars += stars
        total_forks += forks

        lang = r.get("language") or "Other"

        # Per-repo language breakdown for global chart
        lang_data = gh_get(f"/repos/{username}/{r['name']}/languages", token, username) or {}
        for l, b in lang_data.items():
            lang_bytes[l] += b

        # Human-readable updated date
        upd_raw = r.get("updated_at", "")
        try:
            d = datetime.fromisoformat(upd_raw.replace("Z", "+00:00"))
            delta = datetime.now(timezone.utc) - d
            if delta.days == 0:
                updated = "Today"
            elif delta.days < 7:
                updated = f"{delta.days}d ago"
            elif delta.days < 30:
                updated = f"{delta.days // 7}w ago"
            else:
                updated = d.strftime("%b %Y")
        except Exception:
            updated = upd_raw[:10]

        repos.append({
            "name":        r["name"],
            "fullName":    r["full_name"],
            "description": r.get("description") or "",
            "url":         r["html_url"],
            "homepage":    r.get("homepage") or "",
            "stars":       stars,
            "forks":       forks,
            "language":    lang,
            "langColor":   LANG_COLORS.get(lang, "#849495"),
            "topics":      r.get("topics", [])[:4],
            "updatedAt":   updated,
            "openIssues":  r.get("open_issues_count", 0),
        })

    repos.sort(key=lambda x: x["stars"], reverse=True)
    REPOS_OUT.write_text(json.dumps(repos, indent=2, ensure_ascii=False))
    print(f"  ✓ {len(repos)} repos written → {REPOS_OUT.relative_to(ROOT)}")

    # ── 2. Contribution grid (last 365 days) ──────────────────
    print("→ Fetching contribution events...")
    today = datetime.now(timezone.utc).date()
    grid = {(today - timedelta(days=i)).isoformat(): 0 for i in range(365)}

    events = gh_get(f"/users/{username}/events/public", token, username) or []
    for ev in events:
        if ev.get("type") not in ("PushEvent", "CreateEvent", "PullRequestEvent", "IssuesEvent"):
            continue
        day = ev.get("created_at", "")[:10]
        if day in grid:
            weight = {"PushEvent": 3, "PullRequestEvent": 2}.get(ev["type"], 1)
            grid[day] += weight

    contributions = [{"date": d, "count": grid[d]} for d in sorted(grid)]
    print(f"  ✓ {len(contributions)} days of contribution data")

    # ── 3. Language percentages ────────────────────────────────
    total_bytes = sum(lang_bytes.values()) or 1
    languages = {
        lang: round(b / total_bytes * 100, 1)
        for lang, b in sorted(lang_bytes.items(), key=lambda x: -x[1])
    }
    print(f"  ✓ Languages: {list(languages.keys())[:5]}")

    # ── 4. Total commit count via Search API ──────────────────
    print("→ Fetching total commit count...")
    total_commits = 0
    try:
        url = f"https://api.github.com/search/commits?q=author:{username}&per_page=1"
        headers = {
            "Accept":    "application/vnd.github.cloak-preview+json",
            "User-Agent": username,
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
            total_commits = data.get("total_count", 0)
        print(f"  ✓ Total commits: {total_commits:,}")
    except Exception as e:
        print(f"  ⚠ Commit count unavailable: {e}")

    # ── 5. Write github-stats.json ─────────────────────────────
    stats = {
        "username":      username,
        "totalStars":    total_stars,
        "totalForks":    total_forks,
        "totalRepos":    len(repos),
        "totalCommits":  total_commits,
        "contributions": contributions,
        "languages":     languages,
        "fetchedAt":     datetime.now(timezone.utc).isoformat(),
    }
    STATS_OUT.write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(f"  ✓ Stats written → {STATS_OUT.relative_to(ROOT)}")

    print(f"\n✅ Done. Stars: {total_stars} | Forks: {total_forks} | Repos: {len(repos)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch GitHub portfolio data")
    parser.add_argument("--username", required=True, help="GitHub username")
    parser.add_argument("--pat", default=os.environ.get("GH_PAT", ""), help="GitHub PAT (or set GH_PAT env var)")
    args = parser.parse_args()

    main(args.username, args.pat)