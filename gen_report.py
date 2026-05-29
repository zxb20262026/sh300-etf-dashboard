#!/usr/bin/env python3
"""
生成上交所沪深300ETF规模看板 index.html
读取 data.json，将数据内嵌到HTML中
用法: python3 gen_report.py [data.json] [index.html]
"""

import json, sys, os

DIR = os.path.dirname(__file__)
DATA_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "data.json")
OUT_PATH = sys.argv[2] if len(sys.argv) > 2 else os.path.join(DIR, "index.html")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    raw = json.load(f)

etfs_json = json.dumps(raw, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>上交所沪深300ETF规模看板</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Microsoft YaHei","PingFang SC",sans-serif;background:#0a0e17;color:#e6edf3;line-height:1.5;padding:16px;min-height:100vh}}
.wrap{{max-width:1200px;margin:0 auto}}

.header{{background:linear-gradient(135deg,#0a1628 0%,#0f3460 40%,#16213e 70%,#0a0e17 100%);border:1px solid #1e3a5f;border-radius:16px;padding:28px 20px 20px;margin-bottom:16px;text-align:center;position:relative;overflow:hidden}}
.header::before{{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle at 30% 30%,rgba(63,185,80,0.08) 0%,transparent 50%),radial-gradient(circle at 70% 70%,rgba(88,166,255,0.06) 0%,transparent 50%);animation:pulse 4s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:0.6}}50%{{opacity:1}}}}
.header h1{{font-size:1.6em;font-weight:700;position:relative;z-index:1;letter-spacing:1px}}
.header .sub{{color:#8b949e;font-size:0.85em;margin-top:6px;position:relative;z-index:1}}

.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-bottom:16px}}
.kpi-card{{background:#131a26;border:1px solid #1e2d45;border-radius:10px;padding:14px;text-align:center}}
.kpi-card .kpi-label{{color:#8b949e;font-size:0.7em;letter-spacing:0.5px;margin-bottom:4px}}
.kpi-card .kpi-value{{font-size:1.5em;font-weight:700;margin-bottom:2px}}

.etf-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(370px,1fr));gap:14px;margin-bottom:16px}}
.etf-card{{background:#131a26;border:1px solid #1e2d45;border-radius:12px;padding:16px;transition:border-color .2s}}
.etf-card:hover{{border-color:#3a5a8a}}
.etf-hd{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px}}
.etf-name{{font-size:1.05em;font-weight:700;color:#e6edf3}}
.etf-code{{font-size:0.7em;color:#484f58;margin-left:6px}}
.etf-change{{font-size:1.1em;font-weight:700}}
.etf-full{{font-size:0.68em;color:#6e7681;margin-bottom:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.etf-aum{{font-size:1.6em;font-weight:800;margin-bottom:2px}}
.etf-aum .unit{{font-size:0.55em;color:#8b949e;font-weight:400}}
.etf-meta{{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0}}
.etf-tag{{font-size:0.68em;padding:2px 8px;border-radius:5px;background:rgba(88,166,255,0.08);color:#8b949e}}
.etf-tag.green{{color:#3fb950}}
.etf-tag.red{{color:#f85149}}
.etf-tag.gold{{color:#d29922}}
.etf-chart{{height:100px;margin-top:8px}}
.etf-chart svg{{width:100%;height:100%}}

.sort-bar{{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}}
.sort-btn{{font-size:0.72em;padding:5px 14px;border-radius:16px;background:#131a26;border:1px solid #1e2d45;color:#8b949e;cursor:pointer;transition:all .2s}}
.sort-btn:hover,.sort-btn.on{{border-color:#58a6ff;color:#58a6ff;background:rgba(88,166,255,0.06)}}

.footer{{text-align:center;padding:20px 0 40px;color:#484f58;font-size:0.72em;line-height:1.8}}
.footer a{{color:#58a6ff;text-decoration:none}}

@media(max-width:600px){{
  body{{padding:10px}}
  .etf-grid{{grid-template-columns:1fr}}
  .header{{padding:20px 14px}}
  .header h1{{font-size:1.3em}}
}}
</style>
</head>
<body>
<div class="wrap">

<div class="header">
  <h1>📊 上交所沪深300ETF规模看板</h1>
  <div class="sub" id="headerSub">最近三个月净值规模趋势 · 数据更新于 {raw['generated']}</div>
</div>

<div class="kpi-grid" id="kpiGrid"></div>

<div class="sort-bar">
  <span style="font-size:0.72em;color:#8b949e;line-height:28px">排序:</span>
  <button class="sort-btn on" onclick="sortCards('aum')">按规模↓</button>
  <button class="sort-btn" onclick="sortCards('ret3m')">按3月收益</button>
  <button class="sort-btn" onclick="sortCards('ret1m')">按1月收益</button>
  <button class="sort-btn" onclick="sortCards('name')">按名称</button>
</div>

<div class="etf-grid" id="etfGrid"></div>

<div class="footer">
  指标：净值规模（亿元） | 规模估算 = (当前净值 ÷ Q1末净值) × Q1季报规模<br>
  数据来源：天天基金Q1季报 + 腾讯行情K线 | 自动更新于 {raw['generated']}<br>
  仅供参考，不构成投资建议
</div>

</div>

<script>
const DATA = {etfs_json};

let currentSort = 'aum';

function buildSVG(vals, code){{
  if(!vals || vals.length < 5) return '<div style="text-align:center;color:#484f58;line-height:100px;font-size:12px">数据不足</div>';
  const n = vals.length, max = Math.max(...vals), min = Math.min(...vals), rng = max - min || 1;
  
  let grid = '';
  for(let i=0;i<=3;i++){{
    const y = 4 + (i/3)*88;
    grid += `<line x1="4" y1="${{y.toFixed(1)}}" x2="96" y2="${{y.toFixed(1)}}" stroke="#1e2d45" stroke-width="0.5"/>`;
  }}
  
  let pathD = '';
  for(let i=0;i<n;i++){{
    const x = 4 + (i/(n-1))*92, y = 4 + (1 - (vals[i]-min)/rng)*88;
    pathD += (i===0?'M':'L') + x.toFixed(1) + ',' + y.toFixed(1);
  }}
  const fillD = pathD + ' L96,96 L4,96 Z';
  const clr = vals[n-1] >= vals[0] ? '#3fb950' : '#f85149';
  const lastY = 4 + (1 - (vals[n-1]-min)/rng)*88;
  
  return `<svg viewBox="0 0 100 100" preserveAspectRatio="none">
    <defs><linearGradient id="g${{code}}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="${{clr}}" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="${{clr}}" stop-opacity="0.03"/>
    </linearGradient></defs>
    ${{grid}}
    <path d="${{fillD}}" fill="url(#g${{code}})"/>
    <path d="${{pathD}}" fill="none" stroke="${{clr}}" stroke-width="1.5" stroke-linejoin="round"/>
    <circle cx="96" cy="${{lastY.toFixed(1)}}" r="2" fill="${{clr}}"/>
  </svg>`;
}}

function buildCard(e){{
  const aum = e.aum_now || e.aum_q1;
  const aumStr = aum >= 10000 ? (aum/10000).toFixed(2)+'万亿' : aum >= 100 ? aum.toFixed(1)+'亿' : aum >= 1 ? aum.toFixed(2)+'亿' : '0.00亿';
  const ret3m = e.ret_3m || 0;
  const clr = ret3m >= 0 ? '#3fb950' : '#f85149';
  const trend = e.aum_trend || (e.trend_3m ? e.trend_3m.map(d=>d.close) : []);
  const fee = (e.mgmt_fee||0) + (e.cust_fee||0);
  
  let tags = '';
  if(e.aum_q1 >= 1000) tags += '<span class="etf-tag gold">千亿级</span>';
  if(e.aum_q1 < 5) tags += '<span class="etf-tag red">小规模⚠️</span>';
  tags += `<span class="etf-tag">费率 ${{fee.toFixed(2)}}%</span>`;
  if(e.ret_1m !== undefined){{
    const c = e.ret_1m >= 0 ? 'green' : 'red';
    tags += `<span class="etf-tag ${{c}}">1月 ${{e.ret_1m>=0?'+':''}}${{e.ret_1m}}%</span>`;
  }}
  
  return `<div class="etf-card" data-aum="${{aum}}" data-ret3m="${{ret3m}}" data-ret1m="${{e.ret_1m||0}}" data-name="${{e.short}}">
    <div class="etf-hd">
      <div><span class="etf-name">${{e.short}}</span><span class="etf-code">${{e.code}}</span></div>
      <span class="etf-change" style="color:${{clr}}">${{ret3m>=0?'+':''}}${{ret3m.toFixed(1)}}%</span>
    </div>
    <div class="etf-full">${{e.full}} · ${{e.company}} · Q1季报 ${{e.aum_q1||'—'}}亿</div>
    <div class="etf-aum">${{aumStr}}<span class="unit"> 净值规模</span></div>
    <div class="etf-meta">${{tags}}</div>
    <div class="etf-chart">${{buildSVG(trend, e.code)}}</div>
  </div>`;
}}

function render(){{
  const sorted = [...DATA.etfs];
  if(currentSort === 'aum') sorted.sort((a,b)=>(b.aum_now||b.aum_q1||0)-(a.aum_now||a.aum_q1||0));
  else if(currentSort === 'ret3m') sorted.sort((a,b)=>(b.ret_3m||0)-(a.ret_3m||0));
  else if(currentSort === 'ret1m') sorted.sort((a,b)=>(b.ret_1m||0)-(a.ret_1m||0));
  else if(currentSort === 'name') sorted.sort((a,b)=>a.short.localeCompare(b.short));
  
  const totalAum = DATA.etfs.reduce((s,e)=>s + (e.aum_now||e.aum_q1||0), 0);
  const avgRet = DATA.etfs.reduce((s,e)=>s+(e.ret_3m||0),0)/DATA.etfs.length;
  const maxAum = Math.max(...DATA.etfs.map(e=>e.aum_now||e.aum_q1||0));
  
  document.getElementById('kpiGrid').innerHTML = `
    <div class="kpi-card"><div class="kpi-label">ETF总数</div><div class="kpi-value">${{DATA.etfs.length}}<span style="font-size:0.5em;color:#8b949e"> 只</span></div></div>
    <div class="kpi-card"><div class="kpi-label">合计规模</div><div class="kpi-value">${{totalAum>=10000?(totalAum/10000).toFixed(2)+'万亿':totalAum.toFixed(0)+'亿'}}</div></div>
    <div class="kpi-card"><div class="kpi-label">平均3月收益</div><div class="kpi-value" style="color:${{avgRet>=0?'#3fb950':'#f85149'}}">${{avgRet>=0?'+':''}}${{avgRet.toFixed(2)}}%</div></div>
    <div class="kpi-card"><div class="kpi-label">最大单只规模</div><div class="kpi-value">${{maxAum>=1000?(maxAum/10000).toFixed(2)+'万亿':maxAum.toFixed(0)+'亿'}}</div></div>
  `;
  
  document.getElementById('etfGrid').innerHTML = sorted.map(buildCard).join('');
}}

function sortCards(key){{
  currentSort = key;
  document.querySelectorAll('.sort-btn').forEach(b=>b.classList.remove('on'));
  event.target.classList.add('on');
  render();
}}

render();
</script>
</body>
</html>'''

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ 生成 {OUT_PATH} ({len(html)} bytes)")
print(f"   6只ETF | 更新时间: {raw['generated']}")
