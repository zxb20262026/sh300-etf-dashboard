#!/usr/bin/env python3
"""
主题ETF赛道雷达 — 数据采集 v2 (优化并行)
"""
import urllib.request, ssl, json, re, time, os
from concurrent.futures import ThreadPoolExecutor, as_completed

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
H = {"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"}
H_EM = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.eastmoney.com/"}

def get(url, enc="utf-8", t=8, headers=None):
    req = urllib.request.Request(url, headers=headers or H)
    return urllib.request.urlopen(req, timeout=t, context=ssl_ctx).read().decode(enc, errors="replace")

ETFS = [
    {"code":"513500","name":"标普500ETF博时","short":"标普500","cat":"跨境","market":"sh","backup":["513650","159655"]},
    {"code":"159941","name":"纳指ETF广发","short":"纳指100","cat":"跨境","market":"sz","backup":["513100","513300"]},
    {"code":"159920","name":"恒生ETF华夏","short":"港股","cat":"跨境","market":"sz","backup":["513660","513600"]},
    {"code":"510300","name":"沪深300ETF华泰柏瑞","short":"沪深300","cat":"宽基","market":"sh","backup":["510310","510330"]},
    {"code":"510500","name":"中证500ETF南方","short":"中证500","cat":"宽基","market":"sh","backup":["159922","512500"]},
    {"code":"588000","name":"科创50ETF华夏","short":"科创50","cat":"宽基","market":"sh","backup":["588050","588060"]},
    {"code":"159781","name":"科创创业ETF易方达","short":"双创50","cat":"宽基","market":"sz","backup":["159783","159603"]},
    {"code":"159915","name":"创业板ETF易方达","short":"创业板","cat":"宽基","market":"sz","backup":["159952","159948"]},
    {"code":"159819","name":"人工智能ETF易方达","short":"人工智能","cat":"科技","market":"sz","backup":["515070","515980"]},
    {"code":"159995","name":"芯片ETF华夏","short":"芯片","cat":"科技","market":"sz","backup":["512760","159801"]},
    {"code":"159516","name":"半导体设备ETF国泰","short":"半导体设备","cat":"科技","market":"sz","backup":["159558","560780"]},
    {"code":"562500","name":"机器人ETF华夏","short":"机器人","cat":"科技","market":"sh","backup":["159770","562560"]},
    {"code":"512710","name":"军工龙头ETF富国","short":"航天","cat":"军工","market":"sh","backup":["512660","512680"]},
    {"code":"159206","name":"卫星ETF永赢","short":"卫星","cat":"军工","market":"sz","backup":["563230","563790"]},
    {"code":"516160","name":"新能源ETF南方","short":"新能源","cat":"新能源","market":"sh","backup":["515030","159875"]},
    {"code":"515790","name":"光伏ETF华泰柏瑞","short":"光伏","cat":"新能源","market":"sh","backup":["159857","516880"]},
    {"code":"159566","name":"储能电池ETF易方达","short":"储能","cat":"新能源","market":"sz","backup":["159755","159305"]},
    {"code":"512800","name":"银行ETF华宝","short":"银行","cat":"金融","market":"sh","backup":["512700","515290"]},
    {"code":"512880","name":"证券ETF国泰","short":"证券","cat":"金融","market":"sh","backup":["512000","159841"]},
    {"code":"159928","name":"消费ETF汇添富","short":"消费","cat":"消费","market":"sz","backup":["510150","512600"]},
    {"code":"515170","name":"食品饮料ETF华夏","short":"食品饮料","cat":"消费","market":"sh","backup":["159843","516900"]},
    {"code":"512170","name":"医疗ETF华宝","short":"医疗","cat":"医药","market":"sh","backup":["512290","159828"]},
    {"code":"515880","name":"通信ETF国泰","short":"通讯","cat":"其他","market":"sh","backup":["515050","159994"]},
    {"code":"518880","name":"黄金ETF华安","short":"黄金","cat":"其他","market":"sh","backup":["159934","518800"]},
    {"code":"516360","name":"新材料ETF华宝","short":"新材料","cat":"其他","market":"sh","backup":["516710","516890"]},
]

def full_code(etf):
    return f"{etf['market']}{etf['code']}"

