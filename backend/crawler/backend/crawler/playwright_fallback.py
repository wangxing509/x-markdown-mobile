# -*- coding: utf-8 -*-
"""
Playwright 无头浏览器兜底爬虫
当 API 爬取失败时使用
"""
from datetime import datetime
from config import HEADERS
from crawler.base import BaseCrawler, compute_simhash, extract_summary, clean_html


class PlaywrightFallback:
    """Playwright 兜底爬虫"""

    def __init__(self):
        self._browser = None
        self._playwright = None

    async def _ensure_browser(self):
        """确保浏览器已启动"""
        if self._browser is not None:
            return
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
        except ImportError:
            print("  [Playwright] 未安装 playwright，兜底爬虫不可用")
        except Exception as e:
            print(f"  [Playwright] 启动失败: {e}")

    async def fetch_page(self, url: str) -> str:
        """抓取页面内容"""
        await self._ensure_browser()
        if self._browser is None:
            return ""

        try:
            page = await self._browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            content = await page.content()
            await page.close()
            return content
        except Exception as e:
            print(f"  [Playwright] 抓取失败 {url}: {e}")
            return ""

    async def close(self):
        """关闭浏览器"""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


# 全局单例
_fallback_instance = None


def get_fallback() -> PlaywrightFallback:
    global _fallback_instance
    if _fallback_instance is None:
        _fallback_instance = PlaywrightFallback()
    return _fallback_instance
