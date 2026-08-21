# -*- coding: utf-8 -*-
"""
智源社区（BAAI）爬虫：抓取 AI 热门论文页面 https://hub.baai.ac.cn/papers
该页面聚合 24h 内 AI 领域被热议的论文，内容与 AI 强相关、质量高。
"""
import re
from datetime import datetime

from config import SOURCE_AUTHORITY
from crawler.base import BaseCrawler, clean_html


class BAAICrawler(BaseCrawler):
    source_name = "智源社区"
    source_authority = SOURCE_AUTHORITY.get("智源社区", 0.9)
    base_url = "https://hub.baai.ac.cn"

    def fetch(self) -> list[dict]:
        articles = []
        try:
            articles.extend(self._fetch_papers())
        except Exception as e:
            print(f"  [智源社区] 论文列表 失败: {e}")
        print(f"  [智源社区] 共: {len(articles)} 条")
        return articles

    def _fetch_papers(self) -> list[dict]:
        """抓取 AI 热门论文列表与详情"""
        list_url = "https://hub.baai.ac.cn/papers"
        r = self.client.get(list_url, timeout=15)
        r.raise_for_status()
        paper_ids = re.findall(r'/paper/([0-9a-fA-F-]{36})', r.text)
        # 去重并限制数量
        seen = set()
        unique_ids = []
        for pid in paper_ids:
            if pid not in seen:
                seen.add(pid)
                unique_ids.append(pid)
        unique_ids = unique_ids[:20]

        items = []
        for pid in unique_ids:
            detail_url = f"https://hub.baai.ac.cn/paper/{pid}"
            try:
                d = self.client.get(detail_url, timeout=15)
                d.raise_for_status()
                html = d.text
            except Exception:
                continue

            # 标题
            m = re.search(r'<title>(.*?)</title>', html)
            title = clean_html(m.group(1)).replace(" - 智源社区论文", "").replace(" - 智源社区", "") if m else ""

            # 作者 / 机构（meta 或正文）
            author_m = re.search(r'(?:作者|Authors?|机构)[：:]\s*([^<\n]{2,60})', html)
            author = clean_html(author_m.group(1)).strip() if author_m else "BAAI"

            # 摘要：优先 <meta name="description">，其次首个长段落
            desc_m = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html)
            summary = ""
            if desc_m:
                summary = clean_html(desc_m.group(1))
            if not summary or len(summary) < 20:
                paras = re.findall(r'<p[^>]*>(.*?)</p>', html, re.S)
                for p in paras:
                    txt = clean_html(p).strip()
                    if 30 < len(txt) < 400 and ("摘要" in txt or "我们" in txt or "本文" in txt or "提出" in txt or "模型" in txt):
                        summary = txt
                        break
                if not summary and paras:
                    summary = clean_html(paras[0]).strip()[:300]

            # 发布时间（尽量提取）
            time_m = re.search(r'"publishTime"\s*:\s*"([^"]+)"', html)
            published = None
            if time_m:
                try:
                    published = datetime.fromisoformat(time_m.group(1).replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    published = None

            if not title:
                continue
            items.append(self.build_article(
                title=title,
                url=detail_url,
                summary=summary[:300] if summary else f"智源社区 AI 热门论文：{title}",
                published_at=published,
                author=author,
                category="article",
                raw_text=summary[:600] if summary else title,
            ))
        print(f"  [智源社区] 论文: {len(items)} 条")
        return items
