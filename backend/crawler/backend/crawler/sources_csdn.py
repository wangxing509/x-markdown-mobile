# -*- coding: utf-8 -*-
"""
CSDN 爬虫：热榜 API 获取 AI 相关高分博客
使用 blog.csdn.net/phoenix/web/blog/hot-rank 接口
"""
from datetime import datetime
from config import SOURCE_AUTHORITY
from crawler.base import BaseCrawler, clean_html


class CsdnCrawler(BaseCrawler):
    source_name = "CSDN"
    source_authority = SOURCE_AUTHORITY.get("CSDN", 0.68)
    base_url = "https://blog.csdn.net"

    # 强 AI 必含关键词（标题/摘要需命中其一才视为 AI 强相关，避免运维/纯工程文混入）
    AI_KEYWORDS = [
        "大模型", "llm", "agent", "智能体", "ai agent", "ai智能体",
        "chatgpt", "deepseek", "openai", "claude", "gemini", "qwen", "智谱", "kimi",
        "gpt", "aigc", "文生图", "文生视频", "多模态", "提示词", "prompt",
        "rag", "知识图谱", "embedding", "向量数据库", "微调", "对齐",
        "transformer", "diffusion", "stable diffusion", "神经网络", "卷积",
        "深度学习", "机器学习", "强化学习", "nlp", "自然语言处理",
        "计算机视觉", "大模型推理", "模型蒸馏", "量化", "ai编程",
        "copilot", "cursor", "ai应用", "人工智能", "ai 大模型", "智能问答",
    ]

    def fetch(self) -> list[dict]:
        articles = []
        # AI 频道热榜（限定 AI 板块）
        for page in range(3):
            try:
                articles.extend(self._fetch_hot_rank(page, channel="ai"))
            except Exception as e:
                print(f"  [CSDN] AI频道 page={page} 失败: {e}")
        return articles

    def _fetch_hot_rank(self, page: int, channel: str = "") -> list[dict]:
        """CSDN 指定频道热榜 API（channel=ai 限定 AI 板块）"""
        url = "https://blog.csdn.net/phoenix/web/blog/hot-rank"
        params = {"page": page, "pageSize": 50, "type": channel}
        headers = {
            **self.client.headers,
            "Accept": "application/json",
            "Referer": "https://blog.csdn.net/rank",
        }
        resp = self.client.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            return []

        try:
            data = resp.json()
        except Exception:
            return []

        if data.get("code") != 200:
            return []

        entries = data.get("data", [])
        if not isinstance(entries, list):
            return []

        items = []
        for entry in entries[:50]:
            if not isinstance(entry, dict):
                continue
            title = entry.get("articleTitle", "") or entry.get("title", "")
            article_id = entry.get("articleId", "") or entry.get("url", "")
            author = entry.get("nickName", "") or entry.get("username", "")
            username = entry.get("userName", "") or entry.get("username", "")

            if not title:
                continue

            # AI 相关过滤
            combined = f"{title} {entry.get('summary', '')} {entry.get('tags', '')}".lower()
            if not any(kw in combined for kw in self.AI_KEYWORDS):
                continue

            # 构建 URL
            if article_id and not str(article_id).startswith("http"):
                article_url = f"https://blog.csdn.net/{username}/article/details/{article_id}"
            elif isinstance(article_id, str) and article_id.startswith("http"):
                article_url = article_id
            else:
                article_url = entry.get("url", f"https://blog.csdn.net/{username}")

            # 互动数据
            hot_score = entry.get("hotRankScore", 0) or 0
            view_count = entry.get("viewCount", 0) or 0
            comment_count = entry.get("commentCount", 0) or 0
            fan_count = entry.get("fanCount", 0) or 0

            summary = entry.get("summary", "") or entry.get("desc", "") or ""

            items.append(self.build_article(
                title=title,
                url=article_url,
                summary=clean_html(summary)[:200] if summary else "",
                published_at=datetime.now(),
                likes=view_count or hot_score,
                comments=comment_count,
                author=author,
                author_followers=fan_count,
                category="article",
                raw_text=clean_html(summary)[:500] if summary else "",
            ))
        print(f"  [CSDN] 热榜 page={page}: {len(items)} 条")
        return items
