#!/usr/bin/env python3
"""
Cline Web Search Tool — 使用 Playwright headless browser 進行網路搜尋

用法：
    python web_search_playwright.py "<query>"
    python web_search_playwright.py "<query>" --max-results 3
    python web_search_playwright.py "<query>" --engine brave
"""

import argparse
import os
import sys
import urllib.parse

# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------
EXIT_OK = 0
EXIT_USAGE = 1
EXIT_BROWSER_FAIL = 2
EXIT_TIMEOUT = 3
EXIT_UNEXPECTED = 9

# ---------------------------------------------------------------------------
# Browser 偽裝設定
# ---------------------------------------------------------------------------
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_VIEWPORT = {"width": 1280, "height": 800}

# ---------------------------------------------------------------------------
# 搜尋引擎 URL 建構
# ---------------------------------------------------------------------------

def build_search_url(query: str, engine: str = "brave") -> str:
    """根據搜尋引擎與查詢字串產生搜尋 URL。"""
    encoded = urllib.parse.quote_plus(query)
    urls = {
        "brave": f"https://search.brave.com/search?q={encoded}",
        "duckduckgo": f"https://duckduckgo.com/?q={encoded}",
    }
    return urls.get(engine, urls["brave"])

# ---------------------------------------------------------------------------
# 搜尋結果解析（多層 fallback selector）
# ---------------------------------------------------------------------------

def parse_results(page, max_results: int = 5, engine: str = "brave") -> list[dict]:
    """
    從搜尋結果頁面解析搜尋結果。

    實作三組 fallback selector 策略，以應對 DOM 變動。
    """
    if engine == "brave":
        return _parse_brave(page, max_results)
    return _parse_duckduckgo(page, max_results)


def _parse_brave(page, max_results: int) -> list[dict]:
    """解析 Brave Search 搜尋結果。"""
    results: list[dict] = []

    # ── 策略 1：div.snippet[data-type="web"] — 最精確 ──
    try:
        web_snippets = page.query_selector_all('div.snippet[data-type="web"]')
        if web_snippets:
            for snip in web_snippets:
                result = _extract_brave_snippet(snip)
                if result and result.get("url"):
                    results.append(result)
                if len(results) >= max_results:
                    break
            if results:
                return results[:max_results]
    except Exception:
        pass

    # ── 策略 2：div.snippet（含所有類型）──
    try:
        all_snippets = page.query_selector_all("div.snippet")
        if all_snippets:
            for snip in all_snippets:
                result = _extract_brave_snippet(snip)
                if result and result.get("url") and not _is_excluded_url(result["url"]):
                    results.append(result)
                if len(results) >= max_results:
                    break
            if results:
                return results[:max_results]
    except Exception:
        pass

    # ── 策略 3：fallback — #results 區域內所有外部連結 ──
    try:
        container_selectors = [
            '#results a[href^="http"]',
            'a[href^="http"]',
        ]
        for sel in container_selectors:
            anchors = page.query_selector_all(sel)
            if not anchors:
                continue
            seen_urls: set[str] = set()
            for anchor in anchors:
                href = (anchor.get_attribute("href") or "").strip()
                if not href or _is_excluded_url(href):
                    continue
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                title = (anchor.inner_text() or "").strip()
                if title and len(title) > 5:
                    results.append({"title": title, "url": href, "snippet": ""})
                if len(results) >= max_results:
                    break
            if results:
                return results[:max_results]
    except Exception:
        pass

    return results[:max_results]


