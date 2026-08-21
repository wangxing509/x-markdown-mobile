# -*- coding: utf-8 -*-
"""
国内头部 AI 企业官方社区爬虫：
  - 腾讯 CodeBuddy（https://copilot.tencent.com / GitHub Tencent/codebuddy）
  - DeepSeek（https://github.com/deepseek-ai）
  - 字节 Trae（https://www.trae.com.cn / GitHub）
  - Kimi / 月之暗面（https://github.com/Moonshot-AI）
抓取官方发布的技术文章、教程、应用案例（中文，高质量、权威）。
优先使用各企业公开 GitHub 仓库的博客/releases，官方域名页面作兜底。
"""
import re
from datetime import datetime

import httpx

from config import SOURCE_AUTHORITY, HEADERS
from crawler.base import BaseCrawler, extract_summary, clean_html


# 各企业来源定义：name -> (GitHub 仓库 / 官方域名)
CHINA_AI_SOURCES = [
    {
        "name": "腾讯CodeBuddy",
        "authority": SOURCE_AUTHORITY.get("腾讯CodeBuddy", 0.86),
        "gh_repo": "Tencent/codebuddy",          # 官方开源仓库
        "official_url": "https://copilot.tencent.com",
        "blog_path": None,                        # 暂无独立博客仓库，用 releases + 官方页
    },
    {
        "name": "DeepSeek",
        "authority": SOURCE_AUTHORITY.get("DeepSeek", 0.90),
        "gh_repo": "deepseek-ai/deepseek-ai.github.io",  # 官方博客
        "official_url": "https://www.deepseek.com",
        "blog_path": None,
    },
    {
        "name": "字节Trae",
        "authority": SOURCE_AUTHORITY.get("字节Trae", 0.84),
        "gh_repo": None,
        "official_url": "https://www.trae.com.cn",
        "blog_path": None,
    },
    {
        "name": "Kimi",
        "authority": SOURCE_AUTHORITY.get("Kimi", 0.85),
        "gh_repo": "Moonshot-AI/Moonshot-AI.github.io",  # 官方博客
        "official_url": "https://kimi.moonshot.cn",
        "blog_path": None,
    },
]


class ChinaAICrawler(BaseCrawler):
    source_name = "国内AI企业"
    source_authority = 0.86
    base_url = "https://www.deepseek.com"

    def fetch(self) -> list[dict]:
        articles = []
        for src in CHINA_AI_SOURCES:
            try:
                if src.get("gh_repo"):
                    articles.extend(self._fetch_github(src))
                else:
                    articles.extend(self._fetch_official_page(src))
            except Exception as e:
                print(f"  [国内AI] {src['name']} 失败: {e}")
        print(f"  [国内AI] 共: {len(articles)} 条")
        return articles

    def _fetch_github(self, src: dict) -> list[dict]:
        """通过 GitHub API 抓取企业博客仓库的 md 文章 / releases"""
        repo = src["gh_repo"]
        items = []
        # 1) 仓库根目录 md 文件（博客文章）
        url = f"https://api.github.com/repos/{repo}/contents/"
        resp = self.get(url)
        if resp.status_code == 200:
            try:
                data = resp.json()
            except Exception:
                data = []
            for entry in data:
                if not isinstance(entry, dict):
                    continue
                if entry.get("type") != "file" or not entry.get("name", "").endswith(".md"):
                    continue
                name = entry["name"][:-3]
                if name.lower() in ("readme", "license"):
                    continue
                title = name
                try:
                    r2 = self.get(entry.get("download_url", ""))
                    body = r2.text if r2.status_code == 200 else ""
                except Exception:
                    body = ""
                if len(body) < 150:
                    continue
                category = self._classify(title, body)
                item = self.build_article(
                    title=f"{src['name']} · {title}",
                    url=entry.get("html_url", src["official_url"]),
                    summary=extract_summary(body)[:200],
                    raw_text=body[:4000],
                    published_at=datetime.now(),
                    author=src["name"],
                    category=category,
                    score=src["authority"] * 100,
                    lang="cn",
                )
                item["source"] = src["name"]
                items.append(item)
        # 2) releases（版本发布 / 新功能教程）
        rel_url = f"https://api.github.com/repos/{repo}/releases"
        r3 = self.get(rel_url)
        if r3.status_code == 200:
            try:
                rels = r3.json()
            except Exception:
                rels = []
            for rel in rels[:6]:
                if not isinstance(rel, dict):
                    continue
                tag = rel.get("tag_name", "")
                rel_name = rel.get("name", tag)
                body = rel.get("body", "") or ""
                if not rel_name:
                    continue
                item = self.build_article(
                    title=f"{src['name']} 发布 {rel_name}",
                    url=rel.get("html_url", src["official_url"]),
                    summary=extract_summary(body)[:200],
                    raw_text=body[:3000],
                    published_at=datetime.fromisoformat(rel["published_at"].replace("Z", "+00:00")) if rel.get("published_at") else datetime.now(),
                    author=src["name"],
                    category="application",
                    score=src["authority"] * 95,
                    lang="cn",
                )
                item["source"] = src["name"]
                items.append(item)
        print(f"  [国内AI] {src['name']}(GitHub): {len(items)} 条")
        return items

    def _fetch_official_page(self, src: dict) -> list[dict]:
        """官方域名页面兜底（解析文章链接）"""
        try:
            resp = self.client.get(src["official_url"], headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                return []
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")
            items = []
            # 抓取含中文标题的链接
            seen = set()
            for a in soup.select("a[href]")[:40]:
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if not title or len(title) < 6 or len(title) > 50:
                    continue
                if href in seen:
                    continue
                seen.add(href)
                if not any(k in title.lower() for k in ["教程", "案例", "实战", "发布", "更新", "指南", "ai", "模型", "agent", "智能"]):
                    continue
                full = href if href.startswith("http") else (src["official_url"] + href)
                item = self.build_article(
                    title=f"{src['name']} · {title}",
                    url=full,
                    summary="",
                    raw_text="",
                    published_at=datetime.now(),
                    author=src["name"],
                    category=self._classify(title, ""),
                    score=src["authority"] * 70,
                    lang="cn",
                )
                item["source"] = src["name"]
                items.append(item)
            print(f"  [国内AI] {src['name']}(官方页): {len(items)} 条")
            return items
        except Exception as e:
            print(f"  [国内AI] {src['name']} 官方页失败: {e}")
            return []

    @staticmethod
    def _classify(title: str, body: str) -> str:
        combined = (title + " " + body[:200]).lower()
        if any(k in combined for k in ["教程", "tutorial", "guide", "实战", "上手", "搭建", "训练", "部署", "fine", "微调", "how", "quick start"]):
            return "tutorial"
        if any(k in combined for k in ["案例", "应用", "实践", "落地", "场景", "最佳实践", "release", "发布", "更新", "新功能"]):
            return "application"
        return "article"
