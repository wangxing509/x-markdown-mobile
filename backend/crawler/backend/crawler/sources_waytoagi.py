# -*- coding: utf-8 -*-
"""
WaytoAGI 爬虫：基于 GitHub 仓库 waytoAGI/waytoAGI
抓取高质量 AI 学习路径 / 工具清单 / 教程 / 应用案例（中文）。
WaytoAGI 是中文 AI 领域最系统的学习资源导航，内容由社区资深维护，
质量高、拒绝注水。通过 GitHub API 获取 README 及章节 md 文件作为条目。
"""
import re
from datetime import datetime

import httpx

from config import SOURCE_AUTHORITY, HEADERS
from crawler.base import BaseCrawler, extract_summary


class WaytoAGICrawler(BaseCrawler):
    source_name = "WaytoAGI"
    source_authority = SOURCE_AUTHORITY.get("WaytoAGI", 0.90)
    base_url = "https://github.com/waytoAGI/waytoAGI"

    RAW_BASE = "https://raw.githubusercontent.com/waytoAGI/waytoAGI/main"

    # 优先抓取的章节（高质量教程/案例方向）
    PRIORITY_DIRS = [
        "?",
    ]

    def fetch(self) -> list[dict]:
        articles = []
        try:
            articles.extend(self._fetch_readme_sections())
        except Exception as e:
            print(f"  [WaytoAGI] README 章节失败: {e}")
        try:
            articles.extend(self._fetch_dir_docs())
        except Exception as e:
            print(f"  [WaytoAGI] 目录文档失败: {e}")
        print(f"  [WaytoAGI] 共: {len(articles)} 条")
        return articles

    def _get_readme(self) -> str:
        """获取 WaytoAGI README 原始文本"""
        url = f"{self.RAW_BASE}/README.md"
        resp = self.get(url)
        if resp.status_code != 200:
            return ""
        return resp.text

    def _fetch_readme_sections(self) -> list[dict]:
        """将 README 按二级标题拆分为高质量章节条目（每个章节即一篇教程/导航）"""
        md = self._get_readme()
        if not md:
            return []
        # 按 '## ' 或 '### ' 切分
        parts = re.split(r'\n#{2,3}\s+', md)
        title0 = (re.match(r'^#\s+(.+)', md) or [None, "WaytoAGI AI 学习路径"])[1]
        items = []
        for i, part in enumerate(parts[1:], start=1):
            lines = part.strip().splitlines()
            if not lines:
                continue
            heading = lines[0].strip()
            if len(heading) < 3 or len(heading) > 60:
                continue
            body = "\n".join(lines[1:]).strip()
            # 过滤纯链接堆（导航页）过短的章节
            if len(body) < 120:
                continue
            # 判断类别：教程/文章/应用案例
            if any(k in heading.lower() for k in ["教程", "tutorial", "guide", "实战", "上手", "搭建", "怎么", "如何"]):
                category = "tutorial"
            elif any(k in heading.lower() for k in ["案例", "应用", "工具", "平台", "产品", "最佳实践", "实践"]):
                category = "application"
            else:
                category = "article"
            anchor = re.sub(r'[^\w\u4e00-\u9fa5-]', '-', heading)
            url = f"{self.base_url}#readme"
            items.append(self.build_article(
                title=f"WaytoAGI · {heading}",
                url=url,
                summary=extract_summary(body)[:200],
                raw_text=body[:4000],
                published_at=datetime.now(),
                author="WaytoAGI",
                category=category,
                score=90.0,
                lang="cn",
            ))
        print(f"  [WaytoAGI] README 章节: {len(items)} 条")
        return items

    def _fetch_dir_docs(self) -> list[dict]:
        """抓取仓库子目录下的文档（如 框架/工具 分类页）"""
        # 主要抓取根目录的 md 文件（除 README）
        url = "https://api.github.com/repos/waytoAGI/waytoAGI/contents/"
        resp = self.get(url)
        if resp.status_code != 200:
            return []
        try:
            data = resp.json()
        except Exception:
            return []
        items = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "file":
                continue
            name = entry.get("name", "")
            if not name.endswith(".md") or name.lower() == "readme.md":
                continue
            title = name[:-3]
            raw_url = f"{self.RAW_BASE}/{name}"
            try:
                r2 = self.get(raw_url)
                body = r2.text if r2.status_code == 200 else ""
            except Exception:
                body = ""
            if len(body) < 150:
                continue
            category = "article"
            if any(k in title.lower() for k in ["教程", "tutorial", "guide", "实战", "上手"]):
                category = "tutorial"
            elif any(k in title.lower() for k in ["案例", "应用", "工具", "平台", "产品"]):
                category = "application"
            items.append(self.build_article(
                title=f"WaytoAGI · {title}",
                url=entry.get("html_url", self.base_url),
                summary=extract_summary(body)[:200],
                raw_text=body[:4000],
                published_at=datetime.now(),
                author="WaytoAGI",
                category=category,
                score=85.0,
                lang="cn",
            ))
        print(f"  [WaytoAGI] 目录文档: {len(items)} 条")
        return items