def _extract_brave_snippet(snip) -> dict:
    """從 Brave Search 的 snippet 區塊擷取 title / url / snippet。"""
    title = ""
    url = ""
    snippet = ""

    # 取得 URL（從第一個 <a> 的 href）
    anchor = snip.query_selector("a[href^='http']")
    if anchor:
        url = (anchor.get_attribute("href") or "").strip()

    # 取得標題 — 使用 div.title 或 div.search-snippet-title
    title_selectors = [
        "div.title",
        "div.search-snippet-title",
        "span.snippet-title",
    ]
    for sel in title_selectors:
        el = snip.query_selector(sel)
        if el:
            text = (el.inner_text() or "").strip()
            if text:
                title = text
                break

    # 若標題仍為空，從 anchor 的完整文字中提取（排除網站名和 URL）
    if not title and anchor:
        text = (anchor.inner_text() or "").strip()
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        # 通常網站名是第一行，URL 是第二行，標題可能在 div.title 裡（已嘗試上面）
        # 用最長行作為 fallback
        if lines:
            title = max(lines, key=len)

    # 取得 snippet 描述
    snippet_selectors = [
        "div.generic-snippet div.content",
        "div.generic-snippet",
        "div.snippet-description",
        "p.snippet-description",
    ]
    for sel in snippet_selectors:
        el = snip.query_selector(sel)
        if el:
            text = (el.inner_text() or "").strip()
            if text and text != title and len(text) > 5:
                snippet = text
                break

    return _clean_result(title, url, snippet)


def _parse_duckduckgo(page, max_results: int) -> list[dict]:
    """解析 DuckDuckGo 搜尋結果（備用引擎）。"""
    results: list[dict] = []

    # 策略 1：article[data-testid="result"]
    try:
        articles = page.query_selector_all('article[data-testid="result"]')
        for article in articles:
            title_el = article.query_selector('a[data-testid="result-title-a"]')
            snippet_el = article.query_selector('[data-testid="result-snippet"]')
            if title_el:
                url = (title_el.get_attribute("href") or "").strip()
                title = (title_el.inner_text() or "").strip()
                snippet = (snippet_el.inner_text() or "").strip() if snippet_el else ""
                if url and not _is_excluded_url(url):
                    results.append(_clean_result(title, url, snippet))
            if len(results) >= max_results:
                break
        if results:
            return results[:max_results]
    except Exception:
        pass

    # 策略 2：h2 a
    try:
        links = page.query_selector_all("h2 a[href^='http']")
        for link in links:
            url = (link.get_attribute("href") or "").strip()
            title = (link.inner_text() or "").strip()
            if url and title and not _is_excluded_url(url):
                results.append(_clean_result(title, url, ""))
            if len(results) >= max_results:
                break
    except Exception:
        pass

    return results[:max_results]


# ---------------------------------------------------------------------------
# 工具函式
# ---------------------------------------------------------------------------

_EXCLUDED_URL_PATTERNS = [
    "duckduckgo.com",
    "duck.ai",
    "search.brave.com",
    "brave.com/download",
    "brave.com/search",
    "apple.com/app/duckduckgo",
    "play.google.com/store/apps/details?id=com.duckduckgo",
    "insideduckduckgo.substack.com",
    "reddit.com/r/duckduckgo",
    "spreadprivacy.com",
]


def _is_excluded_url(url: str) -> bool:
    """檢查 URL 是否為搜尋引擎自身的連結。"""
    lower = url.lower()
    return any(pat in lower for pat in _EXCLUDED_URL_PATTERNS)


def _clean_result(title: str, url: str, snippet: str) -> dict:
    """清理並正規化單筆搜尋結果。"""
    title = " ".join(title.split()) if title else ""
    snippet = " ".join(snippet.split()) if snippet else ""
    url = url.strip() if url else ""
    return {"title": title, "url": url, "snippet": snippet}

# ---------------------------------------------------------------------------
# 搜尋引擎查詢
# ---------------------------------------------------------------------------

def _resolve_proxy(proxy: str | None) -> str | None:
    """解析 proxy 設定：優先使用明確參數，否則 fallback 到環境變數。"""
    if proxy:
        return proxy
    return (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("http_proxy")
    )


