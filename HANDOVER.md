# Session 交接記錄

## 最後更新
- 日期：2026-08-01（同一天內第二次更新，修了上線後發現的問題）
- 工作時間：本 session 完整討論（從需求訪談到上線，含上線後除錯）

---

## ✅ 本 Session 完成

- [x] 需求訪談確認範圍：全自動股市摘要網站，只給 Shannon 跟伴侶看
- [x] 建立專案資料夾 `projects/RS股市小幫手/`（獨立 git repo，不混在主 repo）
- [x] 開新 GitHub repo：`LeeHsuanHsuan/rs-stock-brief`（Public，免費方案）
- [x] 安裝並登入 GitHub CLI（`gh`，含 workflow 授權範圍）
- [x] 申請並驗證 Gemini API 金鑰（免費方案，存在本機 `.env` 跟 GitHub Secret `GEMINI_API_KEY`）
- [x] 寫 `scripts/fetch_data.py`：抓 Yahoo Finance（美股四指數、匯率、公債殖利率、5檔個股）+ TWSE（大盤、三大法人）+ TPEx（櫃買）+ TAIFEX（外資期貨未平倉）
- [x] 寫 `scripts/generate_summary.py`：用 Gemini 生成投顧語氣摘要，數字含千分位、法人金額轉億元
- [x] 寫 `scripts/render_site.py`：純白底黑字極簡風格網頁，指數表格（紅漲綠跌，台灣慣例）
- [x] 寫 `scripts/run_daily.py`：每日主流程，含容錯（資料不齊全就跳過）+ 交易日比對（自動跳過六日/國定假日休市，不用維護假日清單）
- [x] 設定 GitHub Actions 每日排程（台灣時間早上 7:00 自動跑）
- [x] 設定 GitHub Pages 發布（從 `/docs` 資料夾）
- [x] 手動觸發過一次 Actions，確認雲端自動化跑成功
- [x] 網站正式上線：**https://leehsuanhsuan.github.io/rs-stock-brief/**
- [x] 數字加千分位逗號（例如 13,112.23）
- [x] 指數/個股改用表格呈現（指數/資產、收盤價、漲跌、備註），紅漲綠跌（台灣慣例，跟美股相反）
- [x] 摘要與表格順序調整成「摘要在上、表格在下」
- [x] 外資期貨未平倉新增「較前一交易日增減」（比對自己存的歷史紀錄，不依賴外部 API）
- [x] 新增交易日比對機制，自動判斷六日/國定假日休市並跳過，不用維護假日清單
- [x] **修正排程整點延遲問題**：cron 從整點 `0 23 * * *` 改成錯開 `7 23 * * *`，避免 GitHub Actions 尖峰塞車延遲
- [x] **修正時區 bug（重要）**：GitHub 雲端伺服器預設 UTC 時區，跟台灣差 8 小時，導致排程在台灣時間早上執行時把日期算成前一天，蓋掉舊檔案而非新增一筆。已改成明確用 `Asia/Taipei` 時區計算日期，雲端驗證通過
- [x] 摘要開頭固定改成「全國各位投資朋友們大家好：」（跟 Shannon 提供的原始範例一致）

---

## ⏳ 待辦清單（Shannon 之前主動說先跳過，之後想加再做）

- [ ] 跳空缺口理論判讀（多方缺口/空方缺口）
- [ ] 個股籌碼排行榜（成交量排名、外資/投信買超賣超前40檔）
- [ ] 產業/題材評論（例如「資金轉往蘋果概念股」這種）— **這塊風險最高，AI 沒有即時新聞會容易瞎掰，之後做的話要另外設計資料來源**
- [ ] 追蹤清單客製化（目前固定用範例清單，還沒開放自訂個股）
- [ ] 櫃買成交金額（目前找不到穩定官方免費端點，先跳過這個數字）

---

## 📝 重要決定或發現

