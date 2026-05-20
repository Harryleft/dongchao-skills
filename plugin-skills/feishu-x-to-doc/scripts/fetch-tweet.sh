#!/usr/bin/env bash
# fetch-tweet.sh — Fetch tweet/thread/article content via fxtwitter API
# Usage: fetch-tweet.sh <screen_name> <tweet_id>
# Exit codes: 0=success, 1=api-error, 2=rate-limit, 3=not-found

set -euo pipefail

SCREEN_NAME="${1:?Usage: fetch-tweet.sh <screen_name> <tweet_id>}"
TWEET_ID="${2:?Usage: fetch-tweet.sh <screen_name> <tweet_id>}"
MAX_RETRIES=2
TIMEOUT=15

URL="https://api.fxtwitter.com/${SCREEN_NAME}/status/${TWEET_ID}"

attempt=0
while [ $attempt -le $MAX_RETRIES ]; do
  RESPONSE=$(curl -sL --max-time "$TIMEOUT" \
    -w "\n%{http_code}" \
    -A "Mozilla/5.0 (compatible; Googlebot/2.1)" \
    "$URL" 2>&1) || true

  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  BODY=$(echo "$RESPONSE" | sed '$d')

  case "$HTTP_CODE" in
    200)
      # Validate JSON structure
      if echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'tweet' in d, 'missing tweet key'" 2>/dev/null; then
        echo "$BODY"
        exit 0
      else
        echo "ERROR: Invalid JSON structure" >&2
        exit 1
      fi
      ;;
    404)
      echo "ERROR: Tweet not found or deleted" >&2
      exit 3
      ;;
    429)
      echo "WARN: Rate limited, waiting before retry..." >&2
      sleep 5
      attempt=$((attempt + 1))
      ;;
    *)
      echo "ERROR: HTTP $HTTP_CODE" >&2
      if [ $attempt -lt $MAX_RETRIES ]; then
        sleep 3
        attempt=$((attempt + 1))
      else
        exit 1
      fi
      ;;
  esac
done

echo "ERROR: Max retries exceeded" >&2
exit 1
