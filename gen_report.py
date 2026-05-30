#!/usr/bin/env python3
"""
主题ETF赛道雷达 — HTML看板生成器
25只ETF卡片矩阵，暗色CATL风，含导航栏
数据内嵌到HTML中 (零外部依赖)
"""

import json, sys, os, time

DIR = os.path.dirname(__file__)
DATA_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "data.json")
OUT_PATH = sys.argv[2] if len(sys.argv) > 2 else os.path.join(DIR, "index.html")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    raw = json.load(f)

etfs_json = json.dumps(raw, ensure_ascii=False)

def _fmt(n, d=2):
    if n is None: return "—"
    return f"{n:.{d}f}"

def _aum_str(aum):
    if aum is None: return "—"
    if aum >= 10000: return f"{aum/10000:.2f}万亿"
    if aum >= 100: return f"{aum:.1f}亿"
    return f"{aum:.2f}亿"

def _pct(p):
    if p is None: return "—"
    return f"{p:+.2f}%"

# ═══════════════════════════════════════════
# HTML 模板 (f-string — 双花括号)
# ═══════════════════════════════════════════
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>主题ETF赛道雷达 | 25板块日监控</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Microsoft YaHei","PingFang SC",sans-serif;background:#0a0e17;color:#e6edf3;line-height:1.5;padding:16px;min-height:100vh}}
.wrap{{max-width:1600px;margin:0 auto}}

