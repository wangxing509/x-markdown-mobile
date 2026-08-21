# -*- coding: utf-8 -*-
"""
设置 / 子 Agent / 来源 / LLM 通道 API 端点（v2）
"""
from fastapi import APIRouter, HTTPException
from models import (
    SettingsOut,
    AgentOut,
    SourceOut,
    LlmConfigOut,
)
from settings_store import (
    get_settings,
    save_settings,
    get_agents,
    save_agents,
    get_sources,
    set_source_enabled,
    get_llm_config,
    save_llm_config,
    effective_top_n,
    effective_schedule,
)
from database import SessionLocal, RefreshLog

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/settings", response_model=SettingsOut)
def read_settings():
    s = get_settings()
    return SettingsOut(
        top_n=effective_top_n(),
        en_ratio=float(s.get("en_ratio", 0.4)),
        audit_ratio=float(s.get("audit_ratio", 0.25)),
        schedule=effective_schedule(),
    )


@router.post("/settings", response_model=SettingsOut)
def write_settings(payload: dict):
    """保存设置；top_n 自动 clamp 到 [30,50]；调度变更立即生效"""
    from config import TOP_N_MIN, TOP_N_MAX
    s = get_settings()
    if "top_n" in payload:
        s["top_n"] = max(TOP_N_MIN, min(TOP_N_MAX, int(payload["top_n"])))
    if "en_ratio" in payload:
        s["en_ratio"] = max(0.2, min(0.8, float(payload["en_ratio"])))
    if "audit_ratio" in payload:
        s["audit_ratio"] = max(0.15, min(0.45, float(payload["audit_ratio"])))
    if isinstance(payload.get("schedule"), dict):
        sched = s.get("schedule") or {}
        sched.update(payload["schedule"])
        s["schedule"] = sched
    save_settings(s)
    try:
        from scheduler import reschedule
        reschedule()
    except Exception as e:
        print(f"  [设置] 重新调度失败: {e}")
    return read_settings()


@router.get("/agents", response_model=list[AgentOut])
def read_agents():
    return [AgentOut(**a) for a in get_agents()]


@router.post("/agents", response_model=list[AgentOut])
def write_agents(payload: list[dict]):
    agents = save_agents(payload)
    return [AgentOut(**a) for a in agents]


@router.get("/sources", response_model=list[SourceOut])
def read_sources():
    return [SourceOut(**s) for s in get_sources()]


@router.post("/sources/toggle")
def toggle_source(payload: dict):
    name = payload.get("name", "")
    enabled = bool(payload.get("enabled", False))
    if not name:
        raise HTTPException(status_code=400, detail="缺少来源名称")
    sources = set_source_enabled(name, enabled)
    return {"success": True, "sources": [SourceOut(**s) for s in sources]}


@router.get("/llm-config", response_model=LlmConfigOut)
def read_llm_config():
    return LlmConfigOut(**get_llm_config())


@router.post("/llm-config", response_model=LlmConfigOut)
def write_llm_config(payload: dict):
    cfg = save_llm_config(payload)
    return LlmConfigOut(**cfg)


@router.get("/refresh-logs")
def refresh_logs(limit: int = 10):
    """最近刷新日志（含各阶段计数）"""
    db = SessionLocal()
    try:
        logs = db.query(RefreshLog).order_by(RefreshLog.id.desc()).limit(limit).all()
        return {
            "logs": [
                {
                    "id": l.id,
                    "startedAt": l.started_at.isoformat() if l.started_at else None,
                    "finishedAt": l.finished_at.isoformat() if l.finished_at else None,
                    "status": l.status,
                    "raw": l.raw_count,
                    "dedup": l.dedup_count,
                    "verified": l.verified_count,
                    "curated": l.curated_count,
                    "en": l.en_count,
                    "cn": l.cn_count,
                    "audit": l.audit_count,
                    "general": l.general_count,
                    "shortfall": l.shortfall,
                    "error": l.error_msg,
                }
                for l in logs
            ]
        }
    finally:
        db.close()
