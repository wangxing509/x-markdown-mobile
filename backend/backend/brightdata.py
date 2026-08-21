# -*- coding: utf-8 -*-
"""
Bright Data Web Unlocker 兜底抓取模块

当普通 HTTP 抓取失败（403/429/内容过短/JS 渲染等）时，通过 Bright Data
Unlocker API 重新抓取页面；同时记录失败页面，支持后续批量重试。

API Key 解析优先级：
  1) ~/.xmarkdown/brightdata.json  (界面可配置)
  2) 环境变量 BRIGHTDATA_API_KEY
  3) Bright Data CLI 登录凭证 %APPDATA%/brightdata-cli/credentials.json
  4) Codex MCP 配置 ~/.codex/mcp.json 中 bright-data.API_TOKEN
"""
import json
import os
import threading
from datetime import datetime

import httpx

from config import (
    BRIGHTDATA_CONFIG_PATH,
    FAILED_PAGES_PATH,
    HEADERS,
    HTTP_PROXY,
)

DEFAULT_ZONE = "cli_unlocker"
API_ENDPOINT = "https://api.brightdata.com/request"

_lock = threading.Lock()


def _read_json(path, default=None):
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def _discover_key_from_cli() -> str:
    """从 Bright Data CLI 登录凭证读取 API Key"""
    try:
        base = os.environ.get("APPDATA")
        if base:
            p = os.path.join(base, "brightdata-cli", "credentials.json")
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for k in ("api_key", "apiKey", "token", "key"):
                    if data.get(k):
                        return str(data[k]).strip()
    except Exception:
        pass
    return ""


def _discover_key_from_codex_mcp() -> str:
    """从 Codex MCP 配置读取 API Token（bright-data 服务器的 API_TOKEN）"""
    try:
        p = os.path.join(os.path.expanduser("~"), ".codex", "mcp.json")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            srv = (data.get("mcpServers") or {}).get("bright-data") or {}
            return str((srv.get("env") or {}).get("API_TOKEN") or "").strip()
    except Exception:
        pass
    return ""


def get_config() -> dict:
    """返回 Bright Data 配置：enabled / api_key / zone"""
    cfg = _read_json(BRIGHTDATA_CONFIG_PATH, {}) or {}
    api_key = str(cfg.get("api_key") or "").strip()
    if not api_key:
        api_key = os.environ.get("BRIGHTDATA_API_KEY", "").strip()
    if not api_key:
        api_key = _discover_key_from_cli()
    if not api_key:
        api_key = _discover_key_from_codex_mcp()
    zone = str(cfg.get("zone") or DEFAULT_ZONE).strip() or DEFAULT_ZONE
    enabled = bool(cfg.get("enabled", True)) and bool(api_key)
    return {"enabled": enabled, "api_key": api_key, "zone": zone}


def save_config(payload: dict) -> dict:
    """保存 Bright Data 配置（界面设置入口）"""
    cfg = _read_json(BRIGHTDATA_CONFIG_PATH, {}) or {}
    if "enabled" in payload:
        cfg["enabled"] = bool(payload["enabled"])
    if payload.get("apiKey"):
        cfg["api_key"] = str(payload["apiKey"]).strip()
    if payload.get("zone"):
        cfg["zone"] = str(payload["zone"]).strip()
    _write_json(BRIGHTDATA_CONFIG_PATH, cfg)
    return get_config()


def is_enabled() -> bool:
    return get_config()["enabled"]


def fetch_html(url: str, timeout: float = 90.0) -> str | None:
    """通过 Bright Data Web Unlocker 抓取页面原始 HTML；失败返回 None"""
    cfg = get_config()
    if not cfg["enabled"]:
        return None
    payload = {"zone": cfg["zone"], "url": url, "format": "raw"}
    try:
        client = httpx.Client(
            headers={**HEADERS, "Authorization": f"Bearer {cfg['api_key']}"},
            timeout=httpx.Timeout(timeout, connect=10),
            follow_redirects=True,
            proxy=HTTP_PROXY if HTTP_PROXY else None,
        )
        resp = client.post(API_ENDPOINT, json=payload)
        client.close()
        if resp.status_code == 200 and resp.text and len(resp.text) > 200:
            return resp.text
        print(f"  [BrightData] HTTP {resp.status_code} for {url}: {resp.text[:200]}")
    except Exception as e:
        print(f"  [BrightData] fetch failed {url}: {e}")
    return None


# ==================== 失败页面记录与重试 ====================

def list_failed_pages() -> list[dict]:
    return _read_json(FAILED_PAGES_PATH, []) or []


def record_failed_page(url: str, title: str = "", source: str = "", error: str = ""):
    """记录一条抓取失败的页面（已存在则更新时间）"""
    if not url:
        return
    with _lock:
        data = _read_json(FAILED_PAGES_PATH, []) or []
    now = datetime.now().isoformat()
    for item in data:
        if item.get("url") == url:
            item["title"] = title or item.get("title", "")
            item["source"] = source or item.get("source", "")
            item["last_error"] = error or item.get("last_error", "")
            item["first_failed_at"] = item.get("first_failed_at") or now
            item["retried"] = False
            item.pop("last_success_at", None)
            break
    else:
        data.append({
            "url": url,
            "title": title,
            "source": source,
            "first_failed_at": now,
            "last_error": error,
            "retried": False,
        })
    with _lock:
        _write_json(FAILED_PAGES_PATH, data)


def mark_failed_retried(url: str, success: bool, error: str = ""):
    """更新失败页面的重试状态"""
    with _lock:
        data = _read_json(FAILED_PAGES_PATH, []) or []
    now = datetime.now().isoformat()
    for item in data:
        if item.get("url") == url:
            item["retried"] = True
            item["last_retry_at"] = now
            if success:
                item["last_success_at"] = now
                item["last_error"] = ""
            elif error:
                item["last_error"] = error
            break
    with _lock:
        _write_json(FAILED_PAGES_PATH, data)
