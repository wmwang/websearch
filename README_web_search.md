# Cline Web Search Skill — 使用說明

透過 Playwright headless browser 到 Brave Search 搜尋，擷取搜尋結果供 Cline 使用。不依賴任何付費搜尋 API。

## 安裝

```bash
# 安裝 Python 相依套件
pip install -r requirements.txt

# 安裝 Playwright Chromium 瀏覽器
playwright install chromium
```

> **前提**：Python 3.11 以上

## 測試執行

```bash
# 基本搜尋
python .cline/tools/web_search_playwright.py "Spring Boot WebClient timeout official docs"

# 限制回傳筆數
python .cline/tools/web_search_playwright.py "Python asyncio tutorial" --max-results 3

# 指定引擎（支援 brave 和 duckduckgo）
python .cline/tools/web_search_playwright.py "React hooks best practices" --engine brave

# 透過 proxy 搜尋（若在公司內部網路等受限環境）
python .cline/tools/web_search_playwright.py "Python asyncio tutorial" --proxy "http://proxy.company.com:8080"
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

## Cline Skill 整合

1. 將 `SKILL.md` 放到 `.cline/skills/web-search/`
2. 將 `web_search_playwright.py` 放到 `.cline/tools/`
3. 在 Cline 對話中，當需要查最新文件、近期資訊、外部文件時，Cline 會自動使用此 skill

### 目錄結構

```
project-root/
├─ .cline/
│  ├─ skills/
│  │  └─ web-search/
│  │     └─ SKILL.md
│  └─ tools/
│     └─ web_search_playwright.py
├─ requirements.txt
└─ README_web_search.md
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
