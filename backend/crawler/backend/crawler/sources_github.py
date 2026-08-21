# -*- coding: utf-8 -*-
"""
GitHub 爬虫：REST API + README API
获取 AI 相关高分 repo，同时通过 README API 获取正文内容
"""
from datetime import datetime
import httpx
from config import SOURCE_AUTHORITY, HEADERS
from crawler.base import BaseCrawler, clean_html, extract_summary


# GitHub 搜索查询：按内容类型分类
SEARCH_QUERIES = {
    "application": [
        "AI agent framework stars:>1000",
        "AI tool application stars:>500",
        "audit AI stars:>5",
    ],
    "tutorial": [
        "AI tutorial awesome stars:>500",
        "LLM course stars:>500",
    ],
    "article": [
        "AI best practices stars:>200",
        "audit data analytics stars:>5",
    ],
}


class GitHubCrawler(BaseCrawler):
    source_name = "GitHub"
    source_authority = SOURCE_AUTHORITY["GitHub"]
    base_url = "https://github.com"

    def __init__(self):
        super().__init__()
        # README 请求使用单独的 client（更短超时）
        self.readme_client = httpx.Client(
            headers={**HEADERS, "Accept": "application/vnd.github.v3.raw+json"},
            timeout=httpx.Timeout(12, connect=6),
            follow_redirects=True,
        )

    def fetch(self) -> list[dict]:
        articles = []
        try:
            articles.extend(self._fetch_trending())
        except Exception as e:
            print(f"  [GitHub] Trending 失败: {e}")
        try:
            articles.extend(self._fetch_api_multi())
        except Exception as e:
            print(f"  [GitHub] API 失败: {e}")
        return articles

    def _fetch_trending(self) -> list[dict]:
        """抓取 GitHub Trending (AI 相关)"""
        url = "https://github.com/trending?since=daily"
        resp = self.get(url)
        if resp.status_code != 200:
            return []

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
        items = []
        repos = soup.select("article.Box-row")[:25]

        for repo in repos:
            try:
                title_el = repo.select_one("h2 a")
                if not title_el:
                    continue
                repo_path = title_el.get("href", "").strip()
                title = repo_path.lstrip("/")
                url = f"https://github.com{repo_path}"

                desc_el = repo.select_one("p")
                summary = desc_el.get_text(strip=True) if desc_el else ""

                stars_el = repo.select("a.Link--muted")
                stars = 0
                for a in stars_el:
                    href = a.get("href", "")
                    if "/stargazers" in href:
                        stars_text = a.get_text(strip=True).replace(",", "").replace("k", "")
                        try:
                            stars = int(float(stars_text) * 1000) if "." in stars_text else int(stars_text)
                        except ValueError:
                            pass

                # AI 相关过滤
                combined = f"{title} {summary}".lower()
                ai_kw = ["ai", "llm", "gpt", "agent", "transformer", "diffusion", "rag", "prompt", "langchain", "autogpt", "chat", "model"]
                if not any(kw in combined for kw in ai_kw):
                    continue

                category = self._classify_repo(title, summary)

                # 获取 README 作为正文
                raw_text = self._fetch_readme(title)

                items.append(self.build_article(
                    title=title,
                    url=url,
                    summary=summary or extract_summary(raw_text),
                    published_at=datetime.now(),
                    likes=stars,
                    comments=0,
                    category=category,
                    raw_text=raw_text,
                    lang="cn",
                ))
            except Exception:
                continue
        print(f"  [GitHub] Trending: {len(items)} 条")
        return items

    def _fetch_api_multi(self) -> list[dict]:
        """通过 GitHub REST API 多查询搜索"""
        items = []
        for category, queries in SEARCH_QUERIES.items():
            for query in queries:
                try:
                    partial = self._fetch_api_single(query, category)
                    items.extend(partial)
                except Exception as e:
                    print(f"  [GitHub] API query '{query[:30]}' 失败: {e}")
        print(f"  [GitHub] API: {len(items)} 条")
        return items

    def _fetch_api_single(self, query: str, category: str) -> list[dict]:
        """单次 API 搜索"""
        import time
        url = "https://api.github.com/search/repositories"
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": 8}
        resp = self.get(url, params=params)
        time.sleep(7)  # 未认证搜索 API 限流 10 次/分钟
        if resp.status_code != 200:
            return []

        data = resp.json()
        items = []
        for repo in data.get("items", [])[:8]:
            owner = repo.get("owner", {}) or {}
            full_name = repo.get("full_name", "")
            summary = repo.get("description", "") or ""

            # 获取 README 作为正文（最多前 5 个，避免 API 限流）
            raw_text = ""
            if len(items) < 5:
                raw_text = self._fetch_readme(full_name)

            items.append(self.build_article(
                title=full_name,
                url=repo.get("html_url", ""),
                summary=summary or extract_summary(raw_text),
                published_at=datetime.fromisoformat(repo.get("updated_at", "").replace("Z", "+00:00")) if repo.get("updated_at") else None,
                likes=repo.get("stargazers_count", 0),
                comments=repo.get("forks_count", 0),
                author=owner.get("login", "") if isinstance(owner, dict) else "",
                author_followers=owner.get("followers", 0) if isinstance(owner, dict) else 0,
                category=category,
                raw_text=raw_text,
                lang="cn",
            ))
        return items

    def _fetch_readme(self, repo_full_name: str) -> str:
        """通过 GitHub API 获取 README 内容"""
        try:
            url = f"https://api.github.com/repos/{repo_full_name}/readme"
            resp = self.readme_client.get(url)
            if resp.status_code == 200:
                # README 可能是 Markdown 或 HTML
                content = resp.text
                # 如果是 HTML，转为纯文本
                if content.strip().startswith("<"):
                    content = clean_html(content)
                return content[:5000]  # 限制长度避免数据库过大
        except Exception:
            pass
        return ""

    def _classify_repo(self, title: str, description: str) -> str:
        """根据 repo 名称和描述智能分类"""
        combined = f"{title} {description}".lower()
        if any(kw in combined for kw in ["awesome", "tutorial", "course", "guide", "learn", "study", "入门", "教程", "学习"]):
            return "tutorial"
        if any(kw in combined for kw in ["tool", "app", "platform", "cli", "sdk", "framework", "工作室", "工具", "助手"]):
            return "application"
        if any(kw in combined for kw in ["model", "llm", "gpt", "bert", "transformer", "diffusion", "checkpoint", "pretrained", "模型"]):
            return "model"
        return "article"

    def close(self):
        super().close()
        self.readme_client.close()
