# -*- coding: utf-8 -*-
"""
综合评分模块：时效30% + 权威20% + 热度20% + TF-IDF相关度15% + 互动反馈15%
"""
import math
import re
from datetime import datetime

from config import SCORE_WEIGHTS
from processor.tfidf_quality import compute_tfidf_relevance


def _normalize(value: float, max_val: float) -> float:
    """归一化到 0-1"""
    if max_val <= 0:
        return 0.0
    return min(1.0, value / max_val)


def compute_score(article: dict, now: datetime = None, max_likes: int = 1, max_comments: int = 1) -> float:
    """
    综合评分模型：
    - 时效性 (30%)：24h 内满分，超过 7 天衰减
    - 权威度 (20%)：来源权威度
    - 热度 (20%)：基于内容长度和关键词
    - TF-IDF 相关度 (15%)：与 AI 关键词的余弦相似度
    - 互动反馈 (15%)：点赞数 + 评论数归一化
    """
    if now is None:
        now = datetime.now()

    w = SCORE_WEIGHTS

    # ---------- 1. 时效性 ----------
    published = article.get("published_at")
    freshness = 0.5
    if isinstance(published, datetime):
        hours_ago = (now - published.replace(tzinfo=None)).total_seconds() / 3600
        if hours_ago <= 24:
            freshness = 1.0
        elif hours_ago <= 168:
            freshness = max(0, 1.0 - (hours_ago - 24) / (168 - 24))
        else:
            freshness = max(0, 0.2 - (hours_ago - 168) / 720)

    # ---------- 2. 权威度 ----------
    authority = article.get("source_authority", 0.5)

    # 粉丝权重加分
    author_followers = article.get("author_followers", 0)
    follower_boost = min(0.2, math.log10(max(1, author_followers)) / 10)
    authority = min(1.0, authority + follower_boost)

    # ---------- 3. 热度 ----------
    raw_text = article.get("raw_text", "") or ""
    summary = article.get("summary", "") or ""
    title = article.get("title", "") or ""
    text_len = len(raw_text) + len(summary) + len(title)
    hotness = min(1.0, text_len / 2000)
    numbers = re.findall(r'\d+[万亿千百]?', title)
    hotness = min(1.0, hotness + len(numbers) * 0.02)

    # ---------- 4. TF-IDF 相关度 ----------
    tfidf_relevance = compute_tfidf_relevance(title, summary, raw_text)

    # ---------- 5. 互动反馈 ----------
    likes = article.get("likes", 0)
    comments = article.get("comments", 0)
    engagement = (_normalize(likes, max_likes) + _normalize(comments, max_comments)) / 2

    # ---------- 综合评分 ----------
    score = (
        w["freshness"] * freshness
        + w["authority"] * authority
        + w["hotness"] * hotness
        + w["tfidf_relevance"] * tfidf_relevance
        + w["engagement"] * engagement
    ) * 100

    return round(score, 1)


def rank_and_score(articles: list[dict]) -> list[dict]:
    """评分并排序"""
    now = datetime.now()

    # 计算最大点赞/评论数用于归一化（确保转为数字）
    def _safe_int(v):
        try:
            return int(v) if v else 0
        except (ValueError, TypeError):
            return 0

    max_likes = max((_safe_int(a.get("likes", 0)) for a in articles), default=1) or 1
    max_comments = max((_safe_int(a.get("comments", 0)) for a in articles), default=1) or 1

    # 确保所有文章的 likes/comments 是数字
    for a in articles:
        a["likes"] = _safe_int(a.get("likes", 0))
        a["comments"] = _safe_int(a.get("comments", 0))

    for a in articles:
        a["score"] = compute_score(a, now, max_likes, max_comments)

    articles.sort(key=lambda x: x["score"], reverse=True)
    if articles:
        print(f"  [评分] 最高 {articles[0]['score']} 分")
    return articles
