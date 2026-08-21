# -*- coding: utf-8 -*-
"""
关键词匹配工具：ASCII 词用词边界匹配，中文用子串匹配，
避免 "AI" 误命中 "said/train" 等英文单词。
"""
import re

_ascii_pat_cache: dict[str, re.Pattern] = {}


def _is_ascii(kw: str) -> bool:
    return bool(re.fullmatch(r"[\x00-\x7f]+", kw))


def _pattern_for(kw: str) -> re.Pattern:
    key = kw.lower()
    if key not in _ascii_pat_cache:
        # 词边界 + 忽略大小写；含空格/斜杠的短语同样按整体匹配
        _ascii_pat_cache[key] = re.compile(r"\b" + re.escape(key) + r"\b", re.IGNORECASE)
    return _ascii_pat_cache[key]


def match_keywords(text: str, keywords: list[str]) -> list[str]:
    """返回命中的关键词列表"""
    if not text:
        return []
    low = text.lower()
    hits = []
    for kw in keywords:
        if not kw:
            continue
        if _is_ascii(kw):
            if _pattern_for(kw).search(low):
                hits.append(kw)
        else:
            if kw.lower() in low:
                hits.append(kw)
    return hits

