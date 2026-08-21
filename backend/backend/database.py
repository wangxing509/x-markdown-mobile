# -*- coding: utf-8 -*-
"""
SQLite 数据库 ORM 模型
"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Float, Text, DateTime, Integer, Index, Boolean,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Top100Article(Base):
    """每日精选文章表"""
    __tablename__ = "top100_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1024), unique=True, nullable=False)
    summary = Column(Text, default="")
    source = Column(String(100), nullable=False)
    source_authority = Column(Float, default=0.5)
    published_at = Column(DateTime, default=datetime.now)
    raw_text = Column(Text, default="")
    simhash_value = Column(String(64), default="")
    category = Column(String(20), default="article")
    score = Column(Float, default=0.0)
    rank = Column(Integer, default=0)
    tags = Column(String(500), default="")
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    author = Column(String(200), default="")
    author_followers = Column(Integer, default=0)
    curated_at = Column(DateTime, default=datetime.now)
    # v2 新增字段
    lang = Column(String(10), default="")            # cn / en（逐篇判定）
    domain = Column(String(20), default="ai_general")  # ai_general / ai_audit
    verified = Column(Boolean, default=False)        # 已通过原文抓取验证
    md_length = Column(Integer, default=0)           # 验证时抓到的 markdown 长度

    __table_args__ = (
        Index("idx_top100_category", "category"),
        Index("idx_top100_score", "score"),
        Index("idx_top100_date", "curated_at"),
        Index("idx_top100_domain", "domain"),
        Index("idx_top100_lang", "lang"),
    )


class KnowledgeBaseArticle(Base):
    """知识库文章表（元数据 + 双文件路径）"""
    __tablename__ = "kb_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    filepath = Column(String(1024), nullable=False)          # 原文文件
    translated_path = Column(String(1024), default="")      # 译文文件（可为空）
    source_url = Column(String(1024), default="", unique=True)
    original_md = Column(Text, default="")
    translated_md = Column(Text, default="")
    skill_md = Column(Text, default="")
    category = Column(String(20), default="article")
    domain = Column(String(20), default="ai_general")       # ai_general / ai_audit
    lang = Column(String(10), default="")
    source = Column(String(100), default="")
    tags = Column(String(500), default="")
    saved_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_kb_title", "title"),
        Index("idx_kb_date", "saved_at"),
        Index("idx_kb_domain", "domain"),
    )


class RefreshLog(Base):
    """刷新日志表"""
    __tablename__ = "refresh_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, default=datetime.now)
    finished_at = Column(DateTime, nullable=True)
    raw_count = Column(Integer, default=0)
    dedup_count = Column(Integer, default=0)
    verified_count = Column(Integer, default=0)
    curated_count = Column(Integer, default=0)
    en_count = Column(Integer, default=0)
    cn_count = Column(Integer, default=0)
    audit_count = Column(Integer, default=0)
    general_count = Column(Integer, default=0)
    shortfall = Column(Integer, default=0)
    status = Column(String(20), default="running")
    error_msg = Column(Text, default="")


class SeenUrl(Base):
    """历史 URL 去重表：记录已精选过的链接，避免跨天重复"""
    __tablename__ = "seen_urls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(1024), unique=True, nullable=False)
    first_seen = Column(DateTime, default=datetime.now)


# ==================== v2 迁移与 FTS ====================

def _migrate_top100_columns(conn):
    """为 top100_articles / kb_articles 补充 v2 字段"""
    from sqlalchemy import text
    table_cols = {
        "top100_articles": {
            "lang": "VARCHAR(10) DEFAULT ''",
            "domain": "VARCHAR(20) DEFAULT 'ai_general'",
            "verified": "BOOLEAN DEFAULT 0",
            "md_length": "INTEGER DEFAULT 0",
        },
        "kb_articles": {
            "translated_path": "VARCHAR(1024) DEFAULT ''",
            "domain": "VARCHAR(20) DEFAULT 'ai_general'",
            "lang": "VARCHAR(10) DEFAULT ''",
            "source": "VARCHAR(100) DEFAULT ''",
            "tags": "VARCHAR(500) DEFAULT ''",
        },
        "refresh_logs": {
            "verified_count": "INTEGER DEFAULT 0",
            "en_count": "INTEGER DEFAULT 0",
            "cn_count": "INTEGER DEFAULT 0",
            "audit_count": "INTEGER DEFAULT 0",
            "general_count": "INTEGER DEFAULT 0",
            "shortfall": "INTEGER DEFAULT 0",
        },
    }
    for table, cols in table_cols.items():
        existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()}
        for col, ddl in cols.items():
            if col not in existing:
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))
                except Exception:
                    pass
    conn.commit()


def _ensure_fts(conn):
    """创建知识库 FTS5 索引（title + content，附过滤字段）"""
    import sqlite3
    from config import DATA_DIR
    c = sqlite3.connect(DATA_DIR / "xmarkdown.db")
    try:
        row = c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='kb_fts'").fetchone()
        if row and "content='" in (row[0] or ""):
            # 旧版 contentless schema：重建并回填索引
            c.execute("DROP TABLE kb_fts")
            c.execute(
                """
                CREATE VIRTUAL TABLE kb_fts USING fts5(
                    title,
                    content,
                    domain,
                    lang,
                    category,
                    source,
                    saved_at
                );
                """
            )
            c.commit()
            c.close()
            fts_reindex_all()
            return
        c.executescript(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS kb_fts USING fts5(
                title,
                content,
                domain,
                lang,
                category,
                source,
                saved_at
            );
            """
        )
        c.commit()
    finally:
        c.close()