def fetch_results(
    query: str,
    max_results: int = 5,
    engine: str = "brave",
    proxy: str | None = None,
) -> list[dict]:
    """
    啟動 Playwright headless Chromium，執行搜尋並回傳結果。

    Args:
        proxy: Proxy URL，例如 "http://proxy.company.com:8080"。
               若未提供，會自動讀取 HTTPS_PROXY / HTTP_PROXY 環境變數。

    Raises:
        SystemExit: 當 browser 啟動失敗 (exit 2) 或 timeout (exit 3)
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    except ImportError:
        print(
            "ERROR: playwright 套件未安裝。請執行：pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        sys.exit(EXIT_BROWSER_FAIL)

    resolved_proxy = _resolve_proxy(proxy)
    url = build_search_url(query, engine)
    browser = None
    playwright_ctx = None

    try:
        playwright_ctx = sync_playwright().start()

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ]
        # Proxy 設定
        launch_kwargs: dict = {"headless": True, "args": launch_args}
        if resolved_proxy:
            launch_kwargs["proxy"] = {"server": resolved_proxy}

        browser = playwright_ctx.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            user_agent=_USER_AGENT,
            viewport=_VIEWPORT,
            locale="en-US",
        )
        page = context.new_page()
        # 隱藏 webdriver 標記，降低被偵測為 bot 的機率
        page.add_init_script(
            'Object.defineProperty(navigator, "webdriver", { get: () => undefined });'
        )
        page.set_default_timeout(30_000)  # 30 秒 timeout

        page.goto(url, wait_until="domcontentloaded")
        # 等待搜尋結果載入
        page.wait_for_timeout(3000)

        results = parse_results(page, max_results, engine)
        return results

    except PlaywrightTimeout:
        print("ERROR: page load timeout", file=sys.stderr)
        sys.exit(EXIT_TIMEOUT)
    except Exception as e:
        error_msg = str(e)
        if any(
            kw in error_msg.lower()
            for kw in ("browser", "executable", "launch", "chromium")
        ):
            print(f"ERROR: browser 啟動失敗 — {error_msg}", file=sys.stderr)
            sys.exit(EXIT_BROWSER_FAIL)
        raise
    finally:
        if browser:
            try:
                browser.close()
            except Exception:
                pass
        if playwright_ctx:
            try:
                playwright_ctx.stop()
            except Exception:
                pass

# ---------------------------------------------------------------------------
# 輸出格式化
# ---------------------------------------------------------------------------

def format_results(query: str, results: list[dict]) -> str:
    """將搜尋結果格式化為純文字輸出。"""
    lines = [f"Query: {query}", ""]

    if not results:
        lines.append("No results found.")
        return "\n".join(lines)

    for i, r in enumerate(results, start=1):
        lines.append(f"[{i}] {r.get('title', '')}")
        lines.append(f"URL: {r.get('url', '')}")
        lines.append(f"Snippet: {r.get('snippet', '')}")
        lines.append("")

    return "\n".join(lines).rstrip()

# ---------------------------------------------------------------------------
# CLI 進入點
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Cline Web Search Tool — 使用 Playwright 進行網路搜尋",
        usage='python web_search_playwright.py "<query>" [OPTIONS]',
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="搜尋關鍵字",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="回傳結果數上限（預設 5）",
    )
    parser.add_argument(
        "--engine",
        type=str,
        default="brave",
        choices=["brave", "duckduckgo"],
        help="搜尋引擎（預設 brave）",
    )
    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help="Proxy URL（例如 http://proxy.company.com:8080）。"
             "若未指定，會自動讀取 HTTPS_PROXY / HTTP_PROXY 環境變數。",
    )

    args = parser.parse_args()

    if not args.query:
        print(
            'Usage: python web_search_playwright.py "<query>"',
            file=sys.stderr,
        )
        sys.exit(EXIT_USAGE)

    try:
        results = fetch_results(args.query, args.max_results, args.engine, args.proxy)
        output = format_results(args.query, results)
        print(output)
        sys.exit(EXIT_OK)
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(EXIT_UNEXPECTED)


if __name__ == "__main__":
    main()
