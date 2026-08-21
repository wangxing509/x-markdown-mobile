# -*- coding: utf-8 -*-
"""
X markdown 后端入口（v2）
FastAPI 应用主文件
"""
import sys
import io
import threading
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import (
    init_db,
    SessionLocal,
    Top100Article,
    RefreshLog,
    SeenUrl,
    KnowledgeBaseArticle,
)
from processor.dedup import deduplicate
from processor.classifier import classify_batch, extract_tags
from processor.scorer import rank_and_score
from processor.language import detect_lang
from processor.domain import classify_domain
from processor.quota import select_with_quotas
from processor.verify import enrich_and_verify
from crawler.engine import CrawlerEngine
from scheduler import start_scheduler, stop_scheduler
from settings_store import effective_top_n, effective_schedule

from api.top100 import router as top100_router
from api.markdown import router as markdown_router
from api.translate import router as translate_router
from api.distill import router as distill_router
from api.knowledge import router as knowledge_router
from api.chat import router as chat_router
from api.settings import router as settings_router
from api.brightdata import router as brightdata_router
from api.zhihu import router as zhihu_router
from api.sync_site import router as sync_site_router


# ==================== 刷新流水线（v2） ====================

def _dedup_against_history(articles: list[dict]) -> list[dict]:
    """剔除已保存知识库或当天已精选过的 URL（跨天自动解禁，避免占满新闻位）"""
    db = SessionLocal()
    try:
        kb_urls = {
            r[0]
            for r in db.query(KnowledgeBaseArticle.source_url)
            .filter(KnowledgeBaseArticle.source_url != "")
            .all()
        }
        cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        seen_urls = {
            r[0]
            for r in db.query(SeenUrl.url).filter(SeenUrl.first_seen >= cutoff).all()
        }
        kept = [a for a in articles if a.get("url") not in kb_urls and a.get("url") not in seen_urls]
        dropped = len(articles) - len(kept)
        if dropped:
            print(f"  [历史去重] 剔除 {dropped} 条（已在知识库或今天精选过）")
        return kept
    finally:
        db.close()


def _enrich_with_expansion(articles: list[dict], target: int) -> list[dict]:
    """富集+验证；验证不足时扩选候选（最多 2 倍）"""
    from config import (
        ENRICH_CANDIDATE_MULTIPLIER,
        ENRICH_MIN_POOL,
        ENRICH_MAX_RETRY_MULTIPLIER,
    )
    pool = max(target * ENRICH_CANDIDATE_MULTIPLIER, ENRICH_MIN_POOL)
    pool = min(pool, len(articles))
    verified = enrich_and_verify(articles[:pool])
    max_pool = min(len(articles), pool * ENRICH_MAX_RETRY_MULTIPLIER)
    if len(verified) < target and max_pool > pool:
        print(f"  [验证] 通过 {len(verified)} < 目标 {target}，扩选候选到 {max_pool}")
        verified = enrich_and_verify(articles[:max_pool])
    return verified


def _write_refresh_log(stats: dict, status: str, error: str = ""):
    """写入刷新日志（手动/定时统一记录）"""
    db = SessionLocal()
    try:
        log = RefreshLog(
            started_at=stats.get("started_at") or datetime.now(),
            finished_at=datetime.now(),
            status=status,
            raw_count=stats.get("raw", 0),
            dedup_count=stats.get("dedup", 0),
            verified_count=stats.get("verified", 0),
            curated_count=stats.get("curated", 0),
            en_count=stats.get("en", 0),
            cn_count=stats.get("cn", 0),
            audit_count=stats.get("audit", 0),
            general_count=stats.get("general", 0),
            shortfall=stats.get("shortfall", 0),
            error_msg=error or (stats.get("source_failures") and "；".join(stats["source_failures"][:8]) or ""),
        )
        db.add(log)
        db.commit()
        return log.id
    finally:
        db.close()


