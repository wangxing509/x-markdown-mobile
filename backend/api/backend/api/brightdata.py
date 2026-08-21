# -*- coding: utf-8 -*-
"""
Bright Data API 端点：配置 / 失败页面列表 / 失败页面重试 / 单页抓取
"""
import re

from fastapi import APIRouter, HTTPException

from brightdata import (
    get_config,
    save_config,
    list_failed_pages,
    mark_failed_retried,
)
from converter.html_to_md import convert_with_brightdata
from database import SessionLocal, Top100Article, KnowledgeBaseArticle

router = APIRouter(prefix="/api/brightdata", tags=["brightdata"])


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"


@router.get("/config")
def read_config():
    cfg = get_config()
    return {
        "enabled": cfg["enabled"],
        "zone": cfg["zone"],
        "hasApiKey": bool(cfg["api_key"]),
        "apiKeyMasked": _mask_key(cfg["api_key"]),
    }


@router.post("/config")
def write_config(payload: dict):
    cfg = save_config(payload or {})
    return {
        "enabled": cfg["enabled"],
        "zone": cfg["zone"],
        "hasApiKey": bool(cfg["api_key"]),
        "apiKeyMasked": _mask_key(cfg["api_key"]),
    }


@router.get("/failed")
def failed_pages():
    items = list_failed_pages()
    return {"items": items, "count": len(items)}


@router.post("/retry")
def retry_failed(payload: dict | None = None):
    """用 Bright Data 重新爬取之前失败的页面；成功后回写 top100 / 知识库记录"""
    payload = payload or {}
    urls = [u for u in (payload.get("urls") or []) if str(u).strip()]
    all_items = list_failed_pages()
    targets = urls or [it.get("url") for it in all_items if it.get("url")]
    if not targets:
        return {"success": True, "results": [], "succeeded": 0, "failed": 0,
                "message": "没有待重试的失败页面"}
    if not get_config()["enabled"]:
        raise HTTPException(status_code=400, detail="Bright Data 未启用或未配置 API Key")

    results = []
    db = SessionLocal()
    try:
        for url in targets:
            ok = False
            title = ""
            error = ""
            try:
                res = convert_with_brightdata(url)
                md = (res or {}).get("markdown") or ""
                if res and len(md.strip()) > 300:
                    ok = True
                    title = res.get("title") or ""
                    body = re.sub(r"\n*---\n> 来源:.*$", "", md, flags=re.DOTALL).strip()
                    # 回写每日精选：验证通过
                    art = db.query(Top100Article).filter(Top100Article.url == url).first()
                    if art:
                        art.raw_text = body
                        art.verified = True
                        art.md_length = len(md)
                        art.title = title or art.title
                    # 回写知识库原文
                    kb = db.query(KnowledgeBaseArticle).filter(
                        KnowledgeBaseArticle.source_url == url
                    ).first()
                    if kb:
                        kb.original_md = md
                    db.commit()
                else:
                    error = "Bright Data 返回内容过短"
            except Exception as e:
                error = str(e)[:200]
            mark_failed_retried(url, ok, error)
            results.append({"url": url, "success": ok, "title": title, "error": error})
    finally:
        db.close()

    succeeded = sum(1 for r in results if r["success"])
    return {
        "success": True,
        "results": results,
        "succeeded": succeeded,
        "failed": len(results) - succeeded,
    }


@router.post("/fetch")
def fetch_one(payload: dict):
    """用 Bright Data 抓取单个 URL 并转 Markdown（用于前端重试按钮）"""
    url = str(payload.get("url") or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="缺少 url")
    if not get_config()["enabled"]:
        raise HTTPException(status_code=400, detail="Bright Data 未启用或未配置 API Key")
    try:
        res = convert_with_brightdata(url)
        if not res:
            raise HTTPException(status_code=502, detail="Bright Data 抓取失败或内容过短")
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bright Data 抓取失败: {str(e)[:200]}")