def fetch_fund_info(code):
    try:
        html = get(f"https://fundf10.eastmoney.com/jbgk_{code}.html")
        aum = None
        m = re.search(r'净资产规模.*?>([\d,]+\.?\d*)亿', html, re.DOTALL)
        if m: aum = float(m.group(1).replace(',', ''))
        mgmt = cust = None
        m = re.search(r'管理费率</th><td>([\d.]+)%', html)
        if m: mgmt = float(m.group(1))
        m = re.search(r'托管费率</th><td>([\d.]+)%', html)
        if m: cust = float(m.group(1))
        total_fee = round((mgmt or 0) + (cust or 0), 2)
        return {"aum": aum, "fee": total_fee if total_fee > 0 else None}
    except: return {}

def fetch_kline_qt(etf):
    fc = full_code(etf)
    try:
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={fc},day,,,120,qfq"
        d = json.loads(get(url, headers=H_EM))
        data_block = d.get("data", {}).get(fc, {})
        klines = data_block.get("qfqday", []) or data_block.get("day", [])
        closes = []
        for k in klines:
            if isinstance(k, list) and len(k) >= 3:
                closes.append({"date": k[0], "close": float(k[2]), "vol": float(k[5]) if len(k)>5 else 0})
            elif isinstance(k, str):
                parts = k.strip("[]'\"").split(',')
                if len(parts) >= 3:
                    closes.append({"date": parts[0].strip("'\""), "close": float(parts[2].strip("'\"")),
                                   "vol": float(parts[5].strip("'\"")) if len(parts)>5 else 0})
        if not closes: return {}
        latest = closes[-1]["close"]
        prices = [c["close"] for c in closes]
        ret = {}
        if len(prices) >= 5:  ret["1w"] = round((prices[-1]/prices[-5]-1)*100, 2)
        if len(prices) >= 22: ret["1m"] = round((prices[-1]/prices[-22]-1)*100, 2)
        if len(prices) >= 66: ret["3m"] = round((prices[-1]/prices[-66]-1)*100, 2)
        ytd_date = f"{time.strftime('%Y')}-01-02"
        ytd_close = next((c["close"] for c in closes if c["date"] >= ytd_date), None)
        if ytd_close and ytd_close > 0: ret["ytd"] = round((latest/ytd_close-1)*100, 2)
        ma20 = round(sum(prices[-20:])/20, 4) if len(prices)>=20 else None
        ma60 = round(sum(prices[-60:])/60, 4) if len(prices)>=60 else None
        qt_data = data_block.get("qt", {}).get(fc, [])
        pe = pb = None
        if isinstance(qt_data, list) and len(qt_data) > 46:
            try:
                pe = float(qt_data[39]) if qt_data[39] else None
                pb = float(qt_data[46]) if qt_data[46] else None
            except: pass
        trend_30 = [{"date": c["date"][-5:], "close": c["close"]} for c in closes[-30:]]
        result = {"price": latest, "vol": closes[-1].get("vol", 0), "returns": ret,
                  "ma20": ma20, "ma60": ma60, "pe": pe, "pb": pb, "trend_30": trend_30}
        if ma20: result["ma20_dev"] = round((latest/ma20-1)*100, 2)
        if ma60: result["ma60_dev"] = round((latest/ma60-1)*100, 2)
        return result
    except Exception as e: return {"_error": str(e)[:60]}

def fetch_sina(etf):
    fc = full_code(etf)
    try:
        raw = get(f"https://hq.sinajs.cn/list={fc}", "gbk")
        m = re.search(r'"([^"]*)"', raw)
        if m:
            parts = m.group(1).split(",")
            if len(parts) >= 6:
                price = float(parts[3]) if parts[3] else None
                prev = float(parts[2]) if parts[2] else None
                hi = float(parts[4]) if parts[4] else None
                lo = float(parts[5]) if parts[5] else None
                return {"price": price, "prev": prev, "high": hi, "low": lo}
    except: pass
    try:
        raw = get(f"http://qt.gtimg.cn/q={fc}", "gbk", t=5)
        fields = raw.split('~')
        if len(fields) > 40:
            return {"price": float(fields[3]) if fields[3] else None,
                    "prev": float(fields[4]) if fields[4] else None,
                    "pct": float(fields[32]) if fields[32] else None}
    except: pass
    return {}

H_SINA = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}

