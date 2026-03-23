---
name: web-search
description: 透過 Playwright headless browser 進行網路搜尋，取得最新資訊與外部文件
---

# Web Search Skill

## 何時使用

當遇到以下情況時，應優先使用此 skill：

- 使用者要求「最新」、「目前」、「最近」的資訊
- 問題涉及外部文件、官方文件、套件版本、近期公告
- 錯誤訊息可能需要查網路上的官方文件或 GitHub issue
- 在 codebase 內完全找不到答案
- 需要確認某個技術方案是否仍為目前推薦做法

## 呼叫方式

本 Skill 隨附的執行腳本放置於同層的 `script/web_search_playwright.py`。
請透過 Python 執行該腳本。

> **【重要】動態尋址原則**：
> 當你（Agent）需要呼叫此搜尋功能時，**必須先找出目前這個 `SKILL.md` 檔案的絕對路徑**，再替換為 `script/web_search_playwright.py` 以執行腳本。
> 絕對不要寫死路徑，因為這個資料夾可能被安置在任意工作區（例如 `.cline/skills/web-search/` 或其他地方）。

舉例（假設目前 SKILL.md 位於 `/xxx/skills/web-search/SKILL.md`）：

```bash
python /xxx/skills/web-search/script/web_search_playwright.py "<query>"
```

> 預設使用 Brave Search 引擎。

### 可選參數

```bash
# 限制回傳筆數（預設 5）
python <SKILL絕對路徑>/script/web_search_playwright.py "<query>" --max-results 3

# 指定搜尋引擎（預設 brave，可用 duckduckgo）
python <SKILL絕對路徑>/script/web_search_playwright.py "<query>" --engine brave
```

### 網路異常與 Proxy 設定

> **Skill Execution 核心原則**：若發生連線錯誤（如 `page load timeout`、無網路回應）且可能處於受限網路（如公司環境），**絕對不要盲目猜測或自動套用隨機的 proxy**。

1. **詢問使用者**：立即向使用者確認是否在公司網路，並請其提供正確的 Proxy URL。
2. **手動帶入參數**：取得使用者提供的 Proxy 後，使用 `--proxy` 參數重新搜尋：
```bash
python <SKILL絕對路徑>/script/web_search_playwright.py "<query>" --proxy "http://proxy.company.com:8080"
```
（註：腳本執行時也會自動讀取 `HTTPS_PROXY` / `HTTP_PROXY` 環境變數）

## 查詢語言規則

1. **預設使用英文查詢**，英文搜尋結果通常涵蓋面更廣
2. 若主題明確是中文在地內容（如台灣法律、中文套件文件），可使用繁體中文查詢
3. 查詢字串應盡量精簡，避免過長的自然語言句子
4. 建議加入關鍵技術詞彙，例如 `"Spring Boot WebClient timeout official docs"`

## 結果使用規則

1. **先讀搜尋結果再回答** — 不要在拿到結果前就開始回答
2. **引用來源 URL** — 回答時應附上找到的來源連結
3. **可改寫 query 再查一次** — 若結果不佳，嘗試用不同關鍵字重新搜尋
4. **不要對搜尋結果過度自信** — 搜尋結果可能過時或不準確，應交叉驗證
5. **優先使用官方來源** — 若結果中有官方文件連結，優先參考該來源

## 輸出格式範例

```
Query: Spring Boot WebClient timeout official docs

[1] Title here
URL: https://example.com/page1
Snippet: summary text...

[2] Another title
URL: https://example.com/page2
Snippet: summary text...
```

## 前置條件

使用前必須確保你在目前用來跑指令的 Python 環境（如 `.venv`）中安裝 Playwright：

```bash
pip install playwright>=1.40.0
playwright install chromium
```

## 限制

- 依賴 Brave Search 搜尋頁 DOM 結構，未來頁面改版可能導致解析失敗
- 只擷取搜尋結果列表，不會抓取網頁全文內容
- 公司網路若封鎖外部搜尋網站則無法使用
- 不具備反爬蟲對抗能力
