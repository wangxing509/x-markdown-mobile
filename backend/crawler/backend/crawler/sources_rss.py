# -*- coding: utf-8 -*-
"""
通用 RSS 爬虫：官方博客 / 外文审计源优先走 RSS（结构稳定、正文可及）。
每个实例对应一个 source 配置项（name/feeds/authority/lang/audit）。
"""
from datetime import datetime

import feedparser

from config import HEADERS, REQUEST_TIMEOUT
from crawler.base import BaseCrawler, extract_summary


class RSSCrawler(BaseCrawler):
    def __init__(self, source_config: dict):
        self.source_config = source_config
        self.source_name = source_config["name"]
        self.source_authority = float(source_config.get("authority", 0.85))
        self.base_url = (source_config.get("feeds") or [""])[0]
        super().__init__()

    def fetch(self) -> list[dict]:
        items = []
        for feed_url in (self.source_config.get("feeds") or []):
            try:
                items.extend(self._fetch_feed(feed_url))
            except Exception as e:
                print(f"  [RSS:{self.source_name}] {feed_url} 失败: {e}")
        print(f"  [RSS:{self.source_name}] 共 {len(items)} 条")
        return items

    def _fetch_feed(self, feed_url: str) -> list[dict]:
        resp = self.get(feed_url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return []
        parsed = feedparser.parse(resp.content)
        items = []
        for entry in parsed.entries[:25]:
            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue
            summary = ""
            if entry.get("summary"):
                summary = extract_summary(entry["summary"])
            elif entry.get("description"):
                summary = extract_summary(entry["description"])
            published = None
            for key in ("published_parsed", "updated_parsed"):
                if entry.get(key):
                    try:
                        published = datetime(*entry[key][:6])
                        break
                    except Exception:
                        pass
            author = ""
            if entry.get("author"):
                author = entry["author"]
            elif isinstance(entry.get("authors"), list) and entry["authors"]:
                author = entry["authors"][0].get("name", "")
            items.append(self.build_article(
                title=title,
                url=link,
                summary=summary,
                raw_text=summary,
                published_at=published or datetime.now(),
                author=author,
                category="article",
                score=80.0,
                lang=self.source_config.get("lang", "en"),
            ))
        return items


def build_rss_crawlers(sources: list[dict]) -> list[BaseCrawler]:
    """根据来源配置创建启用的 RSS 爬虫"""
    crawlers = []
    for cfg in sources:
        if cfg.get("kind") == "rss" and cfg.get("enabled", True) and cfg.get("feeds"):
            crawlers.append(RSSCrawler(cfg))
    return crawlers

