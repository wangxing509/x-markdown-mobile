# -*- coding: utf-8 -*-
"""
微软人工智能教育与学习共建社区（AI-Edu）爬虫
基于 GitHub 仓库 microsoft/ai-edu，抓取高质量教程与实践案例。
为规避 GitHub API 未认证限流（60次/小时），直接解析 GitHub 网页目录页 HTML。
结构：基础教程 / 实践案例 / 实践项目 / 社区活动
作为"高质量教程、优秀案例"来源，内容稳定性强、与 AI 强相关。
"""
import re
from datetime import datetime

from config import SOURCE_AUTHORITY
from crawler.base import BaseCrawler, clean_html


class MicrosoftAICrawler(BaseCrawler):
    source_name = "微软AI教育社区"
    source_authority = SOURCE_AUTHORITY.get("微软AI教育社区", 0.85)
    base_url = "https://github.com/microsoft/ai-edu"

    # 优先抓取的分类目录（高质量、强相关）
    CATEGORIES = ["实践案例", "基础教程", "实践项目"]

    def fetch(self) -> list[dict]:
        articles = []
        for cat in self.CATEGORIES:
            try:
                articles.extend(self._fetch_category(cat))
            except Exception as e:
                print(f"  [微软AI教育] {cat} 失败: {e}")
            if len(articles) >= 25:
                break
        print(f"  [微软AI教育] 共: {len(articles)} 条")
        return articles

    def _fetch_category(self, cat: str) -> list[dict]:
        """解析 GitHub 网页目录页，提取子目录作为教程/案例条目（不消耗 API 额度）"""
        from urllib.parse import quote, unquote
        cat_enc = quote(cat)
        url = f"https://github.com/microsoft/ai-edu/tree/master/{cat_enc}"
        r = self.client.get(url, timeout=15)
        r.raise_for_status()
        html = r.text

        # 子目录链接形如 /microsoft/ai-edu/tree/master/%E5%AE%9E%E8%B7%B5%E6%A1%88%E4%BE%8B/xxx
        links = re.findall(
            r'href="(/microsoft/ai-edu/tree/master/' + re.escape(cat_enc) + r'/[^"]+?)"',
            html,
        )
        items = []
        seen = set()
        for link in links:
            name_enc = link.rstrip("/").split("/")[-1]
            if not name_enc or name_enc in seen:
                continue
            seen.add(name_enc)
            name = unquote(name_enc)
            full_url = "https://github.com" + unquote(link)
            items.append(self.build_article(
                title=name,
                url=full_url,
                summary=f"微软 AI 教育社区教程/案例：{name}",
                published_at=datetime.now(),
                author="Microsoft AI-Edu",
                category="tutorial",
                raw_text="",
                lang="cn",
            ))
        print(f"  [微软AI教育] {cat}: {len(items)} 条")
        return items
