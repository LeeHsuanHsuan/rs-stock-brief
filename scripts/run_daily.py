"""
每日主流程：抓資料 -> (成功則)生成摘要 -> 存檔 -> 重新渲染整個網站。
容錯規則：資料抓不齊全就跳過摘要生成，存一筆 ok=False 的紀錄，網站顯示「今日資料異常」。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_data import fetch_all
from generate_summary import generate_summary, _load_dotenv
from render_site import render_all

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def main():
    _load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    os.makedirs(DATA_DIR, exist_ok=True)

    data = fetch_all()
    record = dict(data)

    if data["ok"]:
        try:
            record["summary"] = generate_summary(data)
        except Exception as e:
            record["ok"] = False
            record["missing_fields"] = record.get("missing_fields", []) + [f"gemini生成失敗: {e}"]

    out_path = os.path.join(DATA_DIR, f"{data['date']}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    render_all()

    status = "成功" if record["ok"] else f"失敗（{record.get('missing_fields')}）"
    print(f"{data['date']} 執行{status}")


if __name__ == "__main__":
    main()
