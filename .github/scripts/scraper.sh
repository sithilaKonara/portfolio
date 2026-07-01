#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scraper.sh [username]
# If username is not provided, reads MEDIUM_USERNAME from environment.

USERNAME="${1:-${MEDIUM_USERNAME:-}}"
if [ -z "$USERNAME" ]; then
  echo "❌ Error: No Medium username provided. Set MEDIUM_USERNAME env or pass as argument."
  exit 1
fi

# Feed URLs (with and without @)
URLS=(
  "https://medium.com/feed/@${USERNAME}"
  "https://medium.com/feed/${USERNAME}"
)

# Curl settings
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
ACCEPT_HEADER="Accept: application/rss+xml, application/xml, text/xml, */*"

FEED_DATA=""
for URL in "${URLS[@]}"; do
  echo "→ Trying $URL" >&2
  for TRY in 1 2 3; do
    if FEED_DATA=$(curl -sSL --max-time 15 \
        -H "User-Agent: $USER_AGENT" \
        -H "$ACCEPT_HEADER" \
        "$URL" 2>/dev/null); then
      if echo "$FEED_DATA" | grep -q '<rss'; then
        echo "✓ Success (attempt $TRY)" >&2
        break 2
      else
        echo "⚠️ Response is not RSS (attempt $TRY)" >&2
      fi
    else
      echo "⚠️ Curl failed (attempt $TRY)" >&2
    fi
    sleep $((TRY * 2))
  done
  echo "❌ All attempts failed for $URL" >&2
done

if [ -z "$FEED_DATA" ]; then
  echo "❌ Could not fetch Medium feed from any URL." >&2
  exit 1
fi

# Save feed to temp file
echo "$FEED_DATA" > /tmp/feed.xml

# Count items
ITEM_COUNT=$(xmlstarlet sel -T -t -v "count(//item)" /tmp/feed.xml 2>/dev/null || echo "0")
echo "Found $ITEM_COUNT items in feed." >&2

if [ "$ITEM_COUNT" -eq 0 ]; then
  echo "❌ No items found in feed. Check the feed URL or your username." >&2
  exit 1
fi

# Create output directory
mkdir -p src/data

# Temporary file for JSON lines
> /tmp/posts.json.tmp

# Process each item
for ((i=1; i<=ITEM_COUNT; i++)); do
  # Extract fields
  TITLE=$(xmlstarlet sel -T -t -v "//item[$i]/title" /tmp/feed.xml 2>/dev/null || echo "")
  LINK=$(xmlstarlet sel -T -t -v "//item[$i]/link" /tmp/feed.xml 2>/dev/null || echo "")
  PUB_DATE_RAW=$(xmlstarlet sel -T -t -v "//item[$i]/pubDate" /tmp/feed.xml 2>/dev/null || echo "")
  GUID=$(xmlstarlet sel -T -t -v "//item[$i]/guid" /tmp/feed.xml 2>/dev/null || echo "")
  CATEGORY=$(xmlstarlet sel -T -t -v "//item[$i]/category[1]" /tmp/feed.xml 2>/dev/null || echo "")

  # Content:encoded with namespace
  CONTENT_HTML=$(xmlstarlet sel -N content="http://purl.org/rss/1.0/modules/content/" -T -t -v "//item[$i]/content:encoded" /tmp/feed.xml 2>/dev/null || echo "")

  # --- Thumbnail extraction: skip tracking pixels ---
  THUMB=""
  if [ -n "$CONTENT_HTML" ]; then
    THUMB=$(echo "$CONTENT_HTML" | \
      sed -n 's/.*<img[^>]*src="\([^"]*\)".*/\1/p' | \
      grep -v '/_/stat?' | \
      head -1)
  fi

  # Fallback to media:thumbnail if still empty and not tracking
  if [ -z "$THUMB" ]; then
    MEDIA_THUMB=$(xmlstarlet sel -N media="http://search.yahoo.com/mrss/" -T -t -v "//item[$i]/media:thumbnail/@url" /tmp/feed.xml 2>/dev/null || echo "")
    if ! echo "$MEDIA_THUMB" | grep -q '/_/stat?'; then
      THUMB="$MEDIA_THUMB"
    fi
  fi

  # Plain text excerpt (strip HTML, collapse spaces)
  PLAIN_FULL=$(echo "$CONTENT_HTML" | sed -e 's/<[^>]*>//g' -e 's/&nbsp;/ /g' | tr -s ' ' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

  # Format date (MM.DD.YYYY)
  FORMATTED_DATE=""
  if [ -n "$PUB_DATE_RAW" ]; then
    if date -d "$PUB_DATE_RAW" >/dev/null 2>&1; then
      FORMATTED_DATE=$(date -d "$PUB_DATE_RAW" +"%m.%d.%Y")
    else
      FORMATTED_DATE=$(echo "$PUB_DATE_RAW" | cut -c1-10)
    fi
  fi

  # Category: uppercase, default DEVOPS
  if [ -n "$CATEGORY" ]; then
    PRIMARY_CAT=$(echo "$CATEGORY" | tr '[:lower:]' '[:upper:]')
  else
    PRIMARY_CAT="DEVOPS"
  fi

  # Build JSON object with jq
  jq -n \
    --arg title "$TITLE" \
    --arg link "$LINK" \
    --arg pubDate "$FORMATTED_DATE" \
    --arg category "$PRIMARY_CAT" \
    --arg thumbnail "$THUMB" \
    --arg guid "$GUID" \
    --arg plain "$PLAIN_FULL" \
    '{
      title: $title,
      link: $link,
      pubDate: $pubDate,
      category: $category,
      excerpt: (if ($plain | length) > 200 then ($plain[0:200] | rtrimstr(" ") | sub(" [^ ]*$"; "")) + "…" else $plain end),
      thumbnail: $thumbnail,
      guid: $guid
    }' >> /tmp/posts.json.tmp
done

# Combine into final JSON array
jq -s '.' /tmp/posts.json.tmp > src/data/posts.json

echo "✓ Wrote $(jq length src/data/posts.json) posts to src/data/posts.json" >&2