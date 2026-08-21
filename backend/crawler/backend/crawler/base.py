# -*- coding: utf-8 -*-
"""
爬虫抽象基类（复用 ai-news-dashboard 模式）
"""
import hashlib
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

import httpx
from config import HEADERS, REQUEST_TIMEOUT, HTTP_PROXY

try:
    from simhash import Simhash
    HAS_SIMHASH = True
except ImportError:
    HAS_SIMHASH = False


def compute_simhash(text: str) -> str:
    """计算文本 SimHash 值（HEX 格式）"""
    if not text or not HAS_SIMHASH:
        return ""
    return Simhash(text).value.to_bytes(8, "big").hex()


def clean_html(raw: str) -> str:
    """去除 HTML 标签"""
    if not raw:
        return ""
    raw = re.sub(r"<script[^>]*>.*?</script>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    raw = re.sub(r"<style[^>]*>.*?</style>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    raw = re.sub(r"<[^>]+>", "", raw)
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()


def extract_summary(text: str, max_len: int = 200) -> str:
    """从正文提取摘要"""
    text = clean_html(text)
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0].rsplit("。", 1)[0] + "…"


class BaseCrawler(ABC):
    """爬虫抽象基类"""

    source_name: str = "Unknown"
    source_authority: float = 0.5
    base_url: str = ""
    verify_ssl: bool = True  # 部分站点证书链异常时按源关闭校验

    def __init__(self):
        proxy = HTTP_PROXY if HTTP_PROXY else None
        self.client = httpx.Client(
            headers=HEADERS,
            timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=8),
            follow_redirects=True,
            proxy=proxy,
            verify=self.verify_ssl,
        )

    @abstractmethod
    def fetch(self) -> list[dict]:
        """抓取原始文章列表，返回统一格式的 dict 列表"""

    def build_article(
        self,
        title: str,
        url: str,
        summary: str = "",
        raw_text: str = "",
        published_at: Optional[datetime] = None,
        likes: int = 0,
        comments: int = 0,
        author: str = "",
        author_followers: int = 0,
        category: str = "article",
        score: float = 0.0,
        **extra,
    ) -> dict:
        """构建统一格式的文章字典"""
        combined = f"{title} {summary} {raw_text}"
        article = {
            "title": title.strip(),
            "url": url.strip(),
            "summary": summary.strip() or extract_summary(raw_text),
            "source": self.source_name,
            "source_authority": self.source_authority,
            "published_at": published_at or datetime.now(),
            "raw_text": raw_text.strip(),
            "simhash_value": compute_simhash(combined),
            "category": category,
            "score": float(score or 0.0),
            "likes": likes,
            "comments": comments,
            "author": author,
            "author_followers": author_followers,
        }
        # 附加额外字段（如 bvid、duration 等）
        if extra:
            article.update(extra)
        return article

    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.client.get(url, **kwargs)

    def get_json(self, url: str, **kwargs) -> dict:
        resp = self.client.get(url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def close(self):
        self.client.close()
