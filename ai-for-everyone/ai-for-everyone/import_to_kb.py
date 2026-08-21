# -*- coding: utf-8 -*-
"""
批量导入《AI for Everyone》课程 Markdown 到 X-markdown 知识库。
读取 ai-for-everyone/<week>/<lesson>.md，解析 front-matter，POST 到 /api/kb/save。
"""
import json
import sys
import io
import re
from pathlib import Path

import httpx

API = "http://127.0.0.1:8765/api/kb/save"
BASE = Path(__file__).parent


def parse_front_matter(text: str):
    """解析 YAML 风格的 front-matter 块（--- ... ---）。"""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            raw = text[3:end]
            body = text[end + 4:]
            meta = {}
            for line in raw.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue
                k, _, v = line.partition(":")
                k = k.strip()
                v = v.strip().strip("\"'")
                if k in ("tags",):
                    meta[k] = [t.strip() for t in v.split(",") if t.strip()]
                else:
                    meta[k] = v
            return meta, body.strip()
    return {}, text.strip()


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    files = sorted(BASE.rglob("*.md"))
    imported, skipped, failed = 0, 0, []
    for f in files:
        if f.name.startswith("_"):
            continue
        text = f.read_text(encoding="utf-8")
        meta, body = parse_front_matter(text)
        if not body:
            skipped += 1
            print(f"  [跳过] 空内容 {f.name}")
            continue
        # Build a unique URL per lesson so each gets its own DB record + FTS entry
        base_url = meta.get("url") or "https://www.coursera.org/learn/ai-for-everyone"
        if f.name.startswith("00-"):
            lesson_url = base_url  # course overview keeps the canonical course URL
        else:
            # keep the week home URL as a readable prefix, then append a unique slug
            lesson_url = base_url.rstrip("/") + "/" + f.stem
        payload = {
            "url": lesson_url,
            "title": meta.get("title", f.stem),
            "originalMd": body,
            "domain": meta.get("domain", "ai_general"),
            "category": meta.get("category", "tutorial"),
            "lang": meta.get("lang", "en"),
            "source": meta.get("source", "DeepLearning.AI - AI for Everyone"),
            "tags": meta.get("tags", []),
            "force": True,
        }
        try:
            r = httpx.post(API, json=payload, timeout=30)
            data = r.json()
            if data.get("success"):
                imported += 1
                print(f"  [OK] {f.name} -> {data.get('id')}")
            else:
                skipped += 1
                print(f"  [重复/失败] {f.name}: {data.get('message')}")
        except Exception as e:
            failed.append(f.name)
            print(f"  [错误] {f.name}: {e}")

    print(f"\n完成：导入 {imported}，跳过 {skipped}，失败 {len(failed)}")
    if failed:
        print("失败文件:", ", ".join(failed))


if __name__ == "__main__":
    main()
