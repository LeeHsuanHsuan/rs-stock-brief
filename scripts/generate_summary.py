"""
把 fetch_data.py 抓到的數字丟給 Gemini，生成一篇跟範例語氣一致的每日摘要。
只根據傳入的數字做技術面判讀（均線是否有守），不編造新聞或數字以外的資訊。
"""
import os
import sys
import json
import requests

GEMINI_MODEL = "gemini-flash-latest"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

PROMPT_TEMPLATE = """你是一位台股投顧研究員，每天早上要寫一則給熟客看的股市摘要，語氣口語、專業，會做技術面判讀（例如「觀察5日線是否能持續有守，守住的話就能再往上挑戰創高」這種句型）。

嚴格規則：
1. 只能使用下面提供的數字，不能編造任何新聞、消息面、產業評論或這些數字以外的資訊。
2. 技術判讀只能根據「收盤價 vs 5日線/10日線」的相對關係去寫，不要提到跳空缺口、成交量排名等沒有提供的資料。
3. 格式仿照範例：先美股段落，再大盤段落，再櫃買段落，再資金籌碼面段落，再持續觀察指標段落，最後美股科技股/個股段落。
4. 不要加任何 Markdown 符號（不要用 **、#、-），純文字段落，段落之間空一行。
5. 數字裡的千分位逗號（例如 13,112.23）要原樣保留，不要拿掉。
6. 第一句話固定用「全國各位投資朋友們大家好：」開頭，不要用其他問候語（不要用「早安」「大家早」等）。

今天日期：{date}

【美股】
道瓊 收盤{dow_close} 漲跌{dow_pct}%
那斯達克 收盤{nasdaq_close} 漲跌{nasdaq_pct}%
S&P500 收盤{sp500_close} 漲跌{sp500_pct}%
費半(SOX) 收盤{sox_close} 漲跌{sox_pct}%

【台股大盤】
收盤{twse_close} 漲跌{twse_pct}% 5日線{twse_ma5} 10日線{twse_ma10} 站上5日線:{twse_above5} 站上10日線:{twse_above10}
大盤成交金額 約{twse_value}億

【櫃買】
收盤{tpex_close} 漲跌{tpex_pct}% 5日線{tpex_ma5} 10日線{tpex_ma10} 站上5日線:{tpex_above5} 站上10日線:{tpex_above10}

【三大法人買賣超(億元，正數為買超)】
自營商(自行買賣) {dealer_self}
自營商(避險) {dealer_hedge}
投信 {trust}
外資及陸資 {foreign}

【外資期貨】
臺股期貨未平倉淨部位 {foreign_futures_net}口（負數代表淨空單）
較前一交易日{foreign_futures_change}

【持續觀察指標】
美元指數 {dxy}
台幣匯率(1美元兌台幣) {usdtwd}
美國10年期公債殖利率 {us10y}%

【個股】
台積電(2330) 收盤{tsmc_close} 漲跌{tsmc_pct}%
NVDA 收盤{nvda_close} 漲跌{nvda_pct}%
TSLA 收盤{tsla_close} 漲跌{tsla_pct}%
AAPL 收盤{aapl_close} 漲跌{aapl_pct}%
台積電ADR(TSM) 收盤{tsm_close} 漲跌{tsm_pct}%

請直接輸出摘要內容，不要有開場白或「好的，以下是摘要」這類文字。
"""


def _to_yi(value):
    if value is None:
        return "未知"
    return round(value / 1e8, 1)


def _fmt(value):
    """數字加千分位逗號，例如 13112.23 -> 13,112.23"""
    if value is None:
        return "未知"
    return f"{value:,.2f}"


def _fmt_int(value):
    if value is None:
        return "未知"
    return f"{value:,}"


def _ff_change_text(ff):
    change = ff.get("change_from_prev")
    if change is None:
        return "（沒有前一交易日資料可比對，略過）"
    if change > 0:
        return f"增加{_fmt_int(change)}口"
    if change < 0:
        return f"減少{_fmt_int(abs(change))}口"
    return "持平"


def build_prompt(data):
    us = data["us_indices"]
    twse = data["twse_index"]
    tpex = data["tpex_index"]
    inst = data["institutional"]
    ff = data["foreign_futures"]
    macro = data["macro"]
    stocks = data["stocks"]

    return PROMPT_TEMPLATE.format(
        date=data["date"],
        dow_close=_fmt(us["dow"]["close"]), dow_pct=us["dow"]["change_pct"],
        nasdaq_close=_fmt(us["nasdaq"]["close"]), nasdaq_pct=us["nasdaq"]["change_pct"],
        sp500_close=_fmt(us["sp500"]["close"]), sp500_pct=us["sp500"]["change_pct"],
        sox_close=_fmt(us["sox"]["close"]), sox_pct=us["sox"]["change_pct"],
        twse_close=_fmt(twse["close"]), twse_pct=twse["change_pct"],
        twse_ma5=_fmt(twse["ma5"]), twse_ma10=_fmt(twse["ma10"]),
        twse_above5="是" if twse["above_ma5"] else "否",
        twse_above10="是" if twse["above_ma10"] else "否",
        twse_value=twse.get("trading_value_billion", "未知"),
        tpex_close=_fmt(tpex["close"]), tpex_pct=tpex["change_pct"],
        tpex_ma5=_fmt(tpex["ma5"]), tpex_ma10=_fmt(tpex["ma10"]),
        tpex_above5="是" if tpex["above_ma5"] else "否",
        tpex_above10="是" if tpex["above_ma10"] else "否",
        dealer_self=_to_yi(inst.get("自營商(自行買賣)")),
        dealer_hedge=_to_yi(inst.get("自營商(避險)")),
        trust=_to_yi(inst.get("投信")),
        foreign=_to_yi(inst.get("外資及陸資(不含外資自營商)")),
        foreign_futures_net=_fmt_int(ff["net_open_interest"]),
        foreign_futures_change=_ff_change_text(ff),
        dxy=macro["dxy"], usdtwd=macro["usdtwd"], us10y=macro["us10y"],
        tsmc_close=_fmt(stocks["tsmc_2330"]["close"]), tsmc_pct=stocks["tsmc_2330"]["change_pct"],
        nvda_close=_fmt(stocks["nvda"]["close"]), nvda_pct=stocks["nvda"]["change_pct"],
        tsla_close=_fmt(stocks["tsla"]["close"]), tsla_pct=stocks["tsla"]["change_pct"],
        aapl_close=_fmt(stocks["aapl"]["close"]), aapl_pct=stocks["aapl"]["change_pct"],
        tsm_close=_fmt(stocks["tsm_adr"]["close"]), tsm_pct=stocks["tsm_adr"]["change_pct"],
    )


def generate_summary(data, api_key=None):
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("找不到 GEMINI_API_KEY，請確認環境變數或 .env 有設定")

    prompt = build_prompt(data)
    resp = requests.post(
        f"{GEMINI_URL}?key={api_key}",
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json()
    text = payload["candidates"][0]["content"]["parts"][0]["text"]
    return text.strip()


def _load_dotenv(path=".env"):
    if not os.path.exists(path):
        return
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v)


if __name__ == "__main__":
    _load_dotenv()
    from fetch_data import fetch_all

    data = fetch_all()
    if not data["ok"]:
        print(f"資料不齊全，無法生成摘要: {data['missing_fields']}", file=sys.stderr)
        sys.exit(1)

    summary = generate_summary(data)
    print(summary)
