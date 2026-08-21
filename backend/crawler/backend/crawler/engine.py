# -*- coding: utf-8 -*-
"""
爬虫引擎：注册强 AI 相关平台爬虫，并发执行
"""
import concurrent.futures
import re
from collections import defaultdict
from config import MAX_CONCURRENT, EXCLUDED_SOURCES
from crawler.base import BaseCrawler
from crawler.sources_github import GitHubCrawler
from crawler.sources_msai import MicrosoftAICrawler
from crawler.sources_reddit import RedditCrawler
from crawler.sources_huggingface import HuggingFaceCrawler
from crawler.sources_waytoagi import WaytoAGICrawler
from crawler.sources_modelscope import ModelScopeCrawler
from crawler.sources_china_ai import ChinaAICrawler
from crawler.sources_rss import build_rss_crawlers
from crawler.sources_audit import build_audit_crawlers
from processor.language import detect_lang
from processor.domain import classify_domain

# 每平台入选数量上限（宁缺毋滥：质量优先，但保底下限保证刷新 50+ 条）
PER_SOURCE_LIMIT: dict[str, int] = {
    "GitHub": 35,
    "微软AI教育社区": 30,
    "Reddit": 20,
    "Hugging Face": 20,
    "WaytoAGI": 15,
    "魔搭ModelScope": 15,
    "审计署": 12,
    "中国内部审计协会": 12,
    "中国注册会计师协会": 12,
    "Journal of Accountancy": 20,
    "IIA Internal Auditor": 15,
    "ISACA": 15,
}
DEFAULT_SOURCE_LIMIT = 15

# 低质量标题垃圾词：含这些词且无实质内容的推广/营销/资讯类标题
LOW_QUALITY_TITLE_PATTERNS = [
    r"获奖名单", r"获奖公示", r"获奖结果", r"一等奖", r"二等奖", r"三等奖",
    r"参会指南", r"参会报名", r"参会须知", r"会议通知", r"报名入口", r"报名截止",
    r"直播预告", r"直播回放", r"线上直播", r"即将直播",
    r"征文通知", r"征文启事", r"征文活动", r"征稿", r"约稿",
    r"招聘", r"招募", r"招贤纳士", r"诚聘", r"实习招聘",
    r"问卷调查", r"有奖调查", r"抽奖", r"福利领取", r"限时免费领",
    r"重磅来袭", r"震撼发布", r"喜报", r"捷报", r"喜提",
    r"课程表", r"开课通知", r"开班", r"训练营报名",
]

# 标题中若含这些"营销/低质"词，但只要同时含强 AI 技术词则放行
TECH_SAVER_WORDS = [
    "模型", "算法", "大模型", "LLM", "深度学习", "神经网络", "Transformer",
    "Agent", "智能体", "RAG", "微调", "推理", "训练", "部署", "ChatGPT",
    "DeepSeek", "Qwen", "文心", "算力", "GPU", "Stable Diffusion", "diffusion",
    "PyTorch", "TensorFlow", "Python", "论文", "开源", "教程", "实战", "源码",
]


def _is_low_quality_title(title: str) -> bool:
    """判断标题是否为低质量推广/资讯类（无正文价值的垃圾信息）"""
    if not title:
        return True
    t = title.strip()
    # 命中垃圾词
    hit_spam = any(re.search(p, t) for p in LOW_QUALITY_TITLE_PATTERNS)
    if not hit_spam:
        return False
    # 若同时含技术词，视为正常内容，放行
    if any(w.lower() in t.lower() for w in TECH_SAVER_WORDS):
        return False
    return True


def _has_real_content(article: dict) -> bool:
    """判断是否有正文（避免只有导读/摘要无实质内容）"""
    summary = (article.get("summary") or "").strip()
    raw = (article.get("raw_text") or "").strip()
    # 正文过短视为无实质内容（外文同样要求有正文，保证英文原文可正常打开呈现）
    if len(summary) < 20 and len(raw) < 60:
        return False
    # 标题党：摘要与标题几乎相同（只有导读）
    title = (article.get("title") or "").strip()
    if title and summary and len(summary) <= len(title) + 10 and not raw:
        return False
    return True


def filter_low_quality(articles: list[dict]) -> list[dict]:
    """过滤低质量内容：低质标题 + 无正文 + 类型限定（只保留 article/tutorial/application）"""
    kept = []
    dropped_title = 0
    dropped_nocontent = 0
    dropped_type = 0
    for a in articles:
        if _is_low_quality_title(a.get("title", "")):
            dropped_title += 1
            continue
        if not _has_real_content(a):
            dropped_nocontent += 1
            continue
        # 仅保留三类：文章 / 教程 / 应用案例（拒绝 video/model 主导内容）
        if a.get("category") not in ("article", "tutorial", "application"):
            dropped_type += 1
            continue
        kept.append(a)
    print(f"  [质量过滤] 低质标题剔除 {dropped_title} 条，无正文剔除 {dropped_nocontent} 条，非三类剔除 {dropped_type} 条")
    return kept


