# -*- coding: utf-8 -*-
"""
知识库索引：按「作者 + 主题」自动建立简洁索引

- 作者：从 Markdown 元信息（- 作者：X）提取，缺失时回退到来源/未标注作者
- 主题：基于标题 + 正文前 2000 字用 jieba 提取 1~2 个关键词
- 目录树：聚合类别（领域+分类）→ 主题 → 作者 → 文章，供前端目录树展开
- 索引文件：~/.xmarkdown/knowledge-base/_索引.md（精简版，不参与知识库文章列表）
- 增量缓存：按文件 mtime 缓存作者/主题，仅重算变更文件
"""
import json
import re
from datetime import datetime
from pathlib import Path

from config import KB_DIR, USER_DIR

INDEX_PATH = KB_DIR / "_索引.md"
CACHE_PATH = USER_DIR / "kb_index_cache.json"
CACHE_VERSION = 3  # 提取逻辑/停用词变化时 +1，使旧缓存失效

# 常见无区分度词，避免主题全是「Python / 数据 / 分析」
STOPWORDS = {
    "python", "使用", "分析", "数据", "如何", "什么", "一个", "可以", "我们",
    "他们", "因为", "所以", "但是", "如果", "进行", "通过", "需要", "自己",
    "现在", "知道", "没有", "这个", "那个", "一下", "这么", "就是", "不是",
    "还是", "怎么", "为什么", "之后", "之前", "还有", "很多", "一些", "这样",
    "那样", "文章", "内容", "这些", "那些", "学习", "教程", "工具", "推荐",
    "有没有", "怎么做", "是什么", "有哪些", "怎么办", "实现", "方法", "功能",
    "com", "https", "http", "www", "org", "io", "cn", "url", "链接", "地址",
    "文章链接", "更多", "欢迎", "关注", "转发", "点赞", "评论",
    "zhihu", "github", "code", "代码", "import", "fib", "xw",
}

_AUTHOR_RE = re.compile(r"^\s*[-*]\s*作者\s*[：:]\s*(.+?)\s*$", re.M)
_AUTHOR_EN_RE = re.compile(r"^\s*author\s*[：:]\s*(.+?)\s*$", re.M | re.I)
_TITLE_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.M)

DOMAIN_LABELS = {"ai_general": "通用AI", "ai_audit": "AI×审计"}
CATEGORY_LABELS = {"article": "文章", "tutorial": "教程", "application": "应用案例"}

_cache: dict = {}


def category_label(domain: str = "ai_general", category: str = "article") -> str:
    """聚合类别展示名：领域 + 分类，如「通用AI · 文章」"""
    d = DOMAIN_LABELS.get(domain or "", domain or "未分类")
    c = CATEGORY_LABELS.get(category or "", category or "未分类")
    return f"{d} · {c}"


def _load_db_meta() -> dict[str, "object"]:
    """DB 中 filepath → KnowledgeBaseArticle 记录"""
    try:
        from database import SessionLocal, KnowledgeBaseArticle
        db = SessionLocal()
        try:
            return {a.filepath: a for a in db.query(KnowledgeBaseArticle).all()}
        finally:
            db.close()
    except Exception:
        return {}


def _title_from_filename(filename: str) -> str:
    name = Path(filename).stem
    for suffix in ("_原文", "_译文"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


def extract_author(md: str, source: str = "") -> str:
    """从 Markdown 元信息提取作者"""
    m = _AUTHOR_RE.search(md or "")
    if m:
        author = m.group(1).strip().rstrip("，。")
        if author:
            return author
    m = _AUTHOR_EN_RE.search(md or "")
    if m:
        author = m.group(1).strip()
        if author:
            return author
    return (source or "").strip() or "未标注作者"


def extract_topic(title: str, md: str) -> str:
    """基于标题 + 正文开头提取 1~2 个关键词作为主题"""
    text = f"{title or ''} {md[:2000] if md else ''}"
    # 剥离 URL / 邮箱 / 代码噪声，避免主题被 https/com 污染
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"www\.\S+", " ", text)
    text = re.sub(r"\b[\w-]+\.(?:com|cn|org|io|net|ai|dev|github\.io)\b", " ", text)
    text = re.sub(r"[\w.+-]+@[\w.-]+", " ", text)
    text = re.sub(r"[`*_#~]|`{1,6}", " ", text)
    try:
        import jieba.analyse
        tags_with_weight = jieba.analyse.extract_tags(text, topK=5, withWeight=True)
    except Exception:
        tags_with_weight = []
    kept = []
    for t, w in tags_with_weight:
        word = t.strip()
        if (
            word
            and word.lower() not in STOPWORDS
            and len(word) >= 2
            and not word.isdigit()
            and not re.search(r"[^\w\u4e00-\u9fff·]", word)
            and len(word) <= 20
        ):
            kept.append((word, w))
    if kept:
        # 主词权重显著高于次词时，只保留主词，让主题更聚焦
        if len(kept) >= 2 and kept[0][1] > kept[1][1] * 2:
            return kept[0][0]
        return " · ".join(w for w, _ in kept[:2])

    # 兜底：从标题中挑词
    try:
        import jieba
        words = [
            w.strip()
            for w in jieba.cut(title or "")
            if w.strip()
            and w.strip().lower() not in STOPWORDS
            and len(w.strip()) >= 2
            and not w.strip().isdigit()
            and not re.search(r"[^\w\u4e00-\u9fff·]", w.strip())
        ]
    except Exception:
        words = []
    if words:
        return " · ".join(words[:2])
    return "其他"


