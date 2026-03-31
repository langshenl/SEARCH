#!/bin/zsh
set -euo pipefail

QUERY="${1:-人工智能}"
OUTDIR="$HOME/Desktop/cnki-h5"
mkdir -p "$OUTDIR"
STAMP=$(date +%Y%m%d_%H%M%S)
SAFE_NAME=$(python3 - <<'PY' "$QUERY"
import re, sys
q = sys.argv[1]
q = re.sub(r'[\\/:*?"<>|]+', '_', q)
q = re.sub(r'\s+', ' ', q).strip()
print(q[:80] or 'cnki-search')
PY
)
OUTFILE="$OUTDIR/${STAMP}_${SAFE_NAME}.md"
URL=$(python3 - <<'PY' "$QUERY"
import sys, urllib.parse
print('https://kns.cnki.net/kns8s/search?kw=' + urllib.parse.quote(sys.argv[1]))
PY
)

/usr/bin/osascript <<OSA
tell application "Safari"
    activate
    if (count of windows) = 0 then
        make new document
    end if
    set URL of front document to "$URL"
end tell
OSA

sleep 8

HTML=$(/usr/bin/osascript <<'OSA'
tell application "Safari"
    do JavaScript "document.documentElement.outerHTML" in front document
end tell
OSA
)
printf "%s" "$HTML" > "$OUTFILE"

echo "搜索词: $QUERY"
echo "保存文件: $OUTFILE"
echo "文件夹: $OUTDIR"
