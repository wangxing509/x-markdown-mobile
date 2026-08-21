# -*- coding: utf-8 -*-
"""
用户可配置存储：settings.json / sources.json / agents.json / llm.json
所有文件位于 ~/.xmarkdown/，首次使用写入代码默认值，之后以用户文件为准。
"""
import json
import threading
from typing import Any

from config import (
    SETTINGS_PATH,
    SOURCES_PATH,
    AGENTS_PATH,
    LLM_CONFIG_PATH,
    TOP_N,
    EN_RATIO,
    AUDIT_TARGET_RATIO,
    SCHEDULE_HOUR,
    SCHEDULE_MINUTE,
    SOURCE_AUTHORITY,
    SOURCE_LANG,
)

_lock = threading.Lock()


def _read(path, default):
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


# ==================== 每日目标与调度 ====================

def get_settings() -> dict:
    with _lock:
        data = _read(SETTINGS_PATH, {})
    defaults = {
        "top_n": TOP_N,
        "en_ratio": EN_RATIO,
        "audit_ratio": AUDIT_TARGET_RATIO,
        "schedule": {"enabled": True, "hour": SCHEDULE_HOUR, "minute": SCHEDULE_MINUTE},
    }
    merged = {**defaults, **data}
    merged["schedule"] = {**defaults["schedule"], **(data.get("schedule") or {})}
    return merged


def save_settings(settings: dict) -> dict:
    with _lock:
        _write(SETTINGS_PATH, settings)
    return get_settings()


def effective_top_n() -> int:
    from config import TOP_N_MIN, TOP_N_MAX
    n = int(get_settings().get("top_n", TOP_N))
    return max(TOP_N_MIN, min(TOP_N_MAX, n))


def effective_schedule() -> dict:
    s = get_settings().get("schedule", {})
    return {
        "enabled": bool(s.get("enabled", True)),
        "hour": int(s.get("hour", SCHEDULE_HOUR)),
        "minute": int(s.get("minute", SCHEDULE_MINUTE)),
    }


# ==================== 来源清单 ====================

