# -*- coding: utf-8 -*-
"""
Hacker News 爬虫：通过官方 Algolia Search API 获取 AI 强相关热门内容。
接口：https://hn.algolia.com/api/v1/search
使用 AI 关键词搜索 + front_page 热门榜双重策略，确保内容高质量且强 AI 相关。
"""
from datetime import datetime, timezone

from config import SOURCE_AUTHORITY
from crawler.base import BaseCrawler


class HackerNewsCrawler(BaseCrawler):
    source_name = "Hacker News"
    source_authority = SOURCE_AUTHORITY.get("Hacker News", 0.88)
    base_url = "https://news.ycombinator.com"

    # AI 强相关搜索词（用于 Algolia search）
    AI_QUERIES = [
        "LLM", "machine learning", "deep learning", "GPT",
        "artificial intelligence", "neural network", "open source AI",
        "PyTorch", "transformer", "diffusion model", "AI agent",
        "large language model", "ChatGPT", "openai", "anthropic",
    ]

    # 需过滤的 HN 站内非内容页面
    NOISE_PATHS = (
        "newsguidelines", "item?id=", "login", "about", "submit",
        "news", "jobs", "best", "ask", "show", "front", "user?",
    )

    def fetch(self) -> list[dict]:
        articles = []
        # 策略1：AI 关键词搜索（强相关，高质量）
        try:
            articles.extend(self._fetch_by_search())
        except Exception as e:
            print(f"  [HN] 关键词搜索 失败: {e}")

        # 策略2：front_page 热门榜（过滤 AI 相关，提升覆盖面）
        try:
            articles.extend(self._fetch_front_page())
        except Exception as e:
            print(f"  [HN] 热门榜 失败: {e}")

        # 去重（按 objectID / url）+ 过滤站内噪音页
        seen = set()
        unique = []
        for a in articles:
            url = a.get("url", "")
            # 过滤 HN 站内非内容链接
            if "news.ycombinator.com" in url and any(p in url for p in self.NOISE_PATHS):
                continue
            key = url or a.get("title", "")
            if key and key not in seen:
                seen.add(key)
                unique.append(a)
        # 每平台上限，避免霸榜（取热度最高的前 30 条）
        unique.sort(key=lambda x: (x.get("likes", 0) or 0), reverse=True)
        unique = unique[:30]
        print(f"  [HN] 去重+过滤后: {len(unique)} 条")
        return unique

    def _fetch_by_search(self) -> list[dict]:
        """AI 关键词搜索，按评论/点赞排序取高热度内容"""
        import httpx as _hx
        items = []
        for q in self.AI_QUERIES:
            url = "https://hn.algolia.com/api/v1/search"
            params = {
                "query": q,
                "tags": "story",
                "hitsPerPage": 8,
            }
            try:
                r = self.client.get(url, params=params, timeout=15)
                r.raise_for_status()
                data = r.json()
            except Exception:
                continue
            for h in data.get("hits", []):
                title = h.get("title") or h.get("story_title") or ""
                if not title:
                    continue
                hn_url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
                points = h.get("points") or 0
                comments = h.get("num_comments") or 0
                author = h.get("author") or ""
                created = h.get("created_at")
                try:
                    published = datetime.fromisoformat(created.replace("Z", "+00:00")) if created else None
                except (ValueError, TypeError):
                    published = None
                items.append(self.build_article(
                    title=title,
                    url=hn_url,
                    summary=f"Hacker News 讨论：{title}",
                    published_at=published,
                    likes=points,
                    comments=comments,
                    author=author,
                    category="article",
                    raw_text=title,
                ))
        print(f"  [HN] 关键词搜索: {len(items)} 条")
        return items

    def _fetch_front_page(self) -> list[dict]:
        """front_page 热门榜，过滤 AI 强相关内容"""
        ai_kw = [
            "llm", "gpt", "machine learning", "deep learning",
            "neural network", "pytorch", "tensorflow", "transformer", "diffusion",
            "agent", "openai", "anthropic", "claude", "gemini",
            "chatbot", "embedding", "rag", "fine-tun", "inference",
            "cuda", "gpu", "semiconductor", "robot", "artificial intelligence",
            "language model", "ai ", " ai", "chatgpt", "copilot", "midjourney",
        ]
        url = "https://hn.algolia.com/api/v1/search"
        params = {"tags": "front_page", "hitsPerPage": 30}
        try:
            r = self.client.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception:
            return []
        items = []
        for h in data.get("hits", []):
            title = h.get("title") or h.get("story_title") or ""
            if not title:
                continue
            low = title.lower()
            if not any(kw in low for kw in ai_kw):
                continue
            hn_url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
            points = h.get("points") or 0
            comments = h.get("num_comments") or 0
            author = h.get("author") or ""
            created = h.get("created_at")
            try:
                published = datetime.fromisoformat(created.replace("Z", "+00:00")) if created else None
            except (ValueError, TypeError):
                published = None
            items.append(self.build_article(
                title=title,
                url=hn_url,
                summary=f"Hacker News 热门：{title}",
                published_at=published,
                likes=points,
                comments=comments,
                author=author,
                category="article",
                raw_text=title,
            ))
        print(f"  [HN] 热门榜 AI 过滤: {len(items)} 条")
        return items