def _load_cache() -> dict:
    global _cache
    if _cache:
        return _cache
    try:
        if CACHE_PATH.exists():
            data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            if data.get("version") == CACHE_VERSION:
                _cache = data.get("entries", {})
    except Exception:
        _cache = {}
    return _cache


def _save_cache(cache: dict):
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(
            json.dumps(
                {"version": CACHE_VERSION, "entries": cache},
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"  [KB索引] 缓存写入失败: {e}")


def _article_entries(sources: dict[str, str]) -> list[dict]:
    """扫描知识库 md 文件，返回 [{file, title, author, topic}]"""
    cache = _load_cache()
    entries = []
    for md_file in sorted(KB_DIR.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        stat = md_file.stat()
        key = str(md_file)
        cached = cache.get(key)
        if cached and abs(cached.get("mtime", 0) - stat.st_mtime) < 0.001:
            entries.append({
                "file": md_file.name,
                "path": key,
                "title": cached.get("title") or _title_from_filename(md_file.name),
                "author": cached.get("author") or "未标注作者",
                "topic": cached.get("topic") or "其他",
            })
            continue

        try:
            md = md_file.read_text(encoding="utf-8", errors="replace")[:6000]
        except Exception:
            md = ""
        title = _TITLE_RE.search(md)
        title = title.group(1).strip() if title else _title_from_filename(md_file.name)
        author = extract_author(md, sources.get(key, ""))
        topic = extract_topic(title, md)
        cache[key] = {
            "mtime": stat.st_mtime,
            "title": title,
            "author": author,
            "topic": topic,
        }
        entries.append({
            "file": md_file.name,
            "path": key,
            "title": title,
            "author": author,
            "topic": topic,
        })

    # 清理已删除文件的缓存
    current = {e["path"] for e in entries}
    stale = [k for k in cache if k not in current]
    for k in stale:
        cache.pop(k, None)
    if stale or entries:
        _save_cache(cache)
    return entries


def _load_sources() -> dict[str, str]:
    """DB 中 filepath → source，用于作者回退"""
    try:
        from database import SessionLocal, KnowledgeBaseArticle
        db = SessionLocal()
        try:
            return {a.filepath: (a.source or "") for a in db.query(KnowledgeBaseArticle).all()}
        finally:
            db.close()
    except Exception:
        return {}


def build_kb_index() -> dict:
    """构建精简知识库索引（类别→主题→作者计数，不含文章长列表）
    返回 {path, markdown, updatedAt, total, authors, topics}"""
    KB_DIR.mkdir(parents=True, exist_ok=True)
    sources = _load_sources()
    entries = _article_entries(sources)
    meta = _load_db_meta()

    # 聚合类别（领域+分类）→ 主题 → 作者 → 文章
    cat_groups: dict[str, dict[str, dict[str, list[dict]]]] = {}
    for e in entries:
        rec = meta.get(e["path"])
        domain = getattr(rec, "domain", None) or "ai_general"
        category = getattr(rec, "category", None) or "article"
        key = f"{domain}|{category}"
        cat_groups.setdefault(key, {}).setdefault(e["topic"], {}).setdefault(
            e["author"], []
        ).append(e)

    lines = ["# 知识库索引", ""]
    total = len(entries)
    author_count = len({e["author"] for e in entries})
    topic_count = len({e["topic"] for e in entries})
    lines.append(
        f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')} · "
        f"共 {total} 篇 · {author_count} 位作者 · {topic_count} 个主题"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    authors_stats: list[dict] = []
    topics_stats: dict[str, int] = {}
    for cat_key, topics in sorted(
        cat_groups.items(),
        key=lambda kv: (-sum(len(items) for t in kv[1].values() for a in t.values() for items in [a]), kv[0]),
    ):
        domain, category = cat_key.split("|", 1)
        cat_total = sum(
            len(items)
            for topics_map in topics.values()
            for items in topics_map.values()
        )
        lines.append(f"## {category_label(domain, category)}（{cat_total} 篇）")
        lines.append("")
        for topic, authors in sorted(
            topics.items(),
            key=lambda kv: (-sum(len(v) for v in kv[1].values()), kv[0]),
        ):
            topic_total = sum(len(v) for v in authors.values())
            topics_stats[topic] = topics_stats.get(topic, 0) + topic_total
            lines.append(f"### 主题：{topic}（{topic_total} 篇）")
            lines.append("")
            for author, items in sorted(
                authors.items(),
                key=lambda kv: (-len(kv[1]), kv[0]),
            ):
                authors_stats.append({"name": author, "count": len(items)})
                lines.append(f"- {author}（{len(items)} 篇）")
            lines.append("")

    markdown = "\n".join(lines).strip() + "\n"
    INDEX_PATH.write_text(markdown, encoding="utf-8")
    return {
        "path": str(INDEX_PATH),
        "markdown": markdown,
        "updatedAt": datetime.now().isoformat(timespec="seconds"),
        "total": total,
        "authors": sorted(authors_stats, key=lambda x: -x["count"]),
        "topics": sorted(topics_stats.items(), key=lambda kv: -kv[1]),
    }


def build_kb_tree() -> dict:
    """构建知识库目录树：聚合类别 → 主题 → 作者 → 文章
    返回 {total, updatedAt, categories: [{key, label, domain, category, count, topics}]}"""
    KB_DIR.mkdir(parents=True, exist_ok=True)
    sources = _load_sources()
    entries = _article_entries(sources)
    meta = _load_db_meta()

    cat_groups: dict[str, dict[str, dict[str, list[dict]]]] = {}
    for e in entries:
        rec = meta.get(e["path"])
        domain = getattr(rec, "domain", None) or "ai_general"
        category = getattr(rec, "category", None) or "article"
        key = f"{domain}|{category}"
        cat_groups.setdefault(key, {}).setdefault(e["topic"], {}).setdefault(
            e["author"], []
        ).append(e)

    def item_out(e: dict, rec) -> dict:
        stat = Path(e["path"]).stat()
        has_translation = False
        if rec is not None:
            translated = getattr(rec, "translated_path", "") or ""
            has_translation = bool(translated and Path(translated).exists())
        return {
            "name": e["title"],
            "path": e["path"],
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "sourceUrl": getattr(rec, "source_url", "") if rec else "",
            "domain": getattr(rec, "domain", "") if rec else "",
            "lang": getattr(rec, "lang", "") if rec else "",
            "category": getattr(rec, "category", "") if rec else "",
            "source": getattr(rec, "source", "") if rec else "",
            "hasTranslation": has_translation,
            "author": e["author"],
            "topic": e["topic"],
        }

    categories = []
    for cat_key, topics in sorted(
        cat_groups.items(),
        key=lambda kv: (
            -sum(len(items) for t in kv[1].values() for items in t.values()),
            kv[0],
        ),
    ):
        domain, category = cat_key.split("|", 1)
        topic_nodes = []
        for topic, authors in sorted(
            topics.items(),
            key=lambda kv: (-sum(len(v) for v in kv[1].values()), kv[0]),
        ):
            author_nodes = []
            for author, items in sorted(
                authors.items(),
                key=lambda kv: (-len(kv[1]), kv[0]),
            ):
                author_nodes.append({
                    "author": author,
                    "count": len(items),
                    "items": [item_out(e, meta.get(e["path"])) for e in sorted(items, key=lambda x: x["title"])],
                })
            topic_nodes.append({
                "topic": topic,
                "count": sum(len(v) for v in authors.values()),
                "authors": author_nodes,
            })
        categories.append({
            "key": cat_key,
            "label": category_label(domain, category),
            "domain": domain,
            "category": category,
            "count": sum(t["count"] for t in topic_nodes),
            "topics": topic_nodes,
        })

    return {
        "total": len(entries),
        "updatedAt": datetime.now().isoformat(timespec="seconds"),
        "categories": categories,
    }


def ensure_kb_index(force: bool = False) -> dict:
    """索引不存在或过期时重建；否则直接返回现有索引"""
    try:
        if not force and INDEX_PATH.exists():
            newest_mtime = 0.0
            for md_file in KB_DIR.glob("*.md"):
                if md_file.name.startswith("_"):
                    continue
                newest_mtime = max(newest_mtime, md_file.stat().st_mtime)
            if INDEX_PATH.stat().st_mtime >= newest_mtime:
                md = INDEX_PATH.read_text(encoding="utf-8")
                m = re.search(r"共 (\d+) 篇 · (\d+) 位作者 · (\d+) 个主题", md)
                return {
                    "path": str(INDEX_PATH),
                    "markdown": md,
                    "updatedAt": datetime.fromtimestamp(INDEX_PATH.stat().st_mtime)
                    .isoformat(timespec="seconds"),
                    "total": int(m.group(1)) if m else 0,
                    "authorCount": int(m.group(2)) if m else 0,
                    "topicCount": int(m.group(3)) if m else 0,
                    "cached": True,
                }
        return build_kb_index()
    except Exception as e:
        print(f"  [KB索引] 构建失败: {e}")
        return {
            "path": str(INDEX_PATH),
            "markdown": f"> 索引构建失败: {e}",
            "updatedAt": datetime.now().isoformat(timespec="seconds"),
            "total": 0,
            "authors": [],
            "topics": [],
            "error": str(e),
        }


if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    result = build_kb_index()
    print(f"构建完成：共 {result['total']} 篇")
    print(result["markdown"][:800])
