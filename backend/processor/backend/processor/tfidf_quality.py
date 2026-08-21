# -*- coding: utf-8 -*-
"""
TF-IDF 关键词相关度评分模块
"""
import re
from config import AI_KEYWORDS

# 构建 TF-IDF 向量化器（懒加载）
_vectorizer = None
_keyword_matrix = None


def _ensure_vectorizer():
    global _vectorizer, _keyword_matrix
    if _vectorizer is not None:
        return
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        # 用 AI 关键词构建基准文档
        _vectorizer = TfidfVectorizer(max_features=5000)
        _keyword_matrix = _vectorizer.fit_transform([" ".join(AI_KEYWORDS)])
    except ImportError:
        print("  [TF-IDF] scikit-learn 未安装，相关度评分降级")


def compute_tfidf_relevance(title: str, summary: str = "", raw_text: str = "") -> float:
    """
    计算文章与 AI 关键词集合的 TF-IDF 余弦相似度
    返回 0.0 - 1.0
    """
    _ensure_vectorizer()
    if _vectorizer is None:
        # 降级：简单关键词匹配
        text = f"{title} {summary} {raw_text}".lower()
        matches = sum(1 for kw in AI_KEYWORDS if kw.lower() in text)
        return min(1.0, matches / 5.0)

    try:
        doc = f"{title} {summary} {raw_text[:1000]}"
        doc_matrix = _vectorizer.transform([doc])
        from sklearn.metrics.pairwise import cosine_similarity
        sim = cosine_similarity(doc_matrix, _keyword_matrix)[0][0]
        return float(max(0.0, min(1.0, sim)))
    except Exception as e:
        print(f"  [TF-IDF] 计算失败: {e}")
        return 0.0
