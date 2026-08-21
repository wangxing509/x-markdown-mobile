# -*- coding: utf-8 -*-
"""
知识库核心服务：保存 / 删除（供 API 与知乎专栏自动导入共用）
"""
import re
from datetime import datetime
from pathlib import Path

from config import KB_DIR
from database import (
    SessionLocal,
    KnowledgeBaseArticle,
    fts_upsert,
    fts_delete,
)


def _slugify(title: str) -> str:
    """生成安全的文件名片段（保留中文/字母/数字，去掉非法字符）"""
    slug = re.sub(r'[\\/:*?"<>|\s]+', "_", title.strip())
    slug = re.sub(r"[_]{2,}", "_", slug).strip("_")
    return slug[:60] or "article"


def _ensure_source_footer(md: str, url: str) -> str:
    if not url:
        return md
    if f"> 来源: {url}" in md or url in md[-200:]:
        return md
    return f"{md}\n\n---\n> 来源: {url}"


def save_to_kb(
    url: str = "",
    title: str = "",
    original_md: str = "",
    translated_md: str = "",
    domain: str = "ai_general",
    category: str = "article",
    lang: str = "",
    source: str = "",
    tags: list[str] | None = None,
    force: bool = False,
    build_index: bool = True,
) -> dict:
    """保存文章到知识库：双文件 + DB 元数据 + FTS 索引"""
    KB_DIR.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        url = (url or "").strip()
        title = (title or "未命名文章").strip()
        if url:
            existing = db.query(KnowledgeBaseArticle).filter(
                KnowledgeBaseArticle.source_url == url
            ).first()
            if existing and not force:
                return {
                    "success": False,
                    "duplicate": True,
                    "id": existing.id,
                    "originalPath": existing.filepath,
                    "translatedPath": existing.translated_path or "",
                    "message": f"该链接已存在知识库：{existing.title}",
                }

        date_prefix = datetime.now().strftime("%Y%m%d")
        slug = _slugify(title)
        original_path = KB_DIR / f"{date_prefix}_{slug}_原文.md"
        translated_path = KB_DIR / f"{date_prefix}_{slug}_译文.md"

        original_md = _ensure_source_footer(original_md, url)
        original_path.write_text(original_md, encoding="utf-8")

        translated_md_text = ""
        if translated_md and translated_md.strip():
            translated_md_text = _ensure_source_footer(translated_md, url)
            translated_path.write_text(translated_md_text, encoding="utf-8")

        lang = lang or ("cn" if re.search(r"[\u4e00-\u9fff]", title) else "en")
        domain = domain if domain in ("ai_audit", "ai_general") else "ai_general"

        if existing and force:
            article = existing
        else:
            article = KnowledgeBaseArticle(title=title, filepath=str(original_path))
            db.add(article)
            db.flush()

        article.title = title
        article.filepath = str(original_path)
        article.translated_path = str(translated_path) if translated_md_text else ""
        article.source_url = url
        article.original_md = original_md
        article.translated_md = translated_md_text
        article.category = category or "article"
        article.domain = domain
        article.lang = lang
        article.source = source or ""
        article.tags = ",".join(tags or [])
        article.saved_at = datetime.now()
        db.commit()

        content = f"{original_md}\n\n{translated_md_text}"
        fts_upsert(
            article.id,
            title,
            content,
            domain,
            lang,
            article.category,
            article.source,
            article.saved_at.isoformat(),
        )

        if build_index:
            try:
                from kb_index import ensure_kb_index
                ensure_kb_index(force=True)
            except Exception:
                pass

        return {
            "success": True,
            "duplicate": False,
            "id": article.id,
            "originalPath": str(original_path),
            "translatedPath": str(translated_path) if translated_md_text else "",
            "message": "已保存到知识库",
        }
    finally:
        db.close()


def delete_kb(ids: list[int] | None = None, paths: list[str] | None = None) -> dict:
    """按 id 或文件路径删除知识库文章（DB + FTS + 原文/译文文件）"""
    from sqlalchemy import or_

    KB_DIR.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    deleted = 0
    try:
        records: dict[int, KnowledgeBaseArticle] = {}

        if ids:
            for a in db.query(KnowledgeBaseArticle).filter(
                KnowledgeBaseArticle.id.in_(ids)
            ).all():
                records[a.id] = a

        if paths:
            path_list = [p for p in (paths or []) if p and p.strip()]
            if path_list:
                for a in db.query(KnowledgeBaseArticle).filter(or_(
                    KnowledgeBaseArticle.filepath.in_(path_list),
                    KnowledgeBaseArticle.translated_path.in_(path_list),
                )).all():
                    records[a.id] = a

        removed_paths: set[str] = set()
        for a in records.values():
            for p in (a.filepath, a.translated_path):
                if p:
                    removed_paths.add(p)
                    try:
                        fp = Path(p)
                        if fp.exists():
                            fp.unlink()
                    except Exception:
                        pass
            fts_delete(a.id)
            db.delete(a)
            deleted += 1

        # 清理未登记在 DB 但文件仍存在的路径（按路径删除时）
        if paths:
            for p in paths:
                if not p or p in removed_paths:
                    continue
                try:
                    fp = Path(p)
                    if fp.exists() and str(fp).startswith(str(KB_DIR)):
                        fp.unlink()
                        deleted += 1
                except Exception:
                    pass

        db.commit()
        try:
            from kb_index import ensure_kb_index
            ensure_kb_index(force=True)
        except Exception:
            pass
        return {"success": True, "deleted": deleted}
    finally:
        db.close()
