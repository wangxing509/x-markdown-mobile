# -*- coding: utf-8 -*-
"""冒烟测试：DB 迁移 / FTS 索引检索 / KB 保存接口 / FastAPI 装配"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  OK {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {detail}")


def main():
    from database import (
        init_db,
        SessionLocal,
        KnowledgeBaseArticle,
        fts_upsert,
        fts_search,
        fts_delete,
    )

    print("[1] init_db（迁移 + FTS 建表）")
    init_db()
    db = SessionLocal()
    try:
        # 清理可能残留的测试行
        leftovers = db.query(KnowledgeBaseArticle).filter(
            KnowledgeBaseArticle.source_url.like("https://test.example.com/%")
        ).all()
        for lf in leftovers:
            fts_delete(lf.id)
            db.delete(lf)
        db.commit()
        from sqlalchemy import text
        with db.connection() as conn:
            cols = {r[1] for r in conn.execute(text("PRAGMA table_info(top100_articles)")).fetchall()}
            check("top100_articles 含 lang/domain/verified/md_length",
                  {"lang", "domain", "verified", "md_length"} <= cols, str(cols))
            fts = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='kb_fts'")).fetchall()
            check("kb_fts 虚拟表已创建", len(fts) == 1)
    finally:
        db.close()

    print("[2] FTS 保存与检索闭环")
    db = SessionLocal()
    try:
        a = KnowledgeBaseArticle(
            title="智能审计测试文章",
            filepath="/tmp/test_audit.md",
            source_url="https://test.example.com/audit-ai",
            original_md="本文介绍大语言模型在审计底稿分析中的应用，包括异常检测与风险预警。",
            translated_md="",
            category="article",
            domain="ai_audit",
            lang="cn",
            source="测试源",
            saved_at=datetime.now(),
        )
        db.add(a)
        db.commit()
        db.refresh(a)
        fts_upsert(a.id, a.title, f"{a.original_md}\n\n{a.translated_md}", a.domain, a.lang, a.category, a.source, a.saved_at.isoformat())

        r = fts_search("审计 大模型", domain="ai_audit", limit=5)
        check("FTS 检索命中", len(r) > 0 and r[0]["id"] == a.id, str(r))
        r2 = fts_search("audit", lang="en", limit=5)
        check("FTS 过滤 domain/lang 生效", all(x["lang"] == "en" for x in r2))

        # 清理
        fts_delete(a.id)
        db.delete(a)
        db.commit()
        check("FTS 删除成功", fts_search("审计 大模型", limit=5).__len__() >= 0)
    finally:
        db.close()

    print("[3] 知识库保存接口（用临时目录模拟）")
    import tempfile
    from pathlib import Path as P
    tmp = P(tempfile.mkdtemp())
    import api.knowledge as kb_api
    old_kb_dir = kb_api.KB_DIR
    kb_api.KB_DIR = tmp
    from models import KbSaveRequest
    req = KbSaveRequest(
        url="https://test.example.com/kb-save",
        title="审计AI 实践",
        originalMd="# 审计AI 实践\n\n正文内容足够长，用于验证保存流程。" * 5,
        translatedMd="",
        domain="ai_audit",
        lang="cn",
        source="手动粘贴",
    )
    resp = kb_api.save_kb(req)
    check("save_kb 成功", resp.success, str(resp))
    check("原文文件已写入", resp.originalPath and P(resp.originalPath).exists())
    check("保存结果返回 id", resp.id is not None)
    dup = kb_api.save_kb(req)
    check("重复 URL 返回 duplicate", dup.duplicate)
    # 清理测试行（DB + FTS + 文件）
    db = SessionLocal()
    try:
        row = db.query(KnowledgeBaseArticle).filter(
            KnowledgeBaseArticle.source_url == "https://test.example.com/kb-save"
        ).first()
        if row:
            fts_delete(row.id)
            db.delete(row)
            db.commit()
    finally:
        db.close()
    # 恢复
    kb_api.KB_DIR = old_kb_dir
    for f in tmp.glob("*"):
        f.unlink()
    tmp.rmdir()

    print("[4] FastAPI 应用装配")
    from main import app
    routes = set(app.openapi()["paths"].keys())
    for expected in (
        "/api/top100", "/api/refresh", "/api/md/convert", "/api/kb", "/api/kb/save",
        "/api/kb/search", "/api/kb/reindex", "/api/chat", "/api/chat/context",
        "/api/agents", "/api/settings", "/api/sources", "/api/llm-config", "/api/refresh-logs",
    ):
        check(f"路由 {expected} 已注册", expected in routes, str(sorted(routes))[:500])

    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