def default_sources() -> list[dict]:
    """默认来源清单（可被 sources.json 覆盖）。kind: rss / html / api"""
    return [
        # ---- 中文 AI 资讯 ----
        {"name": "WaytoAGI", "enabled": True, "kind": "html", "authority": SOURCE_AUTHORITY.get("WaytoAGI", 0.9), "lang": "cn"},
        {"name": "魔搭ModelScope", "enabled": True, "kind": "html", "authority": SOURCE_AUTHORITY.get("魔搭ModelScope", 0.88), "lang": "cn"},
        {"name": "微软AI教育社区", "enabled": True, "kind": "html", "authority": SOURCE_AUTHORITY.get("微软AI教育社区", 0.87), "lang": "cn"},
        {"name": "腾讯CodeBuddy", "enabled": True, "kind": "html", "authority": SOURCE_AUTHORITY.get("腾讯CodeBuddy", 0.86), "lang": "cn"},
        {"name": "DeepSeek", "enabled": True, "kind": "html", "authority": SOURCE_AUTHORITY.get("DeepSeek", 0.9), "lang": "cn"},
        {"name": "字节Trae", "enabled": True, "kind": "html", "authority": SOURCE_AUTHORITY.get("字节Trae", 0.84), "lang": "cn"},
        {"name": "Kimi", "enabled": True, "kind": "html", "authority": SOURCE_AUTHORITY.get("Kimi", 0.85), "lang": "cn"},
        # ---- 中文 AI 资讯（RSS）----
        {"name": "量子位", "enabled": True, "kind": "rss", "authority": 0.86, "lang": "cn",
         "feeds": ["https://www.qbitai.com/feed"]},
        {"name": "InfoQ中文", "enabled": True, "kind": "rss", "authority": 0.86, "lang": "cn",
         "feeds": ["https://www.infoq.cn/feed"]},
        {"name": "钛媒体", "enabled": True, "kind": "rss", "authority": 0.80, "lang": "cn",
         "feeds": ["https://www.tmtpost.com/rss"]},
        # ---- 中文 审计×AI ----
        {"name": "审计署", "enabled": True, "kind": "html", "authority": SOURCE_AUTHORITY.get("审计署", 0.92), "lang": "cn", "audit": True,
         "urls": ["https://www.audit.gov.cn/n5/n26/index.html", "https://www.audit.gov.cn/n5/n10002497/index.html"]},
        {"name": "中国内部审计协会", "enabled": True, "kind": "html", "authority": SOURCE_AUTHORITY.get("中国内部审计协会", 0.90), "lang": "cn", "audit": True,
         "urls": ["http://www.ciia.com.cn/xhdt/index.html", "http://www.ciia.com.cn/hydt/index.html"]},
        {"name": "中国注册会计师协会", "enabled": True, "kind": "html", "authority": SOURCE_AUTHORITY.get("中国注册会计师协会", 0.90), "lang": "cn", "audit": True,
         "urls": ["https://www.cicpa.org.cn/news/index.html", "https://www.cicpa.org.cn/industry_research/index.html"]},
        # ---- 英文 AI 资讯（RSS 优先）----
        {"name": "OpenAI Blog", "enabled": False, "kind": "rss", "authority": SOURCE_AUTHORITY.get("OpenAI Blog", 0.97), "lang": "en",
         "feeds": ["https://openai.com/blog/rss.xml"]},
        {"name": "Anthropic News", "enabled": True, "kind": "rss", "authority": SOURCE_AUTHORITY.get("Anthropic News", 0.97), "lang": "en",
         "feeds": ["https://www.anthropic.com/rss.xml"]},
        {"name": "Google AI Blog", "enabled": True, "kind": "rss", "authority": SOURCE_AUTHORITY.get("Google AI Blog", 0.95), "lang": "en",
         "feeds": ["https://blog.google/technology/ai/rss/"]},
        {"name": "Microsoft Research", "enabled": True, "kind": "rss", "authority": SOURCE_AUTHORITY.get("Microsoft Research", 0.95), "lang": "en",
         "feeds": ["https://www.microsoft.com/en-us/research/feed/"]},
        {"name": "VentureBeat AI", "enabled": True, "kind": "rss", "authority": 0.85, "lang": "en",
         "feeds": ["https://venturebeat.com/category/ai/feed/"]},
        {"name": "TechCrunch AI", "enabled": True, "kind": "rss", "authority": 0.85, "lang": "en",
         "feeds": ["https://techcrunch.com/category/artificial-intelligence/feed/"]},
        {"name": "GitHub", "enabled": True, "kind": "html", "authority": SOURCE_AUTHORITY.get("GitHub", 0.95), "lang": "en"},
        {"name": "Reddit", "enabled": True, "kind": "html", "authority": SOURCE_AUTHORITY.get("Reddit", 0.89), "lang": "en"},
        {"name": "Hugging Face", "enabled": True, "kind": "html", "authority": SOURCE_AUTHORITY.get("Hugging Face", 0.88), "lang": "en"},
        # ---- 英文 审计×AI（RSS 优先）----
        {"name": "Journal of Accountancy", "enabled": True, "kind": "rss", "authority": SOURCE_AUTHORITY.get("Journal of Accountancy", 0.93), "lang": "en", "audit": True,
         "feeds": ["https://www.journalofaccountancy.com/news/feed/"]},
        {"name": "IIA Internal Auditor", "enabled": True, "kind": "html", "authority": SOURCE_AUTHORITY.get("IIA Internal Auditor", 0.92), "lang": "en", "audit": True,
         "urls": ["https://internalauditor.org/"]},
        {"name": "ISACA", "enabled": False, "kind": "rss", "authority": SOURCE_AUTHORITY.get("ISACA", 0.91), "lang": "en", "audit": True,
         "feeds": ["https://www.isaca.org/rss/feed/Pages/default.aspx"]},
    ]


