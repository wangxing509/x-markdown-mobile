# -*- coding: utf-8 -*-
"""
思否爬虫：/news 页面 HTML 爬取
修复：/t/{tag} 468反爬 → 改用 /news 全站热门
"""
from datetime import datetime
from config import SOURCE_AUTHORITY
from crawler.base import BaseCrawler, clean_html
from bs4 import BeautifulSoup


class SegmentfaultCrawler(BaseCrawler):
    source_name = "思否"
    source_authority = SOURCE_AUTHORITY["思否"]
    base_url = "https://segmentfault.com"

    def fetch(self) -> list[dict]:
        articles = []
        try:
            articles.extend(self._fetch_news())
        except Exception as e:
            print(f"  [思否] /news 失败: {e}")
        return articles

    def _fetch_news(self) -> list[dict]:
        """抓取思否 /news 页面的文章链接"""
        url = "https://segmentfault.com/news"
        resp = self.get(url)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        items = []
        ai_kw = [
            "ai", "llm", "gpt", "agent", "模型", "人工智能", "深度学习",
            "机器学习", "大模型", "chatgpt", "aigc", "智能", "neural",
            "transformer", "diffusion", "copilot", "cursor",
        ]

        # 全局扫描所有 /a/ 链接
        links = soup.select("a[href*='/a/']")
        seen_urls = set()

        for link in links:
            try:
                href = link.get("href", "")
                title = link.get_text(strip=True)
                # 跳过评论链接和空标题
                if "#comment-area" in href or not title or len(title) < 5:
                    continue
                if not href.startswith("http"):
                    href = f"https://segmentfault.com{href}"
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                # AI 过滤
                combined = title.lower()
                if not any(kw in combined for kw in ai_kw):
                    continue

                items.append(self.build_article(
                    title=title,
                    url=href,
                    summary="",
                    published_at=datetime.now(),
                    category="article",
                ))
            except Exception:
                continue

        print(f"  [思否] /news: {len(items)} 条")
        return items
