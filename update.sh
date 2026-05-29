#!/bin/bash
# 上交所沪深300ETF规模看板 — 日更新 + 自动推送GitHub Pages
# 需要环境变量: GH_TOKEN (GitHub Personal Access Token)
set -e
cd ~/sh300-etf-dashboard

if [ -z "$GH_TOKEN" ]; then
  echo "❌ 请设置环境变量 GH_TOKEN"
  exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M')] 🔄 开始日更新..."

python3 sync_data.py data.json
python3 gen_report.py data.json index.html

echo "[$(date '+%Y-%m-%d %H:%M')] 📤 推送GitHub..."

REPO="zxb20262026/sh300-etf-dashboard"

for f in index.html data.json; do
    ENCODED=$(base64 -w0 "$f")
    SHA=$(curl -s -H "Authorization: token $GH_TOKEN" \
      "https://api.github.com/repos/$REPO/contents/$f" | python3 -c "import sys,json;print(json.load(sys.stdin).get('sha',''))" 2>/dev/null)
    
    BODY="{\"message\":\"$(date '+%Y-%m-%d') 日更新\",\"content\":\"$ENCODED\",\"branch\":\"main\"}"
    [ -n "$SHA" ] && BODY="{\"message\":\"$(date '+%Y-%m-%d') 日更新\",\"content\":\"$ENCODED\",\"branch\":\"main\",\"sha\":\"$SHA\"}"
    
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT \
      -H "Authorization: token $GH_TOKEN" \
      -H "Accept: application/vnd.github+json" \
      "https://api.github.com/repos/$REPO/contents/$f" \
      -d "$BODY")
    echo "  $f → HTTP $STATUS"
done

echo "[$(date '+%Y-%m-%d %H:%M')] ✅ 更新完成 → https://zxb20262026.github.io/sh300-etf-dashboard/"
