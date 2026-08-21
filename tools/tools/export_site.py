# -*- coding: utf-8 -*-
"""
X-markdown 一键同步导出工具
===========================
从桌面端 SQLite 数据库读取「每日精选 + 知识库」，导出为手机端
PWA 所需的静态 JSON 文件，写入 xmarkdown-mobile/public/data/。

用法:
    python tools/export_site.py [--db PATH] [--out DIR] [--limit N]

默认从 backend/data/xmarkdown.db 读取，输出到 xmarkdown-mobile/public/data/。
导出后用 `npm run build` 构建，再将 dist 部署到 GitHub Pages 即可。
"""
import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "backend" / "data" / "xmarkdown.db"
DEFAULT_OUT = ROOT / "xmarkdown-mobile" / "public" / "data"


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def export_top100(con, limit=200) -> dict:
    """导出每日精选列表 + 统计"""
    cur = con.cursor()
    rows = cur.execute(
        """
        SELECT id, title, url, summary, source, category, score, rank, tags,
               likes, comments, author, lang, domain, verified, md_length
        FROM top100_articles
        ORDER BY rank ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    items = []
    for r in rows:
        items.append({
            "id": r[0],
            "rank": r[7],
            "title": r[1],
            "url": r[2],
            "summary": r[3] or "",
            "source": r[4] or "",
            "category": r[5] or "article",
            "score": r[6] or 0,
            "tags": r[8] or "",
            "likes": r[9],
            "comments": r[10],
            "author": r[11] or "",
            "lang": r[12] or "",
            "domain": r[13] or "ai_general",
            "verified": bool(r[14]),
            "mdLength": r[15] or 0,
        })

    total = len(items)
    cn = sum(1 for i in items if i["lang"] == "cn")
    en = sum(1 for i in items if i["lang"] == "en")
    audit = sum(1 for i in items if i["domain"] == "ai_audit")
    general = total - audit
    # target 尽量贴近桌面端配置（top_n 默认 40，这里取总目标的合理值）
    target = max(total, 40)

    stats = {
        "total": total,
        "target": target,
        "cn": cn,
        "en": en,
        "audit": audit,
        "general": general,
        "shortfall": max(0, target - total),
    }
    return {"items": items, "stats": stats}


def export_kb(con, limit=2000) -> tuple:
    """导出知识库元数据 + 文章内容。
    返回 (meta_list, articles_dir_name)。文章内容写入 articles/<id>.json。"""
    cur = con.cursor()
    rows = cur.execute(
        """
        SELECT id, title, source_url, category, saved_at, domain, lang, source,
               original_md, translated_md
        FROM kb_articles
        ORDER BY saved_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    meta_list = []
    for r in rows:
        has_translation = bool(r[9] and r[9].strip())
        meta_list.append({
            "id": r[0],
            "title": r[1] or "",
            "source": r[7] or "",
            "domain": r[5] or "ai_general",
            "lang": r[6] or "",
            "category": r[3] or "article",
            "savedAt": r[4] or "",
            "hasTranslation": has_translation,
            "size": len(r[8] or ""),
        })
    return meta_list


def write_articles(con, out_dir, limit=2000, chunk_size=120):
    """逐篇写入文章内容到 articles/c<chunk>.json（每 chunk 一篇字典，键为文章 id）。
    原文 + 可选译文。分块是为了控制文件数量，便于 GitHub 推送/部署。"""
    cur = con.cursor()
    art_dir = out_dir / "articles"
    art_dir.mkdir(parents=True, exist_ok=True)
    rows = cur.execute(
        """
        SELECT id, original_md, translated_md FROM kb_articles
        ORDER BY saved_at DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()
    # 写分块文件：每篇文章按 id // chunk_size 归入对应分块（与前端 loadArticle 计算一致）
    by_chunk = {}
    for art_id, original, translated in rows:
        chunk_idx = art_id // chunk_size
        by_chunk.setdefault(chunk_idx, {})[str(art_id)] = {
            "original": original or "",
            "translated": (translated or "") if translated else None,
        }
    chunk_files = []
    for chunk_idx in sorted(by_chunk.keys()):
        fname = f"c{chunk_idx}.json"
        with open(art_dir / fname, "w", encoding="utf-8") as f:
            json.dump(by_chunk[chunk_idx], f, ensure_ascii=False)
        chunk_files.append(fname)
    return len(rows), chunk_files


def main():
    ap = argparse.ArgumentParser(description="X-markdown 一键同步导出")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--limit", type=int, default=2000)
    args = ap.parse_args()

    db_path = Path(args.db)
    out_dir = Path(args.out)
    if not db_path.exists():
        print(f"[错误] 数据库不存在: {db_path}", file=sys.stderr)
        sys.exit(1)
    out_dir.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(str(db_path))
    con.text_factory = lambda b: b.decode("utf-8", errors="replace")
    try:
        print("[1/3] 导出每日精选...")
        top = export_top100(con, args.limit)

        print("[2/3] 导出知识库元数据...")
        kb_meta = export_kb(con, args.limit)

        print("[3/3] 写入文章内容...")
        art_count, chunk_files = write_articles(con, out_dir, args.limit)

        # 清理旧的单文件文章（如从旧格式升级）
        art_dir = out_dir / "articles"
        if art_dir.exists():
            for old in art_dir.glob("*.json"):
                if old.name not in chunk_files:
                    old.unlink(missing_ok=True)

        index = {
            "generatedAt": now_iso(),
            "nextRefresh": "手动刷新",
            "top100": top["items"],
            "stats": top["stats"],
            "kbCount": len(kb_meta),
        }

        with open(out_dir / "index.json", "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False)
        with open(out_dir / "kb.json", "w", encoding="utf-8") as f:
            json.dump(kb_meta, f, ensure_ascii=False)

        print(f"\n完成！")
        print(f"  每日精选: {top['stats']['total']} 条")
        print(f"  知识库元数据: {len(kb_meta)} 条")
        print(f"  文章内容: {art_count} 篇")
        print(f"  输出目录: {out_dir}")
        print(f"\n下一步: 在 xmarkdown-mobile 下执行 `npm run build` 构建站点，")
        print(f"       将 dist 目录部署到 GitHub Pages 即可。")
    finally:
        con.close()


if __name__ == "__main__":
    main()
