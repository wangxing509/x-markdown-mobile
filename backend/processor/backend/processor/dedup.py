# -*- coding: utf-8 -*-
"""
SimHash + URL + 标题相似度 三重去重
"""
from difflib import SequenceMatcher

from config import SIMHASH_THRESHOLD, TEXT_SIMILARITY_THRESHOLD

try:
    from simhash import Simhash
    HAS_SIMHASH = True
except ImportError:
    HAS_SIMHASH = False


def hamming_distance(h1: str, h2: str) -> int:
    """计算两个十六进制 SimHash 值的汉明距离"""
    if not h1 or not h2 or len(h1) != len(h2):
        return 999
    x = int(h1, 16)
    y = int(h2, 16)
    return (x ^ y).bit_count()


def text_similarity(t1: str, t2: str) -> float:
    """计算两段文本的相似度"""
    if not t1 or not t2:
        return 0.0
    return SequenceMatcher(None, t1.lower(), t2.lower()).ratio()


def deduplicate(articles: list[dict]) -> list[dict]:
    """
    三重去重：
    1. SimHash 汉明距离（快速预筛）
    2. URL 精确匹配
    3. 标题相似度
    """
    if not articles:
        return []

    kept = []

    for a in articles:
        is_dup = False
        for k in kept:
            # URL 完全相同
            if a.get("url") == k.get("url"):
                is_dup = True
                break

            # SimHash 快速检查
            if HAS_SIMHASH and a.get("simhash_value") and k.get("simhash_value"):
                if hamming_distance(a["simhash_value"], k["simhash_value"]) <= SIMHASH_THRESHOLD:
                    is_dup = True
                    break

            # 标题相似度复核
            title_sim = text_similarity(
                (a.get("title") or "")[:100],
                (k.get("title") or "")[:100],
            )
            if title_sim >= TEXT_SIMILARITY_THRESHOLD:
                is_dup = True
                break

        if not is_dup:
            kept.append(a)

    print(f"  [去重] 原始 {len(articles)} 条 → 去重后 {len(kept)} 条")
    return kept


def url_deduplicate(articles: list[dict]) -> list[dict]:
    """基于 URL 的简单去重"""
    seen = set()
    result = []
    for a in articles:
        url = a.get("url", "")
        if url and url not in seen:
            seen.add(url)
            result.append(a)
    return result
