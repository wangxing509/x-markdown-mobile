# -*- coding: utf-8 -*-
"""
Reddit 爬虫：JSON API 获取 AI 相关 subreddit 高分帖
"""
from datetime import datetime
from config import SOURCE_AUTHORITY
from crawler.base import BaseCrawler


class RedditCrawler(BaseCrawler):
    source_name = "Reddit"
    source_authority = SOURCE_AUTHORITY["Reddit"]
    base_url = "https://www.reddit.com"

    # 高质量 AI 板块（按权威度排序）；聚焦文章/教程/应用案例
    SUBREDDITS = [
        ("MachineLearning", 0.95),   # 机器学习研究/讨论
        ("LocalLLaMA", 0.95),        # 本地大模型部署/应用
        ("ChatGPT", 0.90),           # ChatGPT 技巧/案例
        ("artificial", 0.88),        # 通用 AI 讨论
        ("OpenAI", 0.90),            # OpenAI 技术
        ("LLMDevs", 0.88),           # LLM 开发实战
        ("PromptEngineering", 0.85), # 提示词工程教程
        ("AITools", 0.85),           # AI 工具/应用
        ("MachineLearningProjects", 0.84),  # 项目案例
        ("deeplearning", 0.85),      # 深度学习
    ]

    # 负向过滤：图片/投票/低质灌水帖
    NEGATIVE = [
        "i.redd.it", "imgur.com", "youtu.be", "youtube.com",
        "check out my", "rate my", "what do you think of my",
        "weekly help", "simple questions", "megathread",
        "who's hiring", "hiring thread",
    ]

    def fetch(self) -> list[dict]:
        import concurrent.futures
        articles: list[dict] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            futures = {
                ex.submit(self._fetch_subreddit, sub, weight): sub
                for sub, weight in self.SUBREDDITS
            }
            for fut in concurrent.futures.as_completed(futures):
                sub = futures[fut]
                try:
                    articles.extend(fut.result())
                except Exception as e:
                    print(f"  [Reddit] r/{sub} 失败: {e}")
        return articles

    def _fetch_subreddit(self, subreddit: str, weight: float) -> list[dict]:
        """获取 subreddit 高质量帖（top/month 保证内容与深度）"""
        url = f"https://www.reddit.com/r/{subreddit}/top.json?limit=20&t=month"
        headers = {**self.client.headers, "User-Agent": "XMarkdown/1.0 (by /u/xmarkdown)"}
        resp = self.client.get(url, headers=headers)
        if resp.status_code != 200:
            return []

        try:
            data = resp.json()
        except Exception:
            return []

        items = []
        children = data.get("data", {}).get("children", [])
        for child in children[:20]:
            post = child.get("data", {})
            if not isinstance(post, dict):
                continue
            title = post.get("title", "")
            permalink = post.get("permalink", "")
            article_url = f"https://www.reddit.com{permalink}" if permalink else ""
            score = int(post.get("score", 0) or 0)
            num_comments = int(post.get("num_comments", 0) or 0)
            author = post.get("author", "")
            created_utc = post.get("created_utc", 0)
            selftext = (post.get("selftext", "") or "").strip()
            low = title.lower()

            # 负向过滤
            if any(k in low for k in self.NEGATIVE):
                continue
            # 质量门槛：有正文且足够长，或高赞高互动的链接帖（教程/案例常带外链）
            is_self = post.get("is_self", True)
            if selftext and len(selftext) >= 120:
                summary = selftext[:220]
                category = "article" if (subreddit in ("MachineLearning", "artificial", "deeplearning")) else "tutorial"
            elif score >= 200 and num_comments >= 30 and not is_self:
                summary = title + "\n\n" + (post.get("url", "") or "")
                category = "application"
            else:
                continue

            items.append(self.build_article(
                title=title,
                url=article_url,
                summary=summary,
                raw_text=selftext,
                published_at=datetime.fromtimestamp(created_utc) if created_utc else None,
                likes=score,
                comments=num_comments,
                author=author,
                category=category,
                score=float(score) * weight,
                lang="en",
            ))
        print(f"  [Reddit] r/{subreddit}: {len(items)} 条")
        return items
