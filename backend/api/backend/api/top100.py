# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
每日精选 API 端点（v2）
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from models import (
    Top100Response,
    Top100ItemOut,
    Top100Stats,
    RefreshResponse,
)
from database import SessionLocal, Top100Article
from settings_store import effective_top_n, effective_schedule

router = APIRouter(prefix="/api", tags=["top100"])


@router.get("/top100", response_model=Top100Response)
def get_top100(
    category: Optional[str] = None,
    domain: Optional[str] = None,
    lang: Optional[str] = None,
    verified_only: bool = False,
):
    """获取每日精选列表（支持 category/domain/lang 筛选）"""
    db = SessionLocal()
    try:
        query = db.query(Top100Article)
        if category:
            query = query.filter(Top100Article.category == category)
        if domain:
            query = query.filter(Top100Article.domain == domain)
        if lang:
            query = query.filter(Top100Article.lang == lang)
        if verified_only:
            query = query.filter(Top100Article.verified.is_(True))
        articles = query.order_by(Top100Article.rank.asc()).all()

        items = [
            Top100ItemOut(
                id=a.id,
                rank=a.rank,
                title=a.title,
                url=a.url,
                summary=a.summary,
                source=a.source,
                sourceAuthority=a.source_authority,
                publishedAt=a.published_at,
                category=a.category,
                score=a.score,
                tags=a.tags,
                likes=a.likes,
                comments=a.comments,
                author=a.author,
                authorFollowers=a.author_followers,
                lang=a.lang or "",
                domain=a.domain or "ai_general",
                verified=bool(a.verified),
                mdLength=a.md_length or 0,
            )
            for a in articles
        ]

        stats = Top100Stats(
            total=len(items),
            target=effective_top_n(),
            cn=sum(1 for i in items if i.lang == "cn"),
            en=sum(1 for i in items if i.lang == "en"),
            audit=sum(1 for i in items if i.domain == "ai_audit"),
            general=sum(1 for i in items if i.domain == "ai_general"),
            shortfall=max(0, effective_top_n() - len(items)),
        )

        sched = effective_schedule()
        next_refresh = f"每日 {sched.get('hour', 9):02d}:{sched.get('minute', 0):02d}" if sched.get("enabled", True) else "定时刷新已关闭"
        return Top100Response(
            updateTime=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            nextRefresh=next_refresh,
            items=items,
            totalCount=len(items),
            stats=stats,
        )
    finally:
        db.close()


@router.post("/refresh", response_model=RefreshResponse)
def refresh_top100():
    """手动刷新每日精选"""
    try:
        from main import refresh_pipeline
        stats = refresh_pipeline()
        return RefreshResponse(
            success=True,
            message=(
                f"刷新成功：原始 {stats.get('raw', 0)} 条，去重后 {stats.get('dedup', 0)} 条，"
                f"验证通过 {stats.get('verified', 0)} 条，精选 {stats.get('curated', 0)} 条"
                f"（EN {stats.get('en', 0)}/CN {stats.get('cn', 0)}，审计 {stats.get('audit', 0)} 条）"
            ),
            rawCount=stats.get("raw"),
            dedupCount=stats.get("dedup"),
            verifiedCount=stats.get("verified"),
            curatedCount=stats.get("curated"),
            enCount=stats.get("en"),
            cnCount=stats.get("cn"),
            auditCount=stats.get("audit"),
            generalCount=stats.get("general"),
            shortfall=stats.get("shortfall"),
            stats=stats,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新失败: {str(e)}")
