"""
把每日資料/摘要渲染成靜態 HTML，放進 docs/ 資料夾給 GitHub Pages 發布。
風格依照 html-preferences.md：白底黑字、無色塊、原生標題、極簡表格、無 JavaScript。
"""
import glob
import json
import os

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

BASE_STYLE = """
body {
  max-width: 720px;
  margin: 0 auto;
  padding: 2rem 1.25rem 4rem;
  font-family: "Noto Sans TC", -apple-system, BlinkMacSystemFont, sans-serif;
  line-height: 1.75;
  color: #1a1a1a;
  background: #ffffff;
}
h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
h2 { font-size: 1.2rem; margin-top: 2rem; }
p { margin: 1rem 0; white-space: pre-wrap; }
a { color: #1a1a1a; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
th, td { border: 1px solid #ddd; padding: 0.4rem 0.6rem; text-align: left; font-size: 0.95rem; }
.meta { color: #666; font-size: 0.9rem; margin-bottom: 1.5rem; }
.notice { border-left: 3px solid #ccc; background: #f7f7f7; padding: 0.75rem 1rem; color: #555; }
.back { display: inline-block; margin-top: 2rem; }
.up { color: #c0392b; }
.down { color: #1e8449; }
"""


def _fmt(value):
    if value is None:
        return "—"
    return f"{value:,.2f}"


def _change_cell(pct):
    if pct is None:
        return "<td>—</td>"
    cls = "up" if pct > 0 else "down" if pct < 0 else ""
    sign = "+" if pct > 0 else ""
    return f'<td class="{cls}">{sign}{pct}%</td>'


def render_index_table(record):
    rows = []
    us = record.get("us_indices") or {}
    twse = record.get("twse_index") or {}
    tpex = record.get("tpex_index") or {}
    stocks = record.get("stocks") or {}

    def row(name, close, pct, note=""):
        return f"<tr><td>{name}</td><td>{_fmt(close)}</td>{_change_cell(pct)}<td>{note}</td></tr>"

    entries = [
        ("道瓊工業指數", us.get("dow", {}).get("close"), us.get("dow", {}).get("change_pct"), ""),
        ("那斯達克指數", us.get("nasdaq", {}).get("close"), us.get("nasdaq", {}).get("change_pct"), ""),
        ("S&P500指數", us.get("sp500", {}).get("close"), us.get("sp500", {}).get("change_pct"), ""),
        ("費城半導體指數", us.get("sox", {}).get("close"), us.get("sox", {}).get("change_pct"), ""),
        ("台股大盤", twse.get("close"), twse.get("change_pct"),
         "站上5日線" if twse.get("above_ma5") else "跌破5日線"),
        ("櫃買指數", tpex.get("close"), tpex.get("change_pct"),
         "站上5日線" if tpex.get("above_ma5") else "跌破5日線"),
        ("台積電(2330)", stocks.get("tsmc_2330", {}).get("close"), stocks.get("tsmc_2330", {}).get("change_pct"), ""),
        ("NVDA", stocks.get("nvda", {}).get("close"), stocks.get("nvda", {}).get("change_pct"), ""),
        ("TSLA", stocks.get("tsla", {}).get("close"), stocks.get("tsla", {}).get("change_pct"), ""),
        ("AAPL", stocks.get("aapl", {}).get("close"), stocks.get("aapl", {}).get("change_pct"), ""),
        ("台積電ADR(TSM)", stocks.get("tsm_adr", {}).get("close"), stocks.get("tsm_adr", {}).get("change_pct"), ""),
    ]
    for name, close, pct, note in entries:
        rows.append(row(name, close, pct, note))

    return (
        "<table><tr><th>指數/資產</th><th>收盤價</th><th>漲跌</th><th>備註</th></tr>"
        + "".join(rows) + "</table>"
    )


def _page(title, body_html):
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{BASE_STYLE}</style>
</head>
<body>
{body_html}
</body>
</html>
"""


def render_day_page(record):
    date = record["date"]
    if not record.get("ok"):
        body = f"""
<h1>RS股市小幫手</h1>
<div class="meta">{date}</div>
<p class="notice">今日資料異常，暫無摘要。（缺少：{", ".join(record.get("missing_fields", []))}）</p>
<a class="back" href="index.html">回歷史紀錄</a>
"""
    else:
        summary = record["summary"].replace("\n\n", "</p><p>")
        table = render_index_table(record)
        body = f"""
<h1>RS股市小幫手</h1>
<div class="meta">{date}</div>
<h2>今日摘要</h2>
<p>{summary}</p>
<h2>指數總覽</h2>
{table}
<a class="back" href="index.html">回歷史紀錄</a>
"""
    return _page(f"RS股市小幫手 - {date}", body)


def render_index(records):
    records = sorted(records, key=lambda r: r["date"], reverse=True)
    rows = []
    for r in records:
        status = "" if r.get("ok") else "（資料異常）"
        rows.append(f'<tr><td><a href="{r["date"]}.html">{r["date"]}</a></td><td>{status}</td></tr>')
    table = "<table><tr><th>日期</th><th>備註</th></tr>" + "".join(rows) + "</table>"
    body = f"""
<h1>RS股市小幫手</h1>
<div class="meta">每日股市摘要歷史紀錄</div>
{table}
"""
    return _page("RS股市小幫手", body)


def render_all():
    os.makedirs(DOCS_DIR, exist_ok=True)
    records = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "*.json"))):
        with open(path, encoding="utf-8") as f:
            records.append(json.load(f))

    for record in records:
        html = render_day_page(record)
        with open(os.path.join(DOCS_DIR, f"{record['date']}.html"), "w", encoding="utf-8") as f:
            f.write(html)

    index_html = render_index(records)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)


if __name__ == "__main__":
    render_all()
    print(f"已輸出 {len(glob.glob(os.path.join(DOCS_DIR, '*.html')))} 個頁面到 docs/")
