# -*- coding: utf-8 -*-
"""
魔搭 ModelScope 社区爬虫：https://modelscope.cn
抓取高质量中文内容：技术博客、应用案例、教程、模型/数据集详解。
拒绝注水资讯，优先"教程/实战/案例"类。
通过 ModelScope 开放 API 获取社区热门文章与模型。
"""
from datetime import datetime

import httpx

from config import SOURCE_AUTHORITY, HEADERS
from crawler.base import BaseCrawler, extract_summary, clean_html


class ModelScopeCrawler(BaseCrawler):
    source_name = "魔搭ModelScope"
    source_authority = SOURCE_AUTHORITY.get("魔搭ModelScope", 0.88)
    base_url = "https://modelscope.cn"

    def fetch(self) -> list[dict]:
        articles = []
        try:
            articles.extend(self._fetch_community_posts())
        except Exception as e:
            print(f"  [ModelScope] 社区文章失败: {e}")
        try:
            articles.extend(self._fetch_models())
        except Exception as e:
            print(f"  [ModelScope] 模型失败: {e}")
        print(f"  [ModelScope] 共: {len(articles)} 条")
        return articles

    def _fetch_community_posts(self) -> list[dict]:
        """抓取 ModelScope 社区热门文章/博客（高质量教程/案例）"""
        # 社区文章列表 API
        url = "https://modelscope.cn/api/v1/community/articles"
        params = {"pageSize": 30, "pageNo": 1, "sortBy": "hot"}
        headers = {**HEADERS, "Accept": "application/json"}
        resp = self.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            # 兜底：直接抓社区页面
            return self._fallback_community_html()
        try:
            data = resp.json()
        except Exception:
            return self._fallback_community_html()

        items = []
        # 兼容不同返回结构
        records = []
        if isinstance(data, dict):
            records = data.get("data", {}).get("records", []) or data.get("data", []) or []
        elif isinstance(data, list):
            records = data
        for rec in records[:30]:
            if not isinstance(rec, dict):
                continue
            title = rec.get("title") or rec.get("articleTitle") or ""
            aid = rec.get("articleId") or rec.get("id") or ""
            if not title or not aid:
                continue
            content = rec.get("summary") or rec.get("content") or rec.get("description") or ""
            # 质量门槛
            if len(content.strip()) < 40 and not rec.get("coverUrl"):
                continue
            category = "article"
            low = title.lower()
            if any(k in low for k in ["教程", "tutorial", "实战", "上手", "搭建", "训练", "部署", "fine", "微调"]):
                category = "tutorial"
            elif any(k in low for k in ["案例", "应用", "实践", "落地", "场景", "最佳实践"]):
                category = "application"
            items.append(self.build_article(
                title=title,
                url=f"{self.base_url}/community/articles/{aid}",
                summary=extract_summary(content)[:200] if isinstance(content, str) else "",
                raw_text=content if isinstance(content, str) else "",
                published_at=datetime.now(),
                author=rec.get("authorName") or rec.get("nickName") or "ModelScope",
                category=category,
                likes=int(rec.get("likeCount") or rec.get("thumbsUp") or 0),
                comments=int(rec.get("commentCount") or 0),
                score=80.0,
                lang="cn",
            ))
        print(f"  [ModelScope] 社区文章: {len(items)} 条")
        return items

    def _fallback_community_html(self) -> list[dict]:
        """兜底：解析社区页面（容错）"""
        url = f"{self.base_url}/community"
        try:
            resp = self.client.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                return []
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")
            items = []
            for a in soup.select("a[href*='/community/articles/']")[:20]:
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if not title or len(title) < 5:
                    continue
                items.append(self.build_article(
                    title=title,
                    url=self.base_url + href if href.startswith("/") else href,
                    summary="",
                    raw_text="",
                    published_at=datetime.now(),
                    category="article",
                    score=70.0,
                    lang="cn",
                ))
            print(f"  [ModelScope] 兜底页面: {len(items)} 条")
            return items
        except Exception:
            return []

    def _fetch_models(self) -> list[dict]:
        """抓取热门模型作为应用案例（附模型卡摘要）"""
        url = "https://modelscope.cn/api/v1/models"
        params = {"PageSize": 20, "SortBy": "Downloads", "SortOrder": "Desc"}
        headers = {**HEADERS, "Accept": "application/json"}
        resp = self.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            return []
        try:
            data = resp.json()
        except Exception:
            return []
        items = []
        records = []
        if isinstance(data, dict):
            records = data.get("Data", {}).get("Models") or data.get("data", {}).get("models") or []
        for m in records[:20]:
            if not isinstance(m, dict):
                continue
            model_id = m.get("ModelId") or m.get("Id") or m.get("Name") or ""
            if not model_id:
                continue
            title = m.get("Name") or model_id
            # 模型作为"应用案例/工具"类型
            items.append(self.build_article(
                title=f"模型 · {title}",
                url=f"{self.base_url}/models/{model_id}",
                summary=(m.get("Summary") or m.get("Description") or "")[:200],
                raw_text="",
                published_at=datetime.now(),
                author=m.get("Author") or "ModelScope",
                category="application",
                likes=int(m.get("Downloads") or 0),
                score=75.0,
                lang="cn",
            ))
        print(f"  [ModelScope] 模型: {len(items)} 条")
        return items
