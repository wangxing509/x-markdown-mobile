# -*- coding: utf-8 -*-
"""
Hugging Face 爬虫（外文）：聚焦高质量英文内容
  - HF Blog（技术博客 / 教程 / 案例，含正文，保证英文原文可正常打开呈现）
  - HF Models Discussions（社区讨论 / 应用案例，含正文）
拒绝纯 model 卡片罗列（无正文价值）。
"""
from datetime import datetime
import httpx
from config import SOURCE_AUTHORITY, HEADERS, REQUEST_TIMEOUT
from crawler.base import BaseCrawler, extract_summary


class HuggingFaceCrawler(BaseCrawler):
    source_name = "Hugging Face"
    source_authority = SOURCE_AUTHORITY["Hugging Face"]
    base_url = "https://huggingface.co"

    def fetch(self) -> list[dict]:
        articles = []
        try:
            articles.extend(self._fetch_blog())
        except Exception as e:
            print(f"  [HF] Blog 失败: {e}")
        try:
            articles.extend(self._fetch_papers())
        except Exception as e:
            print(f"  [HF] Papers 失败: {e}")
        return articles

    def _fetch_blog(self) -> list[dict]:
        """抓取 HF Blog 文章（高质量英文技术博客，含正文）"""
        url = "https://huggingface.co/api/blog"
        params = {"sort": "createdAt", "direction": "-1", "limit": 25}
        resp = self.get(url, params=params)
        if resp.status_code != 200:
            return []
        try:
            data = resp.json()
        except Exception:
            return []
        items = []
        for p in data[:25]:
            if not isinstance(p, dict):
                continue
            slug = p.get("slug", "")
            title = p.get("title", "")
            if not slug or not title:
                continue
            summary = (p.get("summary") or p.get("excerpt") or "")[:200]
            # 判断分类
            combined = (title + " " + summary).lower()
            if any(k in combined for k in ["tutorial", "guide", "how to", "step", "build", "fine-tune", "train"]):
                category = "tutorial"
            elif any(k in combined for k in ["release", "announcing", "introducing", "new", "benchmark", "case", "application"]):
                category = "application"
            else:
                category = "article"
            items.append(self.build_article(
                title=title,
                url=f"https://huggingface.co/blog/{slug}",
                summary=extract_summary(summary),
                # 正文通过"打开原文"时由 /api/md/convert 抓取，这里预留 raw_text 为空
                raw_text="",
                published_at=datetime.fromisoformat(p["createdAt"].replace("Z", "+00:00")) if p.get("createdAt") else datetime.now(),
                author=p.get("author", {}).get("name", "Hugging Face") if isinstance(p.get("author"), dict) else "Hugging Face",
                category=category,
                likes=int(p.get("likes", 0) or 0),
                score=85.0,
                lang="en",
            ))
        print(f"  [HF] Blog: {len(items)} 条")
        return items

    def _fetch_papers(self) -> list[dict]:
        """获取热门论文（含摘要正文，外文学术内容）"""
        url = "https://huggingface.co/api/trending"
        try:
            resp = self.get(url)
            if resp.status_code != 200:
                return []
            data = resp.json()
            items = []
            papers = data.get("recentlyTrending", []) if isinstance(data, dict) else []
            for p in papers[:12]:
                paper = p.get("paper", {})
                if not isinstance(paper, dict):
                    continue
                pid = paper.get("id", "")
                title = paper.get("title", "")
                summary = paper.get("summary", "") or ""
                if not pid or not title:
                    continue
                items.append(self.build_article(
                    title=title,
                    url=f"https://huggingface.co/papers/{pid}",
                    summary=extract_summary(summary)[:220],
                    raw_text=summary[:2000],
                    published_at=datetime.now(),
                    author="Hugging Face Papers",
                    category="article",
                    likes=int(paper.get("upvotes", 0) or 0),
                    score=82.0,
                    lang="en",
                ))
            print(f"  [HF] Papers: {len(items)} 条")
            return items
        except Exception:
            return []
