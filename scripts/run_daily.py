"""
每日主流程：抓資料 -> 比對前一筆歷史算增減 -> (成功則)生成摘要 -> 存檔 -> 重新渲染整個網站。
容錯規則：資料抓不齊全就跳過摘要生成，存一筆 ok=False 的紀錄，網站顯示「今日資料異常」。
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_data import fetch_all
from generate_summary import generate_summary, _load_dotenv
from render_site import render_all

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def _load_previous_records(current_date):
    """回傳所有已存在的歷史紀錄（含今天若已跑過一次），由新到舊排序"""
    paths = sorted(glob.glob(os.path.join(DATA_DIR, "*.json")), reverse=True)
    records = []
    for path in paths:
        file_date = os.path.basename(path).replace(".json", "")
        if file_date > current_date:
            continue
        with open(path, encoding="utf-8") as f:
            records.append(json.load(f))
    return records


def _find_previous_foreign_futures_net(previous_records):
    """找最近一筆有外資期貨資料的紀錄，回傳其淨部位口數"""
    for prev in previous_records:
        ff = prev.get("foreign_futures")
        if ff and ff.get("net_open_interest") is not None:
            return ff["net_open_interest"]
    return None


def _is_same_trading_day_as_last_run(data, previous_records):
    """比對交易所實際公布的交易日期，跟上一筆紀錄一樣就代表沒有新資料（六日/國定假日休市）"""
    twse = data.get("twse_index") or {}
    trading_date = twse.get("trading_date")
    if not trading_date or not previous_records:
        return False
    last_trading_date = (previous_records[0].get("twse_index") or {}).get("trading_date")
    return trading_date == last_trading_date


def main():
    _load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    os.makedirs(DATA_DIR, exist_ok=True)

    data = fetch_all()
    previous_records = _load_previous_records(data["date"])

    if data["ok"] and _is_same_trading_day_as_last_run(data, previous_records):
        print(f"{data['date']} 尚無新交易日資料（休市），跳過不產生新的一筆")
        return

    record = dict(data)

    if data.get("foreign_futures"):
        prev_net = _find_previous_foreign_futures_net(previous_records)
        record["foreign_futures"] = dict(data["foreign_futures"])
        record["foreign_futures"]["change_from_prev"] = (
            data["foreign_futures"]["net_open_interest"] - prev_net
            if prev_net is not None else None
        )

    if data["ok"]:
        try:
            record["summary"] = generate_summary(record)
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
