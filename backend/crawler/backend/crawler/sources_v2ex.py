# -*- coding: utf-8 -*-
"""
V2EX 爬虫：API 获取热门节点
增加更多 AI 相关节点
"""
from datetime import datetime
from config import SOURCE_AUTHORITY
from crawler.base import BaseCrawler


class V2exCrawler(BaseCrawler):
    source_name = "V2EX"
    source_authority = SOURCE_AUTHORITY["V2EX"]
    base_url = "https://www.v2ex.com"

    # AI 相关节点
    NODES = ["ai", "ml", "python", "programmer", "share", "create", "tech"]

    def fetch(self) -> list[dict]:
        articles = []
        for node in self.NODES:
            try:
                articles.extend(self._fetch_node(node))
            except Exception as e:
                print(f"  [V2EX] {node} 失败: {e}")
        # 补充：热门主题
        try:
            articles.extend(self._fetch_hot())
        except Exception as e:
            print(f"  [V2EX] hot 失败: {e}")
        return articles

    def _fetch_node(self, node: str) -> list[dict]:
        """获取节点下的主题"""
        url = f"https://www.v2ex.com/api/topics/show.json?node_name={node}"
        resp = self.get(url)
        if resp.status_code != 200:
            return []

        data = resp.json()
        if not isinstance(data, list):
            return []
        items = []
        ai_kw = ["ai", "llm", "gpt", "agent", "模型", "人工智能", "chatgpt", "claude", "大模型", "deepseek"]
        for t in data[:10]:
            if not isinstance(t, dict):
                continue
            title = t.get("title", "")
            combined = title.lower()
            if not any(kw in combined for kw in ai_kw):
                continue

            tid = t.get("id", 0)
            replies = t.get("replies", 0)
            member = t.get("member", {}) or {}

            items.append(self.build_article(
                title=title,
                url=f"https://www.v2ex.com/t/{tid}",
                summary=(t.get("content", "") or "")[:200],
                published_at=datetime.fromtimestamp(t.get("created", 0)) if t.get("created") else None,
                likes=replies,
                comments=replies,
                author=member.get("username", "") if isinstance(member, dict) else "",
                category="article",
            ))
        print(f"  [V2EX] {node}: {len(items)} 条")
        return items

    def _fetch_hot(self) -> list[dict]:
        """获取热门主题"""
        url = "https://www.v2ex.com/api/topics/hot.json"
        resp = self.get(url)
        if resp.status_code != 200:
            return []

        data = resp.json()
        if not isinstance(data, list):
            return []
        items = []
        ai_kw = ["ai", "llm", "gpt", "agent", "模型", "人工智能", "chatgpt", "claude", "大模型"]
        for t in data[:30]:
            if not isinstance(t, dict):
                continue
            title = t.get("title", "")
            combined = title.lower()
            if not any(kw in combined for kw in ai_kw):
                continue

            tid = t.get("id", 0)
            replies = t.get("replies", 0)

            items.append(self.build_article(
                title=title,
                url=f"https://www.v2ex.com/t/{tid}",
                summary=(t.get("content", "") or "")[:200],
                published_at=datetime.fromtimestamp(t.get("created", 0)) if t.get("created") else None,
                likes=replies,
                comments=replies,
                category="article",
            ))
        print(f"  [V2EX] hot: {len(items)} 条")
        return items