def get_sources() -> list[dict]:
    with _lock:
        data = _read(SOURCES_PATH, None)
    defaults = default_sources()
    if not isinstance(data, list):
        # 首次运行：写入默认清单
        with _lock:
            _write(SOURCES_PATH, defaults)
        return defaults

    # 合并：以用户文件为准，但补入代码新增的源
    by_name = {s["name"]: s for s in data}
    for d in defaults:
        if d["name"] not in by_name:
            by_name[d["name"]] = d
    return list(by_name.values())


def set_source_enabled(name: str, enabled: bool) -> list[dict]:
    sources = get_sources()
    for s in sources:
        if s.get("name") == name:
            s["enabled"] = bool(enabled)
    with _lock:
        _write(SOURCES_PATH, sources)
    return sources


# ==================== 子 Agent ====================

def default_agents() -> list[dict]:
    return [
        {
            "id": "general_ai",
            "name": "通用AI资讯助手",
            "desc": "解读 AI 前沿资讯、教程与应用案例，跨语言回答",
            "systemPrompt": "你是 X-markdown 的通用 AI 资讯助手。基于知识库检索到的相关内容，用简洁、专业的中文回答；必要时对比不同来源的观点，并给出对实务工作的启示。回答末尾列出引用的文章。",
            "filters": {"domain": "ai_general"},
            "topK": 5,
            "temperature": 0.3,
        },
        {
            "id": "audit_ai",
            "name": "审计×AI 助手",
            "desc": "聚焦 AI 在审计/内控/合规/风险领域的应用",
            "systemPrompt": "你是 X-markdown 的审计×AI 专家助手。请结合知识库中 AI×审计 相关文章，站在资深审计专家视角解读：该技术如何落地到审计实务（数据审计、智能审计、内控、合规、舞弊识别、风险评估），并指出应用价值、局限与实施要点。回答末尾列出引用的文章。",
            "filters": {"domain": "ai_audit"},
            "topK": 6,
            "temperature": 0.3,
        },
        {
            "id": "kb_search",
            "name": "知识库检索助手",
            "desc": "在全部知识库中检索并摘录相关段落",
            "systemPrompt": "你是 X-markdown 的知识库检索助手。根据用户问题在知识库中检索，优先给出直接相关的原文摘录与出处（文章名+路径），并简要说明相关性；不确定的内容要明确说明。",
            "filters": {},
            "topK": 8,
            "temperature": 0.2,
        },
        {
            "id": "translator",
            "name": "翻译校对助手",
            "desc": "对照原文校对英文译文术语与准确性",
            "systemPrompt": "你是 X-markdown 的翻译校对助手。请对照原文与译文，检查术语准确性（特别是 AI 与审计专业术语）、语句通顺度与 Markdown 结构完整性，逐条列出需要修正之处并给出修正后的中文表达。",
            "filters": {"lang": "en"},
            "topK": 4,
            "temperature": 0.2,
        },
    ]


def get_agents() -> list[dict]:
    with _lock:
        data = _read(AGENTS_PATH, None)
    defaults = default_agents()
    if not isinstance(data, list):
        with _lock:
            _write(AGENTS_PATH, defaults)
        return defaults
    by_id = {a.get("id"): a for a in data}
    for d in defaults:
        if d["id"] not in by_id:
            by_id[d["id"]] = d
    return list(by_id.values())


def save_agents(agents: list[dict]) -> list[dict]:
    with _lock:
        _write(AGENTS_PATH, agents)
    return agents


# ==================== LLM 翻译通道 ====================

def default_llm_config() -> dict:
    return {
        "provider": "local",          # local | api
        "apiBase": "",                # 例如 https://api.deepseek.com/v1
        "apiKey": "",
        "model": "deepseek-chat",
        "temperature": 0.2,
    }


def get_llm_config() -> dict:
    with _lock:
        data = _read(LLM_CONFIG_PATH, {})
    return {**default_llm_config(), **data}


def save_llm_config(cfg: dict) -> dict:
    merged = {**default_llm_config(), **cfg}
    with _lock:
        _write(LLM_CONFIG_PATH, merged)
    return merged


def get_json(path, default: Any):
    return _read(path, default)
