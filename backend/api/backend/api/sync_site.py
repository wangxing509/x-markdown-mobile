# -*- coding: utf-8 -*-
"""
一键同步手机端（GitHub Pages）接口
==================================
在桌面端 Python 后端中提供 /api/sync/site，触发「导出数据 → 构建站点 → 推送」。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/sync", tags=["sync"])

# 项目根目录 = backend 的上一级
ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "scripts"
MOBILE = ROOT / "xmarkdown-mobile"


@router.get("/site/status")
def sync_status():
    """返回同步所需组件是否可用"""
    def has(cmd):
        try:
            subprocess.run(
                [cmd, "--version"], capture_output=True, timeout=5,
                shell=(cmd in ("npm", "python", "python3")),
            )
            return True
        except Exception:
            return False

    py = "python" if os.name == "nt" else "python3"
    return {
        "root": str(ROOT),
        "mobileDir": str(MOBILE),
        "mobileExists": MOBILE.exists(),
        "python": has(py),
        "npm": has("npm"),
        "git": has("git"),
        "exportScript": (SCRIPTS / "sync.mjs").exists(),
    }


@router.post("/site")
def sync_site(body: dict | None = None):
    """执行一键同步。body 可选: {"repo": "owner/repo", "push": true}"""
    body = body or {}
    repo = body.get("repo", "")
    push = bool(body.get("push", False))

    steps = []
    errors = []

    def run(cmd, cwd, timeout=300):
        try:
            r = subprocess.run(
                cmd, cwd=str(cwd), capture_output=True, text=True,
                shell=True, timeout=timeout, encoding="utf-8", errors="replace",
            )
            out = (r.stdout or "")[-2000:]
            err = (r.stderr or "")[-2000:]
            ok = r.returncode == 0
            steps.append({"cmd": cmd, "ok": ok, "stdout": out, "stderr": err})
            if not ok:
                errors.append(f"{cmd} 失败: {err[:500]}")
            return ok
        except Exception as e:
            errors.append(f"{cmd} 异常: {str(e)[:300]}")
            steps.append({"cmd": cmd, "ok": False, "stdout": "", "stderr": str(e)})
            return False

    # 1. 导出数据
    py = "python" if os.name == "nt" else "python3"
    ok1 = run(f'"{py}" tools/export_site.py', ROOT)

    # 2. 构建站点
    ok2 = run("npm run build", MOBILE)

    # 3. 推送
    ok3 = True
    push_log = ""
    if push:
        cmd = f'node scripts/sync.mjs {"--repo " + repo if repo else ""} --push'
        ok3 = run(cmd, ROOT)
        push_log = "已推送" if ok3 else "推送失败"

    return {
        "success": ok1 and ok2 and ok3,
        "exported": ok1,
        "built": ok2,
        "pushed": ok3,
        "pushDetail": push_log,
        "steps": steps,
        "errors": errors,
    }
