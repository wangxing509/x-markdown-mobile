# -*- coding: utf-8 -*-
"""
知识库检索模块（v2）：FTS5 + jieba，支持领域/语言/分类过滤
"""
from database import fts_search, SessionLocal, KnowledgeBaseArticle


def search_knowledge_base(
    query: str,
    limit: int = 10,
    domain: str = "",
    lang: str = "",
    category: str = "",
) -> list[dict]:
    """FTS 检索，附带文件路径"""
    results = fts_search(query, domain=domain, lang=lang, category=category, limit=limit)
    db = SessionLocal()
    try:
        by_id = {a.id: a for a in db.query(KnowledgeBaseArticle).all()}
        out = []
        for r in results:
            rec = by_id.get(r["id"])
            out.append({
                "name": r["title"],
                "path": rec.filepath if rec else "",
                "snippet": r.get("snippet", ""),
                "score": r.get("score", 0.0),
                "domain": r.get("domain", ""),
                "lang": r.get("lang", ""),
                "category": r.get("category", ""),
                "source": r.get("source", ""),
            })
        return out
    finally:
        db.close()


def build_chat_context(
    query: str,
    filters: dict | None = None,
    top_k: int = 5,
) -> tuple[str, list[dict]]:
    """构建 Chat 上下文，返回 (context, references)"""
    filters = filters or {}
    results = search_knowledge_base(
        query,
        limit=top_k,
        domain=filters.get("domain", ""),
        lang=filters.get("lang", ""),
        category=filters.get("category", ""),
    )
    if not results:
        return "", []

    context_parts = []
    references = []
    for r in results:
        ref = {
            "name": r["name"],
            "path": r["path"],
            "snippet": r["snippet"],
            "domain": r.get("domain", ""),
            "lang": r.get("lang", ""),
        }
        references.append(ref)
        context_parts.append(f"[{r['name']}]({r['path']})\n{r['snippet']}")
    return "\n\n---\n\n".join(context_parts), references
