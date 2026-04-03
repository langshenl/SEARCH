#!/bin/zsh
set -euo pipefail

QUERY="${1:-2026年 湖北省政策 site:www.hubei.gov.cn}"
MAX_PAGES="${2:-3}"
YEAR_RANGE="${3:-}"  # 格式: 2023-01-01,2026-12-31
OUTDIR="$HOME/Desktop/h5"
mkdir -p "$OUTDIR"

if [ -n "$YEAR_RANGE" ]; then
    START_DATE=$(echo "$YEAR_RANGE" | cut -d',' -f1)
    END_DATE=$(echo "$YEAR_RANGE" | cut -d',' -f2)
else
    YEAR=$(python3 - <<'PY'
from datetime import datetime
print(datetime.now().year)
PY
)
    START_DATE="${YEAR}-01-01"
    END_DATE="${YEAR}-12-31"
fi
STAMP=$(date +%Y%m%d_%H%M%S)
SAFE_NAME=$(python3 - <<'PY' "$QUERY"
import re, sys
q = sys.argv[1]
q = re.sub(r'[\\/:*?"<>|]+', '_', q)
q = re.sub(r'\s+', ' ', q).strip()
print(q[:80] or 'search')
PY
)
URL=$(python3 - <<'PY' "$QUERY"
import sys, urllib.parse
print('https://www.baidu.com/s?' + urllib.parse.urlencode({'wd': sys.argv[1]}))
PY
)
TMP_JS_DIR="/tmp/openclaw_baidu_multi"
mkdir -p "$TMP_JS_DIR"
NEXT_JS_FILE="$TMP_JS_DIR/next_page.js"
cat > "$NEXT_JS_FILE" <<'EOF'
(function(){
  window.scrollTo(0, document.body.scrollHeight);
  var nextByWord = Array.from(document.querySelectorAll('a')).find(function(a){
    var t = (a.innerText || a.textContent || '').replace(/\s+/g, ' ').trim();
    return t.indexOf('下一页') !== -1;
  });
  if (nextByWord) {
    nextByWord.click();
    return 'CLICKED_NEXT_BY_WORD';
  }
  var nextByHref = Array.from(document.querySelectorAll('a[href]')).find(function(a){
    var href = a.getAttribute('href') || '';
    return href.indexOf('rsv_page=1') !== -1 || href.indexOf('pn=10') !== -1 || href.indexOf('pn=20') !== -1 || href.indexOf('pn=30') !== -1;
  });
  if (nextByHref) {
    nextByHref.click();
    return 'CLICKED_NEXT_BY_HREF';
  }
  return 'NEXT_PAGE_NOT_FOUND';
})();
EOF

/usr/bin/osascript <<OSA
tell application "Safari"
    activate
    if (count of windows) = 0 then
        make new document
    end if
    tell front window
        set newTab to (make new tab with properties {URL:"$URL"})
    end tell
end tell
OSA

sleep 6

TIME_STATUS=$(/usr/bin/osascript <<'OSA'
tell application "Safari"
    return do JavaScript "(function(){var el=document.getElementById('timeRlt');if(!el)return 'TIME_DROPDOWN_NOT_FOUND';el.click();return 'CLICKED_TIME_DROPDOWN';})();" in front document
end tell
OSA
)

sleep 2

DATE_JS=$(cat <<EOF
(function(){var panel=document.querySelector('.custom_2wanX');if(!panel)return 'CUSTOM_PANEL_NOT_FOUND';var inputs=Array.from(panel.querySelectorAll('input')).filter(function(i){return (i.type||'text')==='text';});if(inputs.length<2)return 'DATE_INPUT_NOT_FOUND';function setv(el,val){var p=Object.getPrototypeOf(el);var d=Object.getOwnPropertyDescriptor(p,'value');if(d&&d.set){d.set.call(el,val);}else{el.value=val;}}function fire(el){el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));el.dispatchEvent(new Event('blur',{bubbles:true}));}var s=inputs[0],e=inputs[1];s.click();s.focus();setv(s,'$START_DATE');fire(s);e.click();e.focus();setv(e,'$END_DATE');fire(e);var btn=panel.querySelector('button');if(!btn)return 'CONFIRM_BUTTON_NOT_FOUND';btn.click();btn.dispatchEvent(new MouseEvent('mousedown',{bubbles:true}));btn.dispatchEvent(new MouseEvent('mouseup',{bubbles:true}));btn.dispatchEvent(new MouseEvent('click',{bubbles:true}));return 'DATE_FILLED_CONFIRM_CLICKED';})();
EOF
)

DATE_STATUS=$(/usr/bin/osascript <<OSA
tell application "Safari"
    return do JavaScript $(python3 - <<'PY' "$DATE_JS"
import json, sys
print(json.dumps(sys.argv[1]))
PY
) in front document
end tell
OSA
)

sleep 6

PAGE=1
SAVED_COUNT=0
while [ "$PAGE" -le "$MAX_PAGES" ]; do
  OUTFILE="$OUTDIR/${STAMP}_${SAFE_NAME}_page${PAGE}.md"
  HTML=$(/usr/bin/osascript <<'OSA'
tell application "Safari"
    do JavaScript "document.documentElement.outerHTML" in front document
end tell
OSA
)
  printf "%s" "$HTML" > "$OUTFILE"
  echo "保存文件_PAGE${PAGE}: $OUTFILE"
  SAVED_COUNT=$PAGE

  if [ "$PAGE" -ge "$MAX_PAGES" ]; then
    break
  fi

  NEXT_STATUS=$(/usr/bin/osascript <<OSA
set jsFile to POSIX file "$NEXT_JS_FILE"
set jsText to do shell script "cat " & quoted form of POSIX path of jsFile
tell application "Safari"
    return do JavaScript jsText in front document
end tell
OSA
)
  echo "翻页状态_PAGE${PAGE}_TO_$((PAGE+1)): $NEXT_STATUS"

  case "$NEXT_STATUS" in
    CLICKED_NEXT_BY_WORD|CLICKED_NEXT_BY_HREF)
      ;;
    *)
      break
      ;;
  esac

  PAGE=$((PAGE+1))
  sleep 6
done

CLOSE_STATUS=$(/usr/bin/osascript <<'OSA'
tell application "Safari"
    try
        close front document
        return "CLOSED_FRONT_DOCUMENT"
    on error errMsg
        return "CLOSE_FAILED: " & errMsg
    end try
end tell
OSA
)

echo "搜索词: $QUERY"
echo "最大页数: $MAX_PAGES"
echo "时间筛选开始: $START_DATE"
echo "时间筛选结束: $END_DATE"
echo "时间下拉状态: $TIME_STATUS"
echo "日期填写状态: $DATE_STATUS"
echo "实际保存页数: $SAVED_COUNT"
echo "关闭页面状态: $CLOSE_STATUS"
echo "文件夹: $OUTDIR"
