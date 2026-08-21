# -*- coding: utf-8 -*-
"""
博客园爬虫：搜索页面 HTML 爬取 AI 相关高分文章
"""
from datetime import datetime
import urllib.parse
from config import SOURCE_AUTHORITY
from crawler.base import BaseCrawler, clean_html
from bs4 import BeautifulSoup


class CnblogsCrawler(BaseCrawler):
    source_name = "博客园"
    source_authority = 0.72
    base_url = "https://www.cnblogs.com"

    SEARCH_KEYWORDS = ["AI", "大模型", "LLM", "人工智能", "ChatGPT", "机器学习", "深度学习", "AIGC"]

    def fetch(self) -> list[dict]:
        articles = []
        for kw in self.SEARCH_KEYWORDS:
            try:
                articles.extend(self._fetch_search(kw))
            except Exception as e:
                print(f"  [博客园] {kw} 失败: {e}")
        # 补充：首页热门
        try:
            articles.extend(self._fetch_homepage())
        except Exception as e:
            print(f"  [博客园] 首页 失败: {e}")
        return articles

    def _fetch_search(self, keyword: str) -> list[dict]:
        """搜索博客园文章"""
        encoded = urllib.parse.quote(keyword)
        url = f"https://zzk.cnblogs.com/s?w={encoded}&t=b"
        resp = self.get(url)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        items = []
        results = soup.select(".search-item, .post-list-item")[:10]

        for item in results:
            try:
                title_el = item.select_one("a.post-title, a.search-title, h3 a, .title a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                if not href.startswith("http"):
                    href = f"https://www.cnblogs.com{href}"

                summary_el = item.select_one(".post-summary, .search-body, .summary, p")
                summary = summary_el.get_text(strip=True)[:200] if summary_el else ""

                items.append(self.build_article(
                    title=title,
                    url=href,
                    summary=summary,
                    published_at=datetime.now(),
                    category="article",
                    raw_text=summary,
                ))
            except Exception:
                continue

        # 降级：全局链接扫描
        if not items:
            links = soup.select("a[href*='cnblogs.com/']")
            seen = set()
            ai_kw = ["ai", "人工智能", "机器学习", "深度学习", "大模型", "llm", "gpt", "chatgpt"]
            for link in links[:15]:
                href = link.get("href", "")
                title = link.get_text(strip=True)
                if not title or len(title) < 8 or href in seen:
                    continue
                seen.add(href)
                if not any(kw in title.lower() for kw in ai_kw):
                    continue
                items.append(self.build_article(
                    title=title,
                    url=href,
                    summary="",
                    published_at=datetime.now(),
                    category="article",
                ))

        print(f"  [博客园] {keyword}: {len(items)} 条")
        return items

    def _fetch_homepage(self) -> list[dict]:
        """博客园首页热门文章"""
        url = "https://www.cnblogs.com/"
        resp = self.get(url)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        items = []
        ai_kw = ["ai", "人工智能", "机器学习", "深度学习", "大模型", "llm", "gpt", "chatgpt", "agent", "aigc"]

        # 首页文章卡片
        cards = soup.select(".post-item, .post-list-item, article")[:20]
        for card in cards:
            try:
                title_el = card.select_one("a.post-title, .title a, h3 a, a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                if not href.startswith("http"):
                    href = f"https://www.cnblogs.com{href}"
                if not title or len(title) < 8:
                    continue

                combined = title.lower()
                if not any(kw in combined for kw in ai_kw):
                    continue

                summary_el = card.select_one(".post-summary, p")
                summary = summary_el.get_text(strip=True)[:200] if summary_el else ""

                items.append(self.build_article(
                    title=title,
                    url=href,
                    summary=summary,
                    published_at=datetime.now(),
                    category="article",
                    raw_text=summary,
                ))
            except Exception:
                continue

        print(f"  [博客园] 首页: {len(items)} 条")
        return items
