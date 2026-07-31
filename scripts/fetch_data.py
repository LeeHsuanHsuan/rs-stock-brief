"""
每日抓取美股/台股/籌碼資料，輸出成一份 JSON。
任何一項必要資料抓不到，整體視為失敗（ok=False），
由呼叫端決定當天要不要跳過摘要產生（容錯規則：寧可跳過，不硬湊數字）。
"""
import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import yfinance as yf

REQUIRED_KEYS = [
    "us_indices", "twse_index", "tpex_index",
    "institutional", "foreign_futures", "macro", "stocks",
]

TAIPEI_TZ = ZoneInfo("Asia/Taipei")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; RS-Stock-Brief/1.0)"}


def fetch_yf_index(ticker, days=10):
    t = yf.Ticker(ticker)
    hist = t.history(period=f"{days}d")
    closes = hist["Close"].dropna()
    if len(closes) < 2:
        return None
    last_close = round(float(closes.iloc[-1]), 2)
    change_pct = round((closes.iloc[-1] / closes.iloc[-2] - 1) * 100, 2)
    return {"close": last_close, "change_pct": change_pct}


def fetch_us_indices():
    tickers = {"dow": "^DJI", "nasdaq": "^IXIC", "sp500": "^GSPC", "sox": "^SOX"}
    out = {}
    for key, ticker in tickers.items():
        data = fetch_yf_index(ticker)
        if data is None:
            return None
        out[key] = data
    return out


def fetch_macro():
    tickers = {"dxy": "DX-Y.NYB", "usdtwd": "TWD=X", "us10y": "^TNX"}
    out = {}
    for key, ticker in tickers.items():
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        closes = hist["Close"].dropna()
        if closes.empty:
            return None
        out[key] = round(float(closes.iloc[-1]), 2)
    return out


def fetch_stocks():
    tickers = {
        "tsmc_2330": "2330.TW", "nvda": "NVDA", "tsla": "TSLA",
        "aapl": "AAPL", "tsm_adr": "TSM",
    }
    out = {}
    for key, ticker in tickers.items():
        data = fetch_yf_index(ticker)
        if data is None:
            return None
        out[key] = data
    return out


def _ma_block(closes):
    """closes: 由舊到新排序的收盤價 list"""
    if len(closes) < 2:
        return None
    last_close = closes[-1]
    prev_close = closes[-2]
    change_pct = round((last_close / prev_close - 1) * 100, 2)
    ma5 = round(sum(closes[-5:]) / len(closes[-5:]), 2) if len(closes) >= 5 else None
    ma10 = round(sum(closes[-10:]) / len(closes[-10:]), 2) if len(closes) >= 10 else None
    return {
        "close": round(last_close, 2),
        "change_pct": change_pct,
        "ma5": ma5,
        "ma10": ma10,
        "above_ma5": (last_close >= ma5) if ma5 is not None else None,
        "above_ma10": (last_close >= ma10) if ma10 is not None else None,
    }


def fetch_twse_index():
    """大盤：官方每日市場成交資訊，含收盤指數與成交金額，近一個月歷史一次拿到"""
    try:
        url = "https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?response=json"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("stat") != "OK":
            return None
        rows = payload["data"]
        closes = [float(r[4].replace(",", "")) for r in rows]
        block = _ma_block(closes)
        if block is None:
            return None
        latest_value = int(rows[-1][2].replace(",", ""))
        block["trading_value_billion"] = round(latest_value / 1e8, 1)
        block["trading_date"] = _roc_to_western(rows[-1][0])
        return block
    except Exception:
        return None


def _roc_to_western(roc_date):
    """民國日期 '115/07/31' 轉西元 '2026-07-31'"""
    year, month, day = roc_date.split("/")
    return f"{int(year) + 1911}-{month}-{day}"


def fetch_tpex_index():
    """櫃買指數：官方近一個月每日收盤，沒有官方成交金額端點，先略過該欄位"""
    try:
        url = "https://www.tpex.org.tw/openapi/v1/tpex_index"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        rows = resp.json()
        closes = [float(r["Close"]) for r in rows]
        block = _ma_block(closes)
        if block is None:
            return None
        block["trading_value_billion"] = None
        return block
    except Exception:
        return None


def fetch_institutional():
    """三大法人買賣超（單位：元）"""
    try:
        url = "https://www.twse.com.tw/rwd/zh/fund/BFI82U?response=json"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        rows = payload.get("data")
        if not rows:
            return None
        result = {}
        for row in rows:
            name = row[0]
            net = row[3].replace(",", "")
            result[name] = int(net)
        return result
    except Exception:
        return None


def fetch_foreign_futures():
    """外資在臺股期貨的未平倉淨部位（正數=淨多單，負數=淨空單），單位：口"""
    try:
        url = "https://openapi.taifex.com.tw/v1/MarketDataOfMajorInstitutionalTradersDetailsOfFuturesContractsBytheDate"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        rows = resp.json()
        for row in rows:
            if row.get("ContractCode") == "臺股期貨" and row.get("Item") == "外資及陸資":
                net = int(row["OpenInterest(Net)"])
                return {"date": row.get("Date"), "net_open_interest": net}
        return None
    except Exception:
        return None


def fetch_all():
    result = {
        "date": datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d"),
        "us_indices": fetch_us_indices(),
        "twse_index": fetch_twse_index(),
        "tpex_index": fetch_tpex_index(),
        "institutional": fetch_institutional(),
        "foreign_futures": fetch_foreign_futures(),
        "macro": fetch_macro(),
        "stocks": fetch_stocks(),
    }
    missing = [k for k in REQUIRED_KEYS if result.get(k) is None]
    result["ok"] = len(missing) == 0
    result["missing_fields"] = missing
    return result


if __name__ == "__main__":
    data = fetch_all()
    print(json.dumps(data, ensure_ascii=False, indent=2))
    if not data["ok"]:
        print(f"缺少資料: {data['missing_fields']}", file=sys.stderr)
        sys.exit(1)
