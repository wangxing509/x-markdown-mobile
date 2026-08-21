# -*- coding: utf-8 -*-
"""
文章分类器：article / tutorial / application（聚焦三类，拒绝 video/model）
优先根据来源平台特性分类，再按关键词细分
"""
import re

from config import (
    ARTICLE_KEYWORDS,
    TUTORIAL_KEYWORDS,
    APPLICATION_KEYWORDS,
)


def _build_pattern(keywords: list[str]) -> re.Pattern:
    return re.compile("|".join(re.escape(k) for k in keywords), re.IGNORECASE)


_article_pat = _build_pattern(ARTICLE_KEYWORDS)
_tutorial_pat = _build_pattern(TUTORIAL_KEYWORDS)
_app_pat = _build_pattern(APPLICATION_KEYWORDS)


# 平台默认分类偏好（按内容类型分布）
SOURCE_DEFAULT_CATEGORY = {
    "Hugging Face": "article",
    "WaytoAGI": "tutorial",
    "魔搭ModelScope": "article",
    "微软AI教育社区": "tutorial",
    "GitHub": "article",             # GitHub 默认 article（更多项目是文章/教程性质）
    "Reddit": "article",
    "腾讯CodeBuddy": "article",
    "DeepSeek": "article",
    "字节Trae": "article",
    "Kimi": "article",
}


def classify_article(article: dict) -> str:
    """
    分类单篇文章：只输出 article / tutorial / application 三类
    """
    # 已有非默认分类的保留（application 是明确标注的）
    current = article.get("category", "article")
    if current == "application":
        return current

    title = article.get("title", "") or ""
    summary = article.get("summary", "") or ""
    raw_text = article.get("raw_text", "") or ""
    source = article.get("source", "") or ""
    combined = f"{title} {summary} {raw_text}"

    # 关键词匹配评分
    scores = {
        "article": len(_article_pat.findall(combined)),
        "tutorial": len(_tutorial_pat.findall(combined)),
        "application": len(_app_pat.findall(combined)),
    }

    # GitHub 特殊处理：title 前缀
    if source == "GitHub":
        if title.lower().startswith(("awesome-", "tutorial", "course", "guide", "learn-")):
            return "tutorial"
        if any(kw in title.lower() for kw in ["tool", "cli", "app", "sdk", "framework"]):
            return "application"

    # 选最高分
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        # 无关键词命中，使用来源默认分类
        return SOURCE_DEFAULT_CATEGORY.get(source, "article")
    return best


def classify_batch(articles: list[dict]) -> list[dict]:
    """批量分类"""
    counts = {"article": 0, "tutorial": 0, "application": 0}
    for a in articles:
        a["category"] = classify_article(a)
        counts[a["category"]] = counts.get(a["category"], 0) + 1
    print(f"  [分类] {counts}")
    return articles


def extract_tags(text: str, max_tags: int = 5) -> list[str]:
    """从文本中提取关键词标签"""
    all_kw = ARTICLE_KEYWORDS + TUTORIAL_KEYWORDS + APPLICATION_KEYWORDS
    found = []
    seen = set()
    for kw in all_kw:
        if kw.lower() in text.lower() and kw.lower() not in seen:
            seen.add(kw.lower())
            found.append(kw)
            if len(found) >= max_tags:
                break
    return found