/* ── 头部 ── */
.header{{background:linear-gradient(135deg,#0a1628 0%,#0f3460 40%,#16213e 70%,#0a0e17 100%);border:1px solid #1e3a5f;border-radius:16px;padding:28px 20px 20px;margin-bottom:12px;text-align:center;position:relative;overflow:hidden}}
.header::before{{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle at 30% 30%,rgba(63,185,80,0.08) 0%,transparent 50%),radial-gradient(circle at 70% 70%,rgba(88,166,255,0.06) 0%,transparent 50%);animation:pulse 4s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:0.6}}50%{{opacity:1}}}}
.header h1{{font-size:1.6em;font-weight:700;position:relative;z-index:1;letter-spacing:1px}}
.header .sub{{color:#8b949e;font-size:0.82em;margin-top:6px;position:relative;z-index:1}}

/* ── 快捷导航 ── */
.nav-bar{{display:flex;justify-content:center;gap:6px;margin-bottom:12px;flex-wrap:wrap;position:relative;z-index:2}}
.nav-btn{{font-size:0.7em;padding:5px 12px;border-radius:14px;background:#131a26;border:1px solid #1e2d45;color:#8b949e;text-decoration:none;transition:all .2s;display:inline-block}}
.nav-btn:hover{{border-color:#58a6ff;color:#58a6ff}}
.nav-btn.active{{border-color:#58a6ff;color:#58a6ff;background:rgba(88,166,255,0.1)}}

/* ── KPI汇总 ── */
.kpi-row{{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap}}
.kpi-box{{flex:1;min-width:140px;background:#131a26;border:1px solid #1e2d45;border-radius:10px;padding:12px;text-align:center}}
.kpi-box .kl{{color:#8b949e;font-size:0.68em;letter-spacing:0.5px}}
.kpi-box .kv{{font-size:1.4em;font-weight:700;margin-top:2px}}
.kpi-box .kn{{font-size:0.7em;color:#6e7681;margin-top:2px}}

/* ── 分类筛选 ── */
.filter-bar{{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}}
.filter-tag{{font-size:0.7em;padding:4px 10px;border-radius:12px;background:#131a26;border:1px solid #1e2d45;color:#8b949e;cursor:pointer;transition:all .2s;user-select:none}}
.filter-tag:hover{{border-color:#58a6ff;color:#58a6ff}}
.filter-tag.on{{background:rgba(88,166,255,0.15);border-color:#58a6ff;color:#58a6ff}}

/* ── 排序 ── */
.sort-bar{{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap;align-items:center}}
.sort-bar .sl{{font-size:0.7em;color:#8b949e;margin-right:4px}}
.sort-btn{{font-size:0.68em;padding:3px 10px;border-radius:10px;background:#131a26;border:1px solid #1e2d45;color:#8b949e;cursor:pointer;transition:all .2s;user-select:none}}
.sort-btn:hover{{border-color:#d29922;color:#d29922}}
.sort-btn.on{{border-color:#d29922;color:#d29922;background:rgba(210,153,34,0.12)}}

/* ── ETF卡片网格 ── */
.etf-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-bottom:16px}}
.etf-card{{background:#131a26;border:1px solid #1e2d45;border-radius:12px;padding:14px;transition:border-color .2s;display:flex;flex-direction:column}}
.etf-card:hover{{border-color:#3a5a8a}}
.etf-card.rise{{border-left:3px solid #3fb950}}
.etf-card.fall{{border-left:3px solid #f85149}}
.etf-card.flat{{border-left:3px solid #484f58}}

/* 卡片头部 */
.etf-top{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px}}
.etf-info{{flex:1}}
.etf-name{{font-size:0.95em;font-weight:700;color:#e6edf3}}
.etf-code{{font-size:0.65em;color:#484f58;margin-left:4px}}
.etf-cat{{font-size:0.62em;color:#6e7681;margin-top:1px}}
.etf-change{{font-size:1.15em;font-weight:700;text-align:right;white-space:nowrap}}

/* 价格行 */
.etf-price-row{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px}}
.etf-price{{font-size:1.25em;font-weight:800}}
.etf-pe{{font-size:0.7em;color:#8b949e}}
.etf-pe .pe-val{{color:#58a6ff;font-weight:600}}

/* 收益条 */
.etf-ret{{display:flex;gap:6px;margin-bottom:8px;flex-wrap:wrap}}
.ret-tag{{font-size:0.65em;padding:2px 6px;border-radius:4px;white-space:nowrap}}
.ret-tag.up{{background:rgba(63,185,80,0.12);color:#3fb950}}
.ret-tag.dn{{background:rgba(248,81,73,0.12);color:#f85149}}
.ret-tag.na{{background:rgba(139,148,158,0.08);color:#8b949e}}

/* AUM+费率 */
.etf-meta{{display:flex;gap:8px;margin-bottom:6px;flex-wrap:wrap;font-size:0.68em;color:#8b949e}}
.etf-meta span{{padding:2px 6px;border-radius:4px;background:rgba(88,166,255,0.06)}}
.etf-meta .aum-v{{color:#e6edf3;font-weight:600}}
.etf-meta .fee-v{{color:#d29922}}

/* MA偏离 */
.etf-ma{{display:flex;gap:8px;margin-bottom:6px;font-size:0.65em;flex-wrap:wrap}}
.ma-tag{{padding:2px 6px;border-radius:4px}}
.ma-tag.above{{background:rgba(63,185,80,0.08);color:#3fb950}}
.ma-tag.below{{background:rgba(248,81,73,0.08);color:#f85149}}

/* 趋势图 */
.etf-chart{{height:48px;margin-bottom:6px;border-radius:6px;overflow:hidden;background:rgba(0,0,0,0.2)}}
.etf-chart svg{{width:100%;height:100%}}

/* 备用代码 */
.etf-backup{{font-size:0.6em;color:#484f58;border-top:1px solid #1e2d45;padding-top:6px;margin-top:auto}}

/* ── 页脚 ── */
.footer{{text-align:center;font-size:0.65em;color:#484f58;padding:12px 0;border-top:1px solid #1e2d45;margin-top:8px}}

/* ── 移动端 ── */
@media(max-width:600px){{
    .etf-grid{{grid-template-columns:1fr}}
    .nav-btn{{font-size:0.65em;padding:4px 8px}}
    .kpi-box{{min-width:100px}}
}}
</style>
</head>
<body>
<div class="wrap">

<!-- 导航栏 -->
<div class="nav-bar">
  <a class="nav-btn" href="https://zxb20262026.github.io/300750/">⚡ 宁德时代</a>
  <a class="nav-btn" href="https://zxb20262026.github.io/600900/">🌊 长江电力</a>
  <a class="nav-btn active">🎯 ETF赛道雷达</a>
</div>

<!-- 头部 -->
<div class="header">
  <h1>🎯 主题ETF赛道雷达</h1>
  <div class="sub">25板块 · 日监控 · <span id="gen-time">{raw.get("generated","")}</span></div>
</div>

<!-- KPI汇总 -->
<div class="kpi-row" id="kpi-row"></div>

<!-- 分类筛选 -->
<div class="filter-bar" id="filter-bar"></div>

<!-- 排序 -->
<div class="sort-bar">
  <span class="sl">排序:</span>
  <span class="sort-btn on" data-sort="change">涨跌幅</span>
  <span class="sort-btn" data-sort="aum">规模</span>
  <span class="sort-btn" data-sort="ret1m">1月收益</span>
  <span class="sort-btn" data-sort="ret3m">3月收益</span>
  <span class="sort-btn" data-sort="name">名称</span>
</div>

<!-- ETF卡片 -->
<div class="etf-grid" id="etf-grid"></div>

<!-- 页脚 -->
<div class="footer">
  <p>数据来源: 新浪/腾讯/东方财富 | 仅供参考 不构成投资建议</p>
  <p>Generated: <span id="footer-time"></span></p>
</div>

</div>

<script>
const DATA = {etfs_json};

// ═══════════════════════════════════
// 工具函数
// ═══════════════════════════════════
function fmtPct(v) {{
    if (v === null || v === undefined) return "—";
    return (v>=0?"+":"") + v.toFixed(2) + "%";
}}
function aumStr(a) {{
    if (!a) return "—";
    if (a >= 10000) return (a/10000).toFixed(2) + "万亿";
    if (a >= 100) return a.toFixed(1) + "亿";
    return a.toFixed(2) + "亿";
}}
function colorPct(v) {{ return v>0?"#3fb950":v<0?"#f85149":"#8b949e"; }}
function priceFmt(p) {{ return p ? p.toFixed(3) : "—"; }}

// ═══════════════════════════════════
// KPI 汇总
// ═══════════════════════════════════
function buildKPI() {{
    const etfs = DATA.etfs;
    const up = etfs.filter(e=>e.change_pct>0).length;
    const dn = etfs.filter(e=>e.change_pct<0).length;
    const totalAum = etfs.reduce((s,e)=>s+(e.aum||0),0);
    const changes = etfs.filter(e=>e.change_pct!=null).map(e=>e.change_pct);
    const avgChg = changes.length ? changes.reduce((a,b)=>a+b,0)/changes.length : 0;
    const maxUp = changes.length ? Math.max(...etfs.filter(e=>e.change_pct>0).map(e=>[e.short,e.change_pct])||[["—",0]],x=>x[1]) : ["—",0];
    const maxDn = changes.length ? Math.min(...etfs.filter(e=>e.change_pct<0).map(e=>[e.short,e.change_pct])||[["—",0]],x=>x[1]) : ["—",0];
    
    document.getElementById("kpi-row").innerHTML = `
        <div class="kpi-box"><div class="kl">监控ETF</div><div class="kv">${{etfs.length}}只</div><div class="kn">25板块</div></div>
        <div class="kpi-box"><div class="kl">上涨/下跌</div><div class="kv"><span style="color:#3fb950">${{up}}</span>/<span style="color:#f85149">${{dn}}</span></div><div class="kn">${{etfs.length-up-dn}}只平</div></div>
        <div class="kpi-box"><div class="kl">平均涨跌</div><div class="kv" style="color:${{colorPct(avgChg)}}">${{fmtPct(avgChg)}}</div></div>
        <div class="kpi-box"><div class="kl">合计规模</div><div class="kv">${{aumStr(totalAum)}}</div></div>
    `;
}}

// ═══════════════════════════════════
// 分类筛选
// ═══════════════════════════════════
function buildFilters() {{
    const cats = [...new Set(DATA.etfs.map(e=>e.cat))];
    let html = '<span class="filter-tag on" data-cat="all">全部</span>';
    cats.forEach(c => {{
        html += `<span class="filter-tag" data-cat="${{c}}">${{c}}</span>`;
    }});
    document.getElementById("filter-bar").innerHTML = html;
    
    document.querySelectorAll(".filter-tag").forEach(btn => {{
        btn.addEventListener("click", function() {{
            document.querySelectorAll(".filter-tag").forEach(b=>b.classList.remove("on"));
            this.classList.add("on");
            currentFilter = this.dataset.cat;
            renderCards();
        }});
    }});
}}

// ═══════════════════════════════════
// SVG 迷你趋势图
// ═══════════════════════════════════
function buildTrendSVG(trend) {{
    if (!trend || trend.length < 2) return "";
    const vals = trend.map(t=>t.close);
    const mx = Math.max(...vals), mn = Math.min(...vals);
    const rng = mx - mn || 1;
    const w = 280, h = 48, pad = 3;
    let pathD = "", fillD = "";
    vals.forEach((v,i) => {{
        const x = pad + (i/(vals.length-1))*(w-2*pad);
        const y = pad + (1-(v-mn)/rng)*(h-2*pad);
        pathD += (i===0?"M":"L") + x.toFixed(1) + "," + y.toFixed(1);
    }});
    fillD = pathD + ` L${{w-pad}},${{h-pad}} L${{pad}},${{h-pad}} Z`;
    const clr = vals[vals.length-1] >= vals[0] ? "#3fb950" : "#f85149";
    return `<svg viewBox="0 0 ${{w}} ${{h}}" preserveAspectRatio="none">
        <defs><linearGradient id="g${{trend[0].date}}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${{clr}}" stop-opacity="0.2"/>
            <stop offset="100%" stop-color="${{clr}}" stop-opacity="0.02"/>
        </linearGradient></defs>
        <path d="${{fillD}}" fill="url(#g${{trend[0].date}})"/>
        <path d="${{pathD}}" fill="none" stroke="${{clr}}" stroke-width="1.2"/>
    </svg>`;
}}

// ═══════════════════════════════════
// ETF卡片渲染
// ═══════════════════════════════════
let currentFilter = "all";
let currentSort = "change";

function renderCards() {{
    let etfs = [...DATA.etfs];
    
    // 筛选
    if (currentFilter !== "all") {{
        etfs = etfs.filter(e => e.cat === currentFilter);
    }}
    
    // 排序
    if (currentSort === "change") etfs.sort((a,b)=>(b.change_pct||0)-(a.change_pct||0));
    else if (currentSort === "aum") etfs.sort((a,b)=>(b.aum||0)-(a.aum||0));
    else if (currentSort === "ret1m") etfs.sort((a,b)=>(b.returns?.["1m"]||0)-(a.returns?.["1m"]||0));
    else if (currentSort === "ret3m") etfs.sort((a,b)=>(b.returns?.["3m"]||0)-(a.returns?.["3m"]||0));
    else if (currentSort === "name") etfs.sort((a,b)=>a.short.localeCompare(b.short,"zh"));
    
    let html = "";
    etfs.forEach(e => {{
        const chg = e.change_pct;
        const chgCls = chg>0?"rise":chg<0?"fall":"flat";
        const r = e.returns || {{}};
        
        html += `<div class="etf-card ${{chgCls}}" data-cat="${{e.cat}}">
            <div class="etf-top">
                <div class="etf-info">
                    <span class="etf-name">${{e.short}}</span>
                    <span class="etf-code">${{e.code}}</span>
                    <div class="etf-cat">${{e.cat}} · ${{e.name}}</div>
                </div>
                <div class="etf-change" style="color:${{colorPct(chg)}}">${{fmtPct(chg)}}</div>
            </div>
            <div class="etf-price-row">
                <span class="etf-price">¥${{priceFmt(e.price)}}</span>
                <span class="etf-pe">PE<span class="pe-val">${{e.pe ? e.pe.toFixed(1) : "—"}}</span></span>
            </div>
            <div class="etf-ret">${{["1w","1m","3m","ytd"].map(k => {{
                const v = r[k];
                const cls = v>0?"up":v<0?"dn":"na";
                const label = {{"1w":"1周","1m":"1月","3m":"3月","ytd":"YTD"}}[k];
                return `<span class="ret-tag ${{cls}}">${{label}} ${{fmtPct(v)}}</span>`;
            }}).join("")}}</div>
            <div class="etf-meta">
                <span>规模 <b class="aum-v">${{aumStr(e.aum)}}</b></span>
                <span>费率 <b class="fee-v">${{e.fee ? e.fee.toFixed(2)+"%" : "—"}}</b></span>
            </div>
            <div class="etf-ma">${{[
                ["MA20", e.ma20_dev],
                ["MA60", e.ma60_dev],
            ].map(([l,v]) => {{
                const cls = v>0?"above":"below";
                const sign = v>0?"↑":"↓";
                return `<span class="ma-tag ${{cls}}">${{l}} ${{sign}}${{Math.abs(v||0).toFixed(1)}}%</span>`;
            }}).join("")}}</div>
            <div class="etf-chart">${{buildTrendSVG(e.trend_30)}}</div>
            <div class="etf-backup">备用: ${{(e.backup||[]).join(", ")}}</div>
        </div>`;
    }});
    
    if (html === "") html = '<div style="grid-column:1/-1;text-align:center;padding:40px;color:#484f58">暂无数据</div>';
    document.getElementById("etf-grid").innerHTML = html;
}}

// ═══════════════════════════════════
// 排序事件
// ═══════════════════════════════════
document.querySelectorAll(".sort-btn").forEach(btn => {{
    btn.addEventListener("click", function() {{
        document.querySelectorAll(".sort-btn").forEach(b=>b.classList.remove("on"));
        this.classList.add("on");
        currentSort = this.dataset.sort;
        renderCards();
    }});
}});

// ═══════════════════════════════════
// 初始化
// ═══════════════════════════════════
buildKPI();
buildFilters();
renderCards();
document.getElementById("footer-time").textContent = DATA.generated || "";
</script>
</body>
</html>'''

# ═══════════════════════════════════
# 写入
# ═══════════════════════════════════
with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ 生成 {OUT_PATH} ({len(html)} chars)")
print(f"   25 ETF卡片 + {len([e for e in raw.get('etfs',[]) if e.get('price')])} 只有数据")