- **只有 Shannon 跟伴侶看**，不對外公開宣傳，所以摘要語氣可以完全模仿範例（含技術判讀、預測語句），法律風險低
- **資料來源都是免費/官方**：Yahoo Finance（非官方但穩定）+ TWSE/TPEx/TAIFEX 公開資訊觀測站（官方免費）
- **容錯原則**：寧可跳過、不硬湊數字。資料抓不齊全 → 顯示「今日資料異常」；沒有新交易日資料（六日/假日）→ 直接跳過不產生重複的一筆
- **視覺風格**：曾經考慮改成 growin 那種色塊卡片風格，Shannon **明確選擇維持極簡白底黑字**（`_context/rules/html-preferences.md` 規則不變），只在漲跌數字上用紅/綠（台灣慣例：紅漲綠跌，不是美股的綠漲紅跌）
- **Gemini API 金鑰格式**：這組金鑰開頭是 `AQ.` 不是熟悉的 `AIzaSy...`，一開始以為是錯的，測試後確認是新格式，能正常用。可用模型要用 `gemini-flash-latest`（舊的 `gemini-2.0-flash`／`gemini-2.5-flash` 已經對新帳號關閉）
- **外資期貨/櫃買的「增減」數字**：官方 API 沒有方便的歷史比對端點，改成用自己存的 `data/*.json` 歷史紀錄比對前一筆，比依賴外部 API 更可靠
- 本機這台電腦的 `~/.config` 資料夾被系統設成 root 擁有，一般帳號沒寫入權限，所以 `gh` 的設定改存在 `~/.gh-config`（用 `GH_CONFIG_DIR` 環境變數指定），之後在本機用 `gh` 指令要記得帶這個變數
- **時區是本專案最容易踩的坑**：只要之後新增任何「跟日期有關」的邏輯，一定要用 `datetime.now(TAIPEI_TZ)`（`fetch_data.py` 已定義），不要用系統原生 `datetime.now()`，不然雲端伺服器（UTC）會算錯日期
- 上線第一天（週六）觀察到：排程整點容易延遲 + 時區算錯日期，兩個問題疊加讓 Shannon 誤以為「今天沒更新」。這兩個都已修正並在雲端驗證過，之後週一早上第一次真正的排程執行要留意有沒有正常跑（見下方提醒）

---

## 🔔 給下個 Session 的提醒

- Shannon 不熟技術細節，解釋要用白話
- `.env` 裡有真實的 Gemini API 金鑰，**不要隨便覆蓋或印出全文**，要改動先給 Shannon 看內容
- 本機測試指令：
  ```
  cd "projects/RS股市小幫手"
  source .venv/bin/activate
  python3 scripts/run_daily.py
  ```
- 手動觸發雲端排程：`gh workflow run daily.yml --repo LeeHsuanHsuan/rs-stock-brief`（記得帶 `GH_CONFIG_DIR="$HOME/.gh-config"`）
- 之後如果要加「進階版」內容（缺口理論、個股籌碼排行、產業評論），產業評論那塊要先想好怎麼避免 AI 瞎掰
- **下次開新 session，先確認週一早上（第一個真正交易日）排程有沒有正常跑出新的一筆**，確認方式：`gh run list --repo LeeHsuanHsuan/rs-stock-brief --workflow daily.yml --limit 5`，看有沒有 `event: schedule` 且 `conclusion: success` 的紀錄，並檢查 `data/` 裡有沒有新增當天日期的 json

---

## 🎯 下個 Session 的目標（如果 Shannon 主動提）

- 觀察實際跑幾天，確認每天早上 7 點自動更新是否穩定
- 依 Shannon 回饋調整摘要語氣或版面細節
- 視需求評估要不要開始做「進階版」的缺口理論或個股籌碼排行

---

## 📁 專案檔案清單

| 檔案/資料夾 | 說明 |
|---|---|
| `scripts/fetch_data.py` | 抓美股/台股/籌碼資料 |
| `scripts/generate_summary.py` | 呼叫 Gemini 生成摘要文字 |
| `scripts/render_site.py` | 渲染成靜態 HTML |
| `scripts/run_daily.py` | 每日主流程（容錯 + 假日判斷） |
| `.github/workflows/daily.yml` | GitHub Actions 排程設定 |
| `data/*.json` | 每日原始資料 + 摘要（歷史紀錄，會一直累積） |
| `docs/*.html` | 網站頁面（GitHub Pages 直接發布這個資料夾） |
| `.env` | 本機測試用的 Gemini API 金鑰（不會上傳 GitHub） |
| `requirements.txt` | Python 套件清單 |

**線上網址**：https://leehsuanhsuan.github.io/rs-stock-brief/
**GitHub repo**：https://github.com/LeeHsuanHsuan/rs-stock-brief
