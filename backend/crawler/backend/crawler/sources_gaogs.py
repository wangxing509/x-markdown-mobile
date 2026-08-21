# -*- coding: utf-8 -*-
"""
GAO.GS 高手社区（现已并入 LINUX人社区 linuxren.com）爬虫
抓取 AI 板块（forum/5）的高质量讨论帖子。
内容均为 AI 工具、模型、实践经验的分享与讨论，与 AI 强相关。
"""
import re
from datetime import datetime

from config import SOURCE_AUTHORITY
from crawler.base import BaseCrawler, clean_html


class GaoGSCrawler(BaseCrawler):
    source_name = "GAO.GS高手社区"
    source_authority = SOURCE_AUTHORITY.get("GAO.GS高手社区", 0.72)
    base_url = "https://www.gao.gs"

    AI_FORUM_ID = 5

    def fetch(self) -> list[dict]:
        articles = []
        try:
            articles.extend(self._fetch_ai_forum())
        except Exception as e:
            print(f"  [GAO.GS] AI板块 失败: {e}")
        print(f"  [GAO.GS] 共: {len(articles)} 条")
        return articles

    def _fetch_ai_forum(self) -> list[dict]:
        """抓取 AI 板块（forum/5）帖子列表"""
        # 域名已迁移到 linuxren.com，基类 httpx 已 follow_redirects
        url = f"https://www.gao.gs/forum/{self.AI_FORUM_ID}"
        r = self.client.get(url, timeout=15)
        r.raise_for_status()
        html = r.text

        # 提取 thread id 与标题（Discuz 列表：<a href="thread-数字">标题</a> 或 /thread/数字）
        # 匹配所有含 thread 的链接及其文字
        block_re = re.compile(
            r'<a[^>]+href="[^"]*?thread[-/](\d+)[^"]*?"[^>]*>(.*?)</a>',
            re.S | re.I,
        )
        # 广告/营销过滤词
        SPAM = ["出售", "低价", "会员", "代写", "代做", "招聘", "招人", "招生",
                "加微信", "私聊", "优惠", "代购", "刷", "推广", "广告", "联系QQ",
                "联系方式", "一套", "源码出售", "出售源码"]
        items = []
        seen = set()
        for mid, raw_title in block_re.findall(html):
            title = clean_html(raw_title).strip()
            # 过滤导航/非帖子链接（标题过短或含特定词）
            if len(title) < 4:
                continue
            if title in ("AI", "返回", "下一页", "上一页", "版块"):
                continue
            # 过滤广告/营销帖
            if any(w in title for w in SPAM):
                continue
            if mid in seen:
                continue
            seen.add(mid)
            thread_url = f"https://www.gao.gs/thread/{mid}"
            items.append(self.build_article(
                title=title,
                url=thread_url,
                summary=f"GAO.GS 高手社区 AI 讨论：{title}",
                published_at=datetime.now(),
                author="GAO.GS 社区",
                category="article",
                raw_text=title,
            ))
        print(f"  [GAO.GS] AI板块: {len(items)} 条")
        return items[:30]
