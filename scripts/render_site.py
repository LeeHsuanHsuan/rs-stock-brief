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
"""


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
        body = f"""
<h1>RS股市小幫手</h1>
<div class="meta">{date}</div>
<p>{summary}</p>
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
