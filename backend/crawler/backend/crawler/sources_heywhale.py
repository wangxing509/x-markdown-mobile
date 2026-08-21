# -*- coding: utf-8 -*-
"""
和鲸社区（Heywhale）爬虫：抓取数据科学与人工智能实践社区文章。
地址：https://ai.heywhale.com/community.html
和鲸社区聚合大量 AI / 数据科学实践文章、案例与经验分享，与 AI 强相关。
"""
import re
from datetime import datetime

from config import SOURCE_AUTHORITY
from crawler.base import BaseCrawler, clean_html


class HeywhaleCrawler(BaseCrawler):
    source_name = "和鲸社区"
    source_authority = SOURCE_AUTHORITY.get("和鲸社区", 0.8)
    base_url = "https://ai.heywhale.com"

    # 和鲸本就是数据科学/AI 社区，再做一层 AI 相关过滤确保精度
    AI_KEYWORDS = [
        "ai", "人工智能", "大模型", "llm", "gpt", "机器学习", "深度学习",
        "数据分析", "数据挖掘", "神经网络", "python", "pytorch", "tensorflow",
        "nlp", "cv", "计算机视觉", "自然语言", "智能", "算法", "数据科学",
        "agent", "rag", "embedding", "微调", "transformer", "diffusion",
        "aigc", "提示词", "copilot", "模型", "训练", "推理", "向量",
        "知识图谱", "大模型", "chatgpt", "claude", "gemini",
    ]

    def fetch(self) -> list[dict]:
        articles = []
        try:
            articles.extend(self._fetch_community())
        except Exception as e:
            print(f"  [和鲸社区] 列表 失败: {e}")
        print(f"  [和鲸社区] 共: {len(articles)} 条")
        return articles

    def _fetch_community(self) -> list[dict]:
        """抓取社区文章卡片列表"""
        url = "https://ai.heywhale.com/community.html"
        r = self.client.get(url, timeout=15)
        r.raise_for_status()
        # 文章链接形如 /article/573.html 或 /article/573
        raw_links = re.findall(r'/article/(\d+)(?:\.html)?', r.text)
        seen = set()
        aids = []
        for a in raw_links:
            if a not in seen:
                seen.add(a)
                aids.append(a)
        aids = aids[:25]

        items = []
        for aid in aids:
            detail_url = f"https://ai.heywhale.com/article/{aid}.html"
            try:
                d = self.client.get(detail_url, timeout=15)
                d.raise_for_status()
                html = d.text
            except Exception:
                # 尝试无 .html 后缀
                try:
                    d = self.client.get(f"https://ai.heywhale.com/article/{aid}", timeout=15)
                    d.raise_for_status()
                    html = d.text
                except Exception:
                    continue

            m = re.search(r'<title>(.*?)</title>', html)
            raw_title = clean_html(m.group(1)) if m else ""
            # 清理和鲸官网标题后缀
            title = re.split(r'\s*[-_|]\s*(?:和鲸|数据智能领航者|数据科学与人工智能|Heywhale|ModelWhale)', raw_title)[0].strip()
            if not title:
                continue

            # AI 相关过滤（标题 + 摘要）
            desc_m = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html)
            summary = clean_html(desc_m.group(1)) if desc_m else ""
            combined = f"{title} {summary}".lower()
            if not any(kw in combined for kw in self.AI_KEYWORDS):
                continue

            # 作者
            author_m = re.search(r'(?:作者|Author)[：:]\s*([^<\n]{2,30})', html)
            author = clean_html(author_m.group(1)).strip() if author_m else "和鲸社区"

            items.append(self.build_article(
                title=title,
                url=detail_url,
                summary=summary[:300] if summary else f"和鲸社区 AI 实践：{title}",
                published_at=datetime.now(),
                author=author,
                category="article",
                raw_text=summary[:600] if summary else title,
            ))
        print(f"  [和鲸社区] 文章: {len(items)} 条")
        return items
