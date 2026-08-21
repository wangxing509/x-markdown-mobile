# -*- coding: utf-8 -*-
"""
知识库 API 端点（v2）：列表 / 保存（原文+译文）/ 删除 / 检索 / 重建索引
"""
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from models import (
    KbListResponse,
    KbItemOut,
    KbSaveRequest,
    KbSaveResponse,
    KbSearchResponse,
    KbSearchResult,
    KbTreeResponse,
)
from config import KB_DIR
from database import (
    SessionLocal,
    KnowledgeBaseArticle,
    fts_reindex_all,
    fuzzy_kb_search,
)
from kb_service import save_to_kb, delete_kb
from kb_index import build_kb_tree, ensure_kb_index

router = APIRouter(prefix="/api/kb", tags=["knowledge"])


class KbDeleteRequest(BaseModel):
    """删除知识库请求（id 或路径至少传一种）"""
    ids: List[int] = []
    paths: List[str] = []


@router.get("", response_model=KbListResponse)
def list_knowledge_base():
    """列出知识库文章（文件 + 数据库元数据）"""
    KB_DIR.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        meta = {a.filepath: a for a in db.query(KnowledgeBaseArticle).all()}
        items = []
        for md_file in KB_DIR.glob("*.md"):
            if md_file.name.startswith("_"):
                continue
            stat = md_file.stat()
            m = meta.get(str(md_file))
            has_translation = False
            if m is not None:
                has_translation = bool(m.translated_path and Path(m.translated_path).exists())
            items.append(KbItemOut(
                name=md_file.stem,
                path=str(md_file),
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                sourceUrl=m.source_url if m else "",
                domain=(m.domain if m else "ai_general"),
                lang=(m.lang if m else ""),
                category=(m.category if m else "article"),
                source=(m.source if m else ""),
                hasTranslation=has_translation,
            ))
        items.sort(key=lambda x: x.modified, reverse=True)
        return KbListResponse(items=items)
    finally:
        db.close()


@router.post("/save", response_model=KbSaveResponse)
def save_kb(req: KbSaveRequest):
    """保存原文（+译文）到知识库：双文件 + DB 元数据 + FTS 索引"""
    try:
        result = save_to_kb(
            url=req.url,
            title=req.title,
            original_md=req.originalMd,
            translated_md=req.translatedMd,
            domain=req.domain,
            category=req.category,
            lang=req.lang,
            source=req.source,
            tags=req.tags,
            force=req.force,
        )
        return KbSaveResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.post("/delete")
def delete_kb_endpoint(req: KbDeleteRequest):
    """删除知识库文章（支持按 id 或文件路径，单个/批量）"""
    if not req.ids and not req.paths:
        raise HTTPException(status_code=400, detail="请提供要删除的文章 id 或路径")
    try:
        return delete_kb(ids=req.ids, paths=req.paths)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/index")
def get_kb_index(force: bool = False):
    """获取精简知识库索引 Markdown（聚合类别 → 主题 → 作者计数）"""
    try:
        return ensure_kb_index(force=force)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"索引获取失败: {str(e)}")


@router.get("/tree", response_model=KbTreeResponse)
def get_kb_tree():
    """获取知识库目录树：聚合类别 → 主题 → 作者 → 文章"""
    try:
        return build_kb_tree()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"目录树获取失败: {str(e)}")


@router.get("/search", response_model=KbSearchResponse)
def search_kb(
    q: str = Query(..., min_length=1),
    domain: str = "",
    lang: str = "",
    category: str = "",
    limit: int = Query(20, ge=1, le=100),
):
    """模糊检索：标题/来源子串 + 子序列模糊 + FTS5 全文（支持领域/语言/分类过滤）"""
    results = fuzzy_kb_search(
        q, domain=domain, lang=lang, category=category, limit=limit
    )
    return KbSearchResponse(results=[KbSearchResult(**r) for r in results])


@router.post("/reindex")
def reindex_kb():
    """重建 FTS 全文索引 + 作者/主题索引"""
    try:
        count = fts_reindex_all()
        index = ensure_kb_index(force=True)
        return {
            "success": True,
            "count": count,
            "indexTotal": index.get("total", 0),
            "indexPath": index.get("path", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重建索引失败: {str(e)}")


# 兼容旧调用：/api/kb 前缀下的简单检索
@router.get("/legacy-search")
def legacy_search_kb(q: str = Query(..., min_length=1)):
    """兼容旧版本串检索调用"""
    return {"results": fts_search(q, limit=10)}
