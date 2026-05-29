#!/usr/bin/env python3
"""
上交所沪深300ETF规模看板 — 数据采集模块
每日拉取6只ETF的净值、规模、趋势，输出 data.json
用法: python3 sync_data.py
"""

import urllib.request, ssl, json, re, time

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

H = {"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"}
H_EM = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.eastmoney.com/"}

def get(url, enc="utf-8", t=10, headers=None):
    req = urllib.request.Request(url, headers=headers or H)
    return urllib.request.urlopen(req, timeout=t, context=ssl_ctx).read().decode(enc, errors="replace")

def get_json(url, t=10):
    return json.loads(get(url, t=t, headers=H_EM))

# ═══════════════════════════════════════════
# ETF 定义: 6只沪市沪深300ETF
# ═══════════════════════════════════════════
ETFS = [
    {"code": "510300", "short": "300ETF",     "full": "华泰柏瑞沪深300ETF",   "company": "华泰柏瑞"},
    {"code": "510310", "short": "HS300ETF",   "full": "易方达沪深300ETF",     "company": "易方达"},
    {"code": "510330", "short": "华夏300",    "full": "华夏沪深300ETF",       "company": "华夏"},
    {"code": "510350", "short": "工银300",    "full": "工银沪深300ETF",       "company": "工银瑞信"},
    {"code": "510360", "short": "广发300",    "full": "广发沪深300ETF",       "company": "广发"},
    {"code": "510380", "short": "国寿300",    "full": "国寿安保沪深300ETF",   "company": "国寿安保"},
]

SH_CODES = [e["code"] for e in ETFS]


# ═══════════════════════════════════════════
# 1. 基金基本信息 (规模/费率) — 天天基金
# ═══════════════════════════════════════════
def fetch_fund_info(code):
    """从天天基金获取季报规模、费率、全称"""
    try:
        html = get(f"https://fundf10.eastmoney.com/jbgk_{code}.html")
        
        # 净资产规模
        aum = None
        m = re.search(r'净资产规模[：:][^<]*<span[^>]*>\s*([\d,]+\.?\d*)亿', html, re.DOTALL)
        if not m:
            m = re.search(r'净资产规模</th><td>([\d,]+\.?\d*)亿', html)
        if m:
            aum = float(m.group(1).replace(',', ''))
        
        # 管理费率
        mgmt = None
        m = re.search(r'管理费率</th><td>([\d.]+)%', html)
        if m: mgmt = float(m.group(1))
        
        # 托管费率
        cust = None
        m = re.search(r'托管费率</th><td>([\d.]+)%', html)
        if m: cust = float(m.group(1))
        
        return {"aum_q1": aum, "mgmt_fee": mgmt, "cust_fee": cust}
    except Exception as e:
        return {"error": str(e)[:80]}


# ═══════════════════════════════════════════
# 2. K线 — 腾讯 (前复权)
# ═══════════════════════════════════════════
def fetch_kline(code, days=120):
    """获取ETF日K线，返回日期+收盘价+成交量"""
    full_code = f"sh{code}"
    try:
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={full_code},day,,,{days},qfq"
        d = json.loads(get(url, headers=H_EM))
        klines = d.get("data", {}).get(full_code, {}).get("qfqday", []) or \
                 d.get("data", {}).get(full_code, {}).get("day", [])
        
        result = []
        for k in klines:
            if isinstance(k, list) and len(k) >= 3:
                result.append({"date": k[0], "close": float(k[2]), "vol": float(k[5]) if len(k) > 5 else 0})
            elif isinstance(k, str):
                parts = k.strip("[]'").split(',')
                if len(parts) >= 3:
                    result.append({"date": parts[0].strip("'"), 
                                   "close": float(parts[2].strip("'")),
                                   "vol": float(parts[5].strip("'")) if len(parts) > 5 else 0})
        return result
    except Exception as e:
        return None


# ═══════════════════════════════════════════
# 3. 腾讯实时行情 (PE/PB/市值级)
# ═══════════════════════════════════════════
def fetch_tencent_quote(code):
    """腾讯行情: qt[3]=当前价, qt[31]=涨跌幅, qt[39]=PE, qt[45]=总市值"""
    full_code = f"sh{code}"
    try:
        raw = get(f"http://qt.gtimg.cn/q={full_code}", "gbk", t=8)
        fields = raw.split('~')
        if len(fields) < 50:
            return None
        return {
            "price": float(fields[3]) if fields[3] else None,
            "change_pct": float(fields[32]) if fields[32] else None,
            "pe": float(fields[39]) if fields[39] else None,
            "market_cap": float(fields[45]) if fields[45] else None,
            "pb": float(fields[46]) if fields[46] else None,
        }
    except:
        return None


# ═══════════════════════════════════════════
# 汇总输出
# ═══════════════════════════════════════════
def build_output():
    output = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "generated_ts": int(time.time()),
        "etfs": []
    }
    
    for etf in ETFS:
        code = etf["code"]
        entry = {
            "code": code,
            "short": etf["short"],
            "full": etf["full"],
            "company": etf["company"],
        }
        
        # Fund info
        info = fetch_fund_info(code)
        entry.update({k: v for k, v in info.items() if v is not None})
        
        # K-line
        kline = fetch_kline(code)
        if kline:
            entry["kline"] = kline
            
            # 近3个月趋势 (约66个交易日)
            trend_3m = kline[-66:] if len(kline) >= 66 else kline
            entry["trend_3m"] = trend_3m
            
            # AUM trend: (当前净值 / Q1末净值) × Q1规模
            if info.get("aum_q1"):
                # Q1末是3月31日，找到最近的K线
                q1_price = None
                for k in kline:
                    if k["date"] >= "2026-03-31":
                        q1_price = k["close"]
                        break
                if not q1_price:
                    q1_price = kline[0]["close"]
                
                if q1_price and q1_price > 0:
                    entry["aum_trend"] = [
                        round(k["close"] / q1_price * info["aum_q1"], 2)
                        for k in trend_3m
                    ]
                    entry["aum_now"] = entry["aum_trend"][-1]
            
            # 当前净值
            entry["nav"] = kline[-1]["close"]
            
            # 收益率
            closes = [k["close"] for k in kline]
            if len(closes) >= 22:
                entry["ret_1m"] = round((closes[-1] / closes[-22] - 1) * 100, 2)
            if len(closes) >= 66:
                entry["ret_3m"] = round((closes[-1] / closes[-66] - 1) * 100, 2)
            if len(closes) >= 132:
                entry["ret_6m"] = round((closes[-1] / closes[-132] - 1) * 100, 2)
        
        # Tencent quote (备用)
        qt = fetch_tencent_quote(code)
        if qt:
            if not entry.get("pe"): entry["pe"] = qt.get("pe")
        
        output["etfs"].append(entry)
        print(f"  ✓ {etf['short']}({code}): NAV={entry.get('nav')}, AUM={entry.get('aum_now')}亿, "
              f"1m={entry.get('ret_1m')}%, 3m={entry.get('ret_3m')}%")
    
    return output


if __name__ == "__main__":
    import sys, os
    
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "data.json")
    
    print(f"🔄 上交所沪深300ETF 数据采集 [{time.strftime('%Y-%m-%d %H:%M')}]")
    print(f"   目标: {len(ETFS)}只ETF → {out_path}")
    print()
    
    data = build_output()
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 写入 {out_path} ({len(json.dumps(data, ensure_ascii=False))} bytes)")
    print(f"   {len(data['etfs'])}只ETF, 生成时间: {data['generated']}")