class CrawlerEngine:
    """爬虫引擎（强 AI 相关平台）"""

    def __init__(self):
        self.crawlers: list[BaseCrawler] = []
        self.failures: list[str] = []

    def register_all(self) -> "CrawlerEngine":
        """根据 ~/.xmarkdown/sources.json 注册启用的爬虫"""
        from settings_store import get_sources
        sources = get_sources()
        enabled = {s["name"] for s in sources if s.get("enabled", True)}

        crawlers: list[BaseCrawler] = []
        # 中文 AI 源（HTML/API）
        if "WaytoAGI" in enabled:
            crawlers.append(WaytoAGICrawler())
        if "魔搭ModelScope" in enabled:
            crawlers.append(ModelScopeCrawler())
        if "微软AI教育社区" in enabled:
            crawlers.append(MicrosoftAICrawler())
        # 国内头部 AI 企业官方社区（按子源启停）
        china_ai_enabled = [
            n for n in ("腾讯CodeBuddy", "DeepSeek", "字节Trae", "Kimi") if n in enabled
        ]
        if china_ai_enabled:
            crawlers.append(ChinaAICrawler())
        if "GitHub" in enabled:
            crawlers.append(GitHubCrawler())
        if "Reddit" in enabled:
            crawlers.append(RedditCrawler())
        if "Hugging Face" in enabled:
            crawlers.append(HuggingFaceCrawler())

        # RSS 源（官方博客 + 外文审计源）
        crawlers.extend(build_rss_crawlers(sources))
        # 中文审计官方站点
        crawlers.extend(build_audit_crawlers(sources))

        # 剔除被明确排除的平台（如掘金/博客园/知乎）
        self.crawlers = [c for c in crawlers if c.source_name not in EXCLUDED_SOURCES]
        print(f"  [引擎] 启用爬虫: {[c.source_name for c in self.crawlers]}")
        return self

    def run(self) -> list[dict]:
        """并发执行所有爬虫"""
        all_articles = []
        self.failures = []

        def _run_crawler(crawler: BaseCrawler) -> list[dict]:
            try:
                print(f"  [爬虫] 开始: {crawler.source_name}")
                result = crawler.fetch()
                print(f"  [爬虫] {crawler.source_name}: {len(result)} 条")
                if not result:
                    self.failures.append(f"{crawler.source_name}: 0 条")
                return result
            except Exception as e:
                print(f"  [爬虫] {crawler.source_name} 异常: {e}")
                self.failures.append(f"{crawler.source_name}: {str(e)[:80]}")
                return []
            finally:
                crawler.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
            futures = {executor.submit(_run_crawler, c): c for c in self.crawlers}
            for future in concurrent.futures.as_completed(futures):
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                except Exception as e:
                    print(f"  [爬虫] 执行异常: {e}")
                    self.failures.append(f"executor: {str(e)[:80]}")

        # 质量过滤：剔除低质标题 / 无正文内容
        all_articles = filter_low_quality(all_articles)

        # 领域与语言判定（逐篇）
        kept = []
        for a in all_articles:
            a["domain"] = classify_domain(a)
            if not a.get("domain"):
                continue
            a["lang"] = detect_lang(a)
            kept.append(a)
        all_articles = kept

        # 每平台抓取数量上限（保证候选池多样性；入选上限由配额阶段控制）
        by_src = defaultdict(list)
        for a in all_articles:
            by_src[a.get("source", "未知")].append(a)

        limited = []
        for src, items in by_src.items():
            items.sort(key=lambda x: (x.get("score", 0) or 0, x.get("likes", 0) or 0), reverse=True)
            cap = PER_SOURCE_LIMIT.get(src, DEFAULT_SOURCE_LIMIT)
            limited.extend(items[:cap])

        print(f"  [爬虫] 原始: {len(all_articles)} 条 -> 限流后: {len(limited)} 条")
        return limited

    def run_with_fallback(self) -> list[dict]:
        """执行爬取，失败时使用缓存"""
        try:
            articles = self.run()
            if articles:
                self._save_cache(articles)
                return articles
        except Exception as e:
            print(f"  [爬虫] 引擎异常: {e}")

        # 降级：加载缓存
        return self._load_cache()

    def _save_cache(self, articles: list[dict]):
        """保存缓存"""
        import json
        from config import DATA_DIR
        cache_file = DATA_DIR / "cache_articles.json"
        try:
            serializable = []
            for a in articles:
                a_copy = {**a}
                if hasattr(a_copy.get("published_at"), "isoformat"):
                    a_copy["published_at"] = a_copy["published_at"].isoformat()
                serializable.append(a_copy)
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(serializable, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  [缓存] 保存失败: {e}")

    def _load_cache(self) -> list[dict]:
        """加载缓存"""
        import json
        from config import DATA_DIR
        cache_file = DATA_DIR / "cache_articles.json"
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 恢复 datetime
            from datetime import datetime
            for a in data:
                if a.get("published_at") and isinstance(a["published_at"], str):
                    try:
                        a["published_at"] = datetime.fromisoformat(a["published_at"])
                    except Exception:
                        a["published_at"] = datetime.now()
            print(f"  [缓存] 加载: {len(data)} 条")
            return data
        except FileNotFoundError:
            print(f"  [缓存] 无缓存文件")
            return []
        except Exception as e:
            print(f"  [缓存] 加载失败: {e}")
            return []
