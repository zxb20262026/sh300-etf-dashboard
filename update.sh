#!/bin/bash
# 上交所沪深300ETF规模看板 — 日更新脚本
# 每天收盘后运行: sync_data.py → gen_report.py → git push
set -e
cd ~/sh300-etf-dashboard

echo "[$(date '+%Y-%m-%d %H:%M')] 🔄 开始日更新..."

python3 sync_data.py data.json
python3 gen_report.py data.json index.html

echo "[$(date '+%Y-%m-%d %H:%M')] ✅ 更新完成"