def init_db():
    """创建所有表并执行 v2 迁移"""
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        _migrate_top100_columns(conn)
        _ensure_fts(conn)


# ==================== FTS 索引读写（知识库）====================

def _sqlite_conn():
    import sqlite3
    from config import DATA_DIR
    conn = sqlite3.connect(DATA_DIR / "xmarkdown.db")
    conn.row_factory = sqlite3.Row
    return conn


def fts_upsert(article_id: int, title: str, content: str, domain: str,
               lang: str, category: str, source: str, saved_at: str):
    """写入/更新单条 FTS 记录"""
    try:
        title_idx = _tokenize(title)
        content_idx = _tokenize(content)
        conn = _sqlite_conn()
        try:
            conn.execute("DELETE FROM kb_fts WHERE rowid = ?", (article_id,))
            conn.execute(
                "INSERT INTO kb_fts(rowid, title, content, domain, lang, category, source, saved_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (article_id, title_idx, content_idx, domain, lang, category, source, saved_at),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        print(f"  [FTS] 索引失败 id={article_id}: {e}")


def fts_delete(article_id: int):
    try:
        conn = _sqlite_conn()
        try:
            conn.execute("DELETE FROM kb_fts WHERE rowid = ?", (article_id,))
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def fts_reindex_all():
    """根据 kb_articles 表重建 FTS 索引"""
    db = SessionLocal()
    try:
        conn = _sqlite_conn()
        try:
            conn.execute("DELETE FROM kb_fts")
            rows = db.query(KnowledgeBaseArticle).all()
            for a in rows:
                content = f"{a.original_md or ''}\n\n{a.translated_md or ''}"
                title_idx = _tokenize(a.title)
                content_idx = _tokenize(content)
                conn.execute(
                    "INSERT INTO kb_fts(rowid, title, content, domain, lang, category, source, saved_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (a.id, title_idx, content_idx, a.domain, a.lang, a.category, a.source,
                     a.saved_at.isoformat() if a.saved_at else ""),
                )
            conn.commit()
            return len(rows)
        finally:
            conn.close()
    finally:
        db.close()


def fts_search(query: str, domain: str = "", lang: str = "",
               category: str = "", limit: int = 10) -> list[dict]:
    """BM25 全文检索（jieba 分词，词间默认 AND）"""
    tokens = _tokenize(query).split()
    if not tokens:
        tokens = [query]
    match_expr = " AND ".join(f'"{t}"' for t in tokens[:8])
    filters = []
    if domain:
        filters.append("domain = :domain")
    if lang:
        filters.append("lang = :lang")
    if category:
        filters.append("category = :category")
    where = f"WHERE kb_fts MATCH :match"
    if filters:
        where += " AND " + " AND ".join(filters)

    sql = (
        f"SELECT rowid, title, domain, lang, category, source, saved_at, "
        f"bm25(kb_fts) AS score, snippet(kb_fts, 1, '[', ']', '…', 24) AS snippet "
        f"FROM kb_fts {where} ORDER BY score LIMIT :limit"
    )
    params = {"match": match_expr, "limit": int(limit)}
    if domain:
        params["domain"] = domain
    if lang:
        params["lang"] = lang
    if category:
        params["category"] = category
    try:
        conn = _sqlite_conn()
        try:
            rows = conn.execute(sql, params).fetchall()
            return [
                {
                    "id": r["rowid"],
                    "title": r["title"],
                    "domain": r["domain"],
                    "lang": r["lang"],
                    "category": r["category"],
                    "source": r["source"],
                    "saved_at": r["saved_at"],
                    "score": round(-(r["score"] or 0), 4),
                    "snippet": r["snippet"] or "",
                }
                for r in rows
            ]
        finally:
            conn.close()
    except Exception as e:
        print(f"  [FTS] 检索失败: {e}")
        return []