def fetch_backup_pcts(etfs_list):
    """批量获取所有备用ETF的涨跌幅"""
    # 收集所有备用代码 (去重)
    all_backups = []
    seen = set()
    for etf in etfs_list:
        for code in etf.get("backup", []):
            if code not in seen:
                seen.add(code)
                # 判断市场: 5开头=sh, 1/3开头=sz
                mkt = "sh" if code.startswith("5") or code.startswith("58") else "sz"
                all_backups.append({"code": code, "market": mkt})
    
    # 批量查询 (新浪一次最多几十个)
    batch_size = 20
    results = {}
    for i in range(0, len(all_backups), batch_size):
        batch = all_backups[i:i+batch_size]
        codes_str = ",".join(f"{b['market']}{b['code']}" for b in batch)
        try:
            raw = get(f"https://hq.sinajs.cn/list={codes_str}", "gbk", t=10, headers=H_SINA)
            # 新浪批量返回格式: var hq_str_shXXXX="...";\nvar hq_str_szYYYY="...";
            for m in re.finditer(r'var hq_str_..(\d+)="([^"]*)"', raw):
                code = m.group(1)
                parts = m.group(2).split(",")
                if len(parts) >= 4:
                    price = float(parts[3]) if parts[3] else None
                    prev = float(parts[2]) if parts[2] else None
                    if price and prev and prev > 0:
                        results[code] = round((price/prev-1)*100, 2)
        except: pass
    return results

def fetch_one(etf, backup_pcts={}):
    code = etf["code"]
    info = fetch_fund_info(code)
    kq = fetch_kline_qt(etf)
    sq = fetch_sina(etf)
    entry = {"code": code, "name": etf["name"], "short": etf["short"],
             "cat": etf["cat"], "backup": etf["backup"], "aum": info.get("aum"), "fee": info.get("fee")}
    if "_error" not in kq:
        entry["price"] = kq.get("price") or sq.get("price")
        entry["vol"] = kq.get("vol")
        entry["returns"] = kq.get("returns", {})
        entry["ma20"] = kq.get("ma20"); entry["ma20_dev"] = kq.get("ma20_dev")
        entry["ma60"] = kq.get("ma60"); entry["ma60_dev"] = kq.get("ma60_dev")
        entry["pe"] = kq.get("pe"); entry["pb"] = kq.get("pb")
        entry["trend_30"] = kq.get("trend_30", [])
    if sq.get("pct") is not None:
        entry["change_pct"] = sq["pct"]
    elif entry.get("price") and sq.get("prev") and sq["prev"] > 0:
        entry["change_pct"] = round((entry["price"]/sq["prev"]-1)*100, 2)
    if sq.get("high") and sq.get("low") and sq["low"] > 0:
        entry["amplitude"] = round((sq["high"]/sq["low"]-1)*100, 2)
    # 备用ETF涨跌幅
    entry["backup_pct"] = []
    for bc in etf.get("backup", []):
        if bc in backup_pcts:
            entry["backup_pct"].append({"code": bc, "pct": backup_pcts[bc]})
    return entry

def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "data.json")
    print(f"🔄 主题ETF赛道雷达 [{time.strftime('%H:%M')}] — 25只ETF并行采集\n", flush=True)
    # 先批量采集备用ETF涨跌幅
    backup_pcts = fetch_backup_pcts(ETFS)
    print(f"  📡 备用ETF涨跌幅: {len(backup_pcts)}只获取成功\n", flush=True)
    results = {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(fetch_one, e, backup_pcts): e for e in ETFS}
        for i, f in enumerate(as_completed(futures)):
            e = futures[f]
            try:
                entry = f.result()
                results[e["short"]] = entry
                pct = f'{entry.get("change_pct","?"):+.2f}%' if entry.get("change_pct") is not None else "?"
                aum_s = f'{entry.get("aum","?"):.0f}亿' if entry.get("aum") else "?"
                pe_s = f'{entry.get("pe","?"):.1f}' if entry.get("pe") else "?"
                print(f"  [{len(results):2d}/25] {e['short']:6s} {e['code']} | ¥{entry.get('price','?'):>8} | {pct:>8s} | AUM={aum_s:>6s} | PE={pe_s:>5s}", flush=True)
            except Exception as ex2:
                print(f"  [{len(results)+1:2d}/25] {e['short']:6s} ERROR: {ex2}", flush=True)
    output = {"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "etfs": [results[e["short"]] for e in ETFS if e["short"] in results]}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✅ {out_path} — {len(output['etfs'])}/25 成功", flush=True)

if __name__ == "__main__":
    import sys
    main()
