# -*- coding: utf-8 -*-
"""
掘金爬虫：推荐接口获取 AI 相关文章
修复：搜索API下线 → 使用 recommend_all_feed + recommend_cate_tag_feed
"""
from datetime import datetime
import urllib.parse
from config import SOURCE_AUTHORITY
from crawler.base import BaseCrawler


class JuejinCrawler(BaseCrawler):
    source_name = "掘金"
    source_authority = SOURCE_AUTHORITY["掘金"]
    base_url = "https://juejin.cn"

    # 强 AI 必含关键词
    AI_KEYWORDS = [
        "大模型", "llm", "agent", "智能体", "chatgpt", "deepseek", "openai",
        "claude", "gemini", "qwen", "智谱", "kimi", "gpt", "aigc", "文生图",
        "文生视频", "多模态", "提示词", "prompt", "rag", "知识图谱", "embedding",
        "向量数据库", "微调", "transformer", "diffusion", "神经网络", "深度学习",
        "机器学习", "强化学习", "nlp", "自然语言处理", "计算机视觉", "copilot",
        "cursor", "人工智能", "ai", "ai 大模型", "智能问答", "模型训练", "推理",
        "ai编程", "agent", "mcp", "function calling", "幻觉", "对齐",
    ]

    def fetch(self) -> list[dict]:
        articles = []
        # 仅保留人工智能标签（最精准的 AI 内容来源）
        try:
            articles.extend(self._fetch_by_tag("6809637769959178254", "人工智能"))
        except Exception as e:
            print(f"  [掘金] AI标签 失败: {e}")
        return articles

    def _fetch_by_tag(self, tag_id: str, tag_name: str) -> list[dict]:
        """通过推荐接口按标签获取文章（多翻页以扩充数量）"""
        url = "https://api.juejin.cn/recommend_api/v1/article/recommend_cate_tag_feed"
        headers = {
            **self.client.headers,
            "Content-Type": "application/json",
            "Referer": "https://juejin.cn/",
            "Origin": "https://juejin.cn",
        }
        entries = []
        # 翻 3 页（cursor 0/20/40）
        for cursor in ("0", "20", "40"):
            payload = {"cate_id": tag_id, "cursor": cursor, "limit": 20, "sort_type": 200}
            try:
                resp = self.client.post(url, json=payload, headers=headers, timeout=15)
            except Exception:
                continue
            if resp.status_code != 200:
                continue
            try:
                data = resp.json()
            except Exception:
                continue
            if data.get("err_no") != 0:
                continue
            batch = data.get("data", [])
            if not isinstance(batch, list) or not batch:
                break
            entries.extend(batch)
            if len(batch) < 20:
                break

        if not entries:
            return []

        items = []
        for a in entries[:20]:
            if not isinstance(a, dict):
                continue
            info = a.get("article_info", {}) or {}
            title = info.get("title", "")
            article_id = info.get("article_id", "") or a.get("article_id", "")
            if not title or not article_id:
                continue

            # 强 AI 过滤（避免标签内混入的纯工程/前端文）
            brief = info.get("brief_content", "") or ""
            combined = f"{title} {brief}".lower()
            if not any(kw in combined for kw in self.AI_KEYWORDS):
                continue

            author = a.get("author_user_info", {}) or {}
            ctime = info.get("ctime", 0)
            try:
                published = datetime.fromtimestamp(int(ctime)) if ctime else None
            except (ValueError, TypeError, OSError):
                published = None
            items.append(self.build_article(
                title=title,
                url=f"https://juejin.cn/post/{article_id}",
                summary=info.get("brief_content", "") or "",
                published_at=published,
                likes=info.get("digg_count", 0) or 0,
                comments=info.get("comment_count", 0) or 0,
                author=author.get("user_name", "") if isinstance(author, dict) else "",
                author_followers=author.get("follower_count", 0) if isinstance(author, dict) else 0,
                category="article",
            ))
        print(f"  [掘金] {tag_name}: {len(items)} 条")
        return items

    def _fetch_recommend_all(self) -> list[dict]:
        """全站推荐文章，过滤 AI 相关"""
        url = "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed"
        payload = {"cursor": "0", "limit": 40}
        headers = {
            **self.client.headers,
            "Content-Type": "application/json",
            "Referer": "https://juejin.cn/",
            "Origin": "https://juejin.cn",
        }
        resp = self.client.post(url, json=payload, headers=headers)
        if resp.status_code != 200:
            return []

        try:
            data = resp.json()
        except Exception:
            return []
        if data.get("err_no") != 0:
            return []

        entries = data.get("data", [])
        if not isinstance(entries, list):
            return []

        ai_kw = [
            "ai", "llm", "gpt", "agent", "模型", "人工智能", "深度学习",
            "机器学习", "大模型", "chatgpt", "aigc", "智能", "transformer",
            "diffusion", "copilot", "cursor", "prompt", "rag", "向量",
        ]

        items = []
        for entry in entries[:40]:
            if not isinstance(entry, dict):
                continue
            # recommend_all 的结构是 item_type + item_info
            info = entry.get("item_info", {}) or entry.get("article_info", {})
            if not isinstance(info, dict):
                continue

            title = info.get("title", "") or info.get("article_title", "")
            article_id = info.get("article_id", "") or info.get("item_id", "")
            if not title or not article_id:
                continue

            # AI 过滤
            combined = f"{title} {info.get('brief_content', '')}".lower()
            if not any(kw in combined for kw in ai_kw):
                continue

            author = entry.get("author_user_info", {}) or entry.get("author", {}) or {}
            # ctime 可能是字符串或整数
            ctime = info.get("ctime", 0) or info.get("create_time", 0)
            try:
                published = datetime.fromtimestamp(int(ctime)) if ctime else None
            except (ValueError, TypeError, OSError):
                published = None
            items.append(self.build_article(
                title=title,
                url=f"https://juejin.cn/post/{article_id}",
                summary=info.get("brief_content", "") or "",
                published_at=published,
                likes=info.get("digg_count", 0) or 0,
                comments=info.get("comment_count", 0) or 0,
                author=author.get("user_name", "") if isinstance(author, dict) else "",
                author_followers=author.get("follower_count", 0) if isinstance(author, dict) else 0,
                category="article",
            ))
        print(f"  [掘金] 全站推荐: {len(items)} 条")
        return items