def _tokenize(text: str) -> str:
    """jieba 分词（空格连接），供 FTS5 unicode61 索引使用"""
    if not text:
        return ""
    try:
        import jieba
        return " ".join(
            t for t in jieba.cut_for_search(text)
            if t.strip() and t.strip() not in "，。！？、；：\"'()[]{}《》【】\n\t "
        )
    except Exception:
        return text


def _normalize_text(text: str) -> str:
    """归一化：小写 + 去除空白/标点/连接符，用于模糊匹配"""
    if not text:
        return ""
    import re
    return re.sub(
        r"[\s\-_·.,，。！？、；：\"'()（）\[\]{}《》【】/\\:·+]+",
        "",
        text.lower(),
    )


def _is_subsequence(q: str, text: str) -> bool:
    """子序列匹配：q 的每个字符按顺序出现在 text 中（容忍漏字/错字）"""
    if not q:
        return True
    it = iter(text)
    return all(ch in it for ch in q)


def _make_snippet(md: str, q: str, window: int = 48) -> str:
    """在正文中定位查询串，返回带上下文的高亮片段"""
    if not md:
        return ""
    lower_md = md.lower()
    pos = -1
    # 先找完整查询串，再按字符片段找第一个命中
    if q:
        pos = lower_md.find(q)
    if pos < 0 and q:
        ch = q[0]
        if ch:
            pos = lower_md.find(ch)
    if pos < 0:
        text = md.strip().replace("\n", " ")
        return text[: window * 2] if text else ""
    start = max(0, pos - window)
    end = min(len(md), pos + len(q) + window)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(md) else ""
    return f"{prefix}{md[start:end].strip()}{suffix}".replace("\n", " ")


def fuzzy_kb_search(
    query: str,
    domain: str = "",
    lang: str = "",
    category: str = "",
    limit: int = 20,
) -> list[dict]:
    """知识库模糊检索：标题/来源子串 + 子序列模糊 + FTS5 全文，合并去重
    返回 [{id, title, path, domain, lang, category, source, snippet, score, matchType}]"""
    q = (query or "").strip()
    if not q:
        return []
    qn = _normalize_text(q)

    db = SessionLocal()
    try:
        articles = db.query(KnowledgeBaseArticle).all()
    finally:
        db.close()

    by_id = {a.id: a for a in articles}

    # 1) 标题 / 来源 / 子序列匹配
    title_hits: list[dict] = []
    for a in articles:
        if domain and a.domain != domain:
            continue
        if lang and a.lang != lang:
            continue
        if category and a.category != category:
            continue
        title_n = _normalize_text(a.title)
        source_n = _normalize_text(a.source)
        score = 0
        matched = ""
        if qn and title_n and qn in title_n:
            score = 100 + min(9.0, len(qn) / max(len(title_n), 1) * 10)
            matched = "title"
        elif qn and source_n and qn in source_n:
            score = 80 + min(9.0, len(qn) / max(len(source_n), 1) * 10)
            matched = "source"
        elif qn and title_n and _is_subsequence(qn, title_n):
            ratio = len(qn) / max(len(title_n), 1)
            score = 50 + ratio * 25
            matched = "fuzzy"
        if score > 0:
            title_hits.append({
                "id": a.id,
                "title": a.title or "",
                "path": a.filepath or "",
                "domain": a.domain,
                "lang": a.lang,
                "category": a.category,
                "source": a.source,
                "snippet": _make_snippet(a.original_md or a.translated_md or "", qn),
                "score": round(score, 2),
                "matchType": matched,
            })
    title_hits.sort(key=lambda x: -x["score"])

    # 2) FTS 全文检索（内容命中）
    try:
        content_hits = fts_search(
            q, domain=domain, lang=lang, category=category,
            limit=max(limit * 2, 20),
        )
    except Exception:
        content_hits = []

    merged: dict[int, dict] = {}
    for h in title_hits:
        merged[h["id"]] = h
    for r in content_hits:
        if r["id"] in merged:
            # 已有标题命中则保留更高分；全文命中作为补充片段
            existing = merged[r["id"]]
            if not existing.get("snippet") and r.get("snippet"):
                existing["snippet"] = r["snippet"]
            continue
        rec = by_id.get(r["id"])
        merged[r["id"]] = {
            "id": r["id"],
            "title": r["title"],
            "path": rec.filepath if rec else "",
            "domain": r.get("domain", ""),
            "lang": r.get("lang", ""),
            "category": r.get("category", ""),
            "source": r.get("source", ""),
            "snippet": r.get("snippet", ""),
            "score": r.get("score", 0.0),
            "matchType": "content",
        }

    results = sorted(merged.values(), key=lambda x: -x["score"])[: int(limit)]
    # 补全 path（FTS 命中的记录在循环里已带 path；保险起见再兜底一次）
    for r in results:
        if not r.get("path") and by_id.get(r["id"]):
            r["path"] = by_id[r["id"]].filepath or ""
    return results


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
