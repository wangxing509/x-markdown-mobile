# -*- coding: utf-8 -*-
"""
领域判定：ai_audit（审计 ∩ AI）/ ai_general（仅 AI）/ None（不入库）。
审计 track 只收“AI×审计”交叉内容。
"""
from config import AUDIT_KEYWORDS, AUDIT_AI_KEYWORDS, AI_KEYWORDS
from processor.keywords import match_keywords


def classify_domain(article: dict) -> str | None:
    """返回 'ai_audit' / 'ai_general' / None"""
    title = article.get("title") or ""
    summary = article.get("summary") or ""
    raw = article.get("raw_text") or ""
    text = f"{title} {summary} {raw[:3000]}"

    hits_audit = bool(match_keywords(text, AUDIT_KEYWORDS))
    hits_ai = bool(match_keywords(text, AUDIT_AI_KEYWORDS)) or bool(match_keywords(text, AI_KEYWORDS))

    if hits_audit and hits_ai:
        return "ai_audit"
    if hits_ai:
        return "ai_general"
    return None

