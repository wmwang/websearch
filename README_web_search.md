# Cline Web Search Skill — 使用說明

透過 Playwright headless browser 到 Brave Search 搜尋，擷取搜尋結果供 Cline 使用。不依賴任何付費搜尋 API。

## 安裝相依

在準備執行腳本的 Python 環境下執行：

```bash
pip install playwright>=1.40.0
playwright install chromium
```

> **注意**：不需要進行複雜的 project install，這只是一支獨立的 Python 腳本。

## 測試執行

```bash
# 基本搜尋
python skills/web-search/script/web_search_playwright.py "Playwright Python examples"

# 限制回傳筆數
python skills/web-search/script/web_search_playwright.py "Python asyncio tutorial" --max-results 3

# 指定引擎（支援 brave 和 duckduckgo）
python skills/web-search/script/web_search_playwright.py "React hooks best practices" --engine brave

# 透過 proxy 搜尋
python skills/web-search/script/web_search_playwright.py "Python asyncio tutorial" --proxy "http://proxy.company.com:8080"
```

### 預期輸出

```
Query: Spring Boot WebClient timeout official docs

[1] Title here
URL: https://example.com/page1
Snippet: summary text...

[2] Another title
URL: https://example.com/page2
Snippet: summary text...
```

## 整合說明 (Skill 標準封裝)

這是一個標準的 Cline / Agent Skill 資料夾結構，整包 `web-search` 可以直接 shard 給任何 Agent 使用。

1. 直接將整個 `skills/web-search/` 資料夾複製或掛載給你的 LLM Agent 工作區。
2. 將 `SKILL.md` 註冊或設定為 Agent 的 Prompt。
3. Agent 遇到需要查網頁的時候，就會自動讀取 `SKILL.md`，並使用它隨附在 `script/` 下的 Python 腳本完成搜尋。

### 目錄結構

```
你的專案或 Agent 統一存放 Skills 的目錄/
└─ web-search/                  <-- 將這整包 shard/複製 出去
   ├─ SKILL.md                  <-- 教導 AI 如何自主尋找並執行腳本
   └─ script/
      └─ web_search_playwright.py  <-- 隨附的執行腳本
```

## 錯誤碼

| Exit Code | 意義 |
|-----------|------|
| 0 | 正常完成（含找不到結果） |
| 1 | 未提供搜尋字串 |
| 2 | Playwright / Browser 啟動失敗 |
| 3 | 頁面載入 timeout |
| 9 | 其他未預期錯誤 |

## 已知限制

- **DOM 依賴**：依賴 Brave Search 搜尋頁面 DOM 結構，頁面改版可能導致解析失敗
- **穩定性**：無法保證所有搜尋結果都能穩定擷取
- **範圍**：只擷取搜尋結果列表，不抓取網頁全文內容
- **網路限制**：公司網路若封鎖外部搜尋網站，則無法使用
- **反爬蟲**：不具備反爬蟲對抗能力，高頻使用可能被暫時封鎖