def refresh_pipeline() -> dict:
    """全量刷新流水线（v2）：爬取 → 去重 → 分类/领域/语言 → 评分 → 富集验证 → 配额入库
    成功/失败都会写 RefreshLog。"""
    stats: dict = {"started_at": datetime.now()}
    print(f"\n{'='*60}")
    print(f"  [流水线 v2] 开始执行 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"{'='*60}")
    try:
        target = effective_top_n()
        print(f"  [目标] 每日 {target} 条（30-50），英文40%，审计×AI 20-30%")

        # Step 1: 爬取
        print("\n[1/7] 多源爬取（RSS + 官方社区 + 审计源）...")
        engine = CrawlerEngine().register_all()
        articles = engine.run_with_fallback()
        raw_count = len(articles)
        print(f"  -> 爬取原始: {raw_count} 条")
        failures = getattr(engine, "failures", [])
        if failures:
            print(f"  [源失败] {len(failures)} 个来源无产出: {'; '.join(failures[:8])}")

        # Step 2: 去重（批内三重去重 + 知识库/历史 URL 去重）
        print("\n[2/7] 去重（SimHash + URL + 标题 + 知识库/历史）...")
        articles = deduplicate(articles)
        articles = _dedup_against_history(articles)
        dedup_count = len(articles)

        # Step 3: 分类 + 领域 + 语言（逐篇）
        print("\n[3/7] 分类（article/tutorial/application）+ 领域（AI×审计）+ 语言判定...")
        articles = classify_batch(articles)
        kept = []
        for a in articles:
            a["domain"] = classify_domain(a)
            if not a.get("domain"):
                continue
            a["lang"] = detect_lang(a)
            kept.append(a)
        articles = kept
        print(f"  -> 领域过滤后: {len(articles)} 条")

        # Step 4: 预评分
        print("\n[4/7] 综合评分（时效/权威/热度/TF-IDF/互动）...")
        articles = rank_and_score(articles)

        # Step 5: 正文富集 + 验证
        print(f"\n[5/7] 正文富集与验证（≥500字符、无失败标记）...")
        verified = _enrich_with_expansion(articles, target)

        # Step 6: 二维配额选择
        print("\n[6/7] 配额选择（领域×语言、单源上限、分类软配额）...")
        selected, sel_stats = select_with_quotas(verified, target)
        print(f"  -> 入选 {sel_stats['total']} 条，EN {sel_stats['en']}/CN {sel_stats['cn']}，审计 {sel_stats['audit']} 条，缺额 {sel_stats['shortfall']}")
        stats.update(sel_stats)

        # Step 7: 入库 + 记录历史 URL
        print("\n[7/7] 精选入库...")
        db = SessionLocal()
        cat_dist = {}
        curated_count = 0
        try:
            db.query(Top100Article).delete()
            now = datetime.now()
            for rank, a in enumerate(selected, 1):
                tags = extract_tags(a.get("raw_text", "") or a.get("summary", ""))
                published = a.get("published_at")
                if isinstance(published, str):
                    try:
                        published = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    except Exception:
                        published = now
                article = Top100Article(
                    title=a["title"],
                    url=a["url"],
                    summary=a.get("summary", ""),
                    source=a.get("source", ""),
                    source_authority=a.get("source_authority", 0.5),
                    published_at=published or now,
                    raw_text=a.get("raw_text", ""),
                    simhash_value=a.get("simhash_value", ""),
                    category=a.get("category", "article"),
                    score=a.get("score", 0.0),
                    rank=rank,
                    tags=",".join(tags),
                    likes=a.get("likes", 0),
                    comments=a.get("comments", 0),
                    author=a.get("author", ""),
                    author_followers=a.get("author_followers", 0),
                    curated_at=now,
                    lang=a.get("lang", ""),
                    domain=a.get("domain", "ai_general"),
                    verified=bool(a.get("verified")),
                    md_length=int(a.get("md_length", 0) or 0),
                )
                db.add(article)
                if not db.query(SeenUrl).filter(SeenUrl.url == a["url"]).first():
                    db.add(SeenUrl(url=a["url"], first_seen=now))
                curated_count += 1

            db.commit()
            print(f"  -> 精选入库: {curated_count} 条")
            for a in selected:
                c = a.get("category", "article")
                cat_dist[c] = cat_dist.get(c, 0) + 1
            print(f"  -> 分类分布: {cat_dist}")
        except Exception as e:
            db.rollback()
            print(f"  [错误] 入库失败: {e}")
            raise
        finally:
            db.close()

        stats.update({
            "raw": raw_count,
            "dedup": dedup_count,
            "verified": len(verified),
            "curated": curated_count,
            "category": cat_dist,
            "target": target,
            "source_failures": failures,
        })
        _write_refresh_log(stats, "success")
        print(f"\n  [完成] 流水线 v2 执行完毕")
        return stats
    except Exception as e:
        stats["error"] = str(e)[:500]
        _write_refresh_log(stats, "failed", str(e)[:500])
        raise


def scheduled_refresh():
    """定时刷新入口（在独立线程中运行）"""
    def _run():
        try:
            stats = refresh_pipeline()
            print(f"  [定时] 刷新成功: {stats}")
        except Exception as e:
            print(f"  [定时] 刷新失败: {e}")

    threading.Thread(target=_run, daemon=True).start()


# ==================== 应用生命周期 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的生命周期管理"""
    # UTF-8 编码兼容
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("=" * 60)
    print("  X markdown v2 后端启动中 ...")
    print("=" * 60)

    # 初始化数据库（含 v2 迁移与 FTS）
    print("\n[启动] 初始化数据库（迁移 + FTS5）...")
    init_db()

    # 检查是否已有数据
    db = SessionLocal()
    try:
        existing = db.query(Top100Article).count()
        if existing == 0:
            print(f"[启动] 数据库为空，执行首次数据刷新...")
            threading.Thread(target=refresh_pipeline, daemon=True).start()
        else:
            print(f"[启动] 数据库已有 {existing} 条精选文章")
    finally:
        db.close()

    # 启动定时调度
    sched = effective_schedule()
    print(f"[启动] 注册定时任务（{sched.get('enabled')}, {sched.get('hour')}:{sched.get('minute')}）...")
    start_scheduler(scheduled_refresh)

    print(f"\n  [就绪] 服务已启动: http://127.0.0.1:8765")
    print(f"  [文档] API 文档: http://127.0.0.1:8765/docs")
    print("=" * 60)

    yield

    # 关闭
    print("\n[关闭] 停止调度器 ...")
    stop_scheduler()


# ==================== 创建应用 ====================

app = FastAPI(
    title="X markdown v2 API",
    description="AI×审计 内容聚合与 Markdown 工具后端",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(top100_router)
app.include_router(markdown_router)
app.include_router(translate_router)
app.include_router(distill_router)
app.include_router(knowledge_router)
app.include_router(chat_router)
app.include_router(settings_router)
app.include_router(brightdata_router)
app.include_router(zhihu_router)
app.include_router(sync_site_router)


@app.get("/")
def root():
    return {
        "name": "X markdown v2 API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0", "timestamp": datetime.now().isoformat()}


# ==================== 代理配置 ====================

@app.get("/api/proxy")
def get_proxy():
    """读取当前代理配置（界面与本地文件共享）"""
    try:
        from config import PROXY_CONFIG_PATH
        import json
        if PROXY_CONFIG_PATH.exists():
            with open(PROXY_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "enabled": bool(data.get("enabled", False)),
                "url": data.get("url", "") or "",
            }
    except Exception:
        pass
    return {"enabled": False, "url": ""}


@app.post("/api/proxy")
def set_proxy(payload: dict):
    """保存代理配置到本地文件（同时刷新当前进程运行的 HTTP_PROXY）"""
    import json
    from config import PROXY_CONFIG_PATH, _normalize_proxy

    enabled = bool(payload.get("enabled", False))
    url = _normalize_proxy(payload.get("url", "") or "")

    PROXY_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROXY_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"enabled": enabled, "url": url}, f, ensure_ascii=False, indent=2)

    # 运行时刷新（后续刷新流水线立即生效）
    import config
    config.HTTP_PROXY = url if enabled else ""
    return {"success": True, "enabled": enabled, "url": url}


# ==================== 直接运行 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8765, reload=False)
