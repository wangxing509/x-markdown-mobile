# -*- coding: utf-8 -*-
"""
正文富集与验证：对候选文章并发抓取原文 markdown，
验证通过标准：md 长度 >= 500、无失败标记、标题非空。
"""
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    VERIFY_MIN_MD_LENGTH,
    ENRICH_CONCURRENCY,
    ENRICH_TIMEOUT,
)

FAIL_MARKERS = ["抓取失败", "无法解析正文", "内容过长已截断", "转换失败", "Fetch failed", "404 Not Found"]


def _has_failure_marker(md: str) -> bool:
    head = md[:200]
    return any(m in head for m in FAIL_MARKERS)


def _enrich_one(article: dict) -> dict:
    """抓取原文并写入 raw_text/verified/md_length 等字段"""
    url = article.get("url", "")
    if not url:
        article["verified"] = False
        article["md_length"] = 0
        return article
    try:
        from converter.html_to_md import convert_url_to_markdown
        result = convert_url_to_markdown(url)
        md = result.get("markdown", "") or ""
        title = (result.get("title") or "").strip()
        ok = (
            len(md) >= VERIFY_MIN_MD_LENGTH
            and bool(title)
            and not _has_failure_marker(md)
        )
        article["verified"] = ok
        article["md_length"] = len(md)
        if ok:
            # 去除尾部的来源标注后再作为正文
            body = re.sub(r"\n*---\n> 来源:.*$", "", md, flags=re.DOTALL).strip()
            if not article.get("raw_text") or len(article.get("raw_text") or "") < len(body):
                article["raw_text"] = body
            if not article.get("title") or len(article.get("title", "")) < 3:
                article["title"] = title
            if not article.get("summary"):
                from crawler.base import extract_summary
                article["summary"] = extract_summary(body)[:200]
    except Exception as e:
        article["verified"] = False
        article["md_length"] = 0
        article["verify_error"] = str(e)[:200]
    return article


def enrich_and_verify(articles: list[dict]) -> list[dict]:
    """并发富集+验证，返回验证通过的文章"""
    verified = []
    with ThreadPoolExecutor(max_workers=ENRICH_CONCURRENCY) as ex:
        futures = [ex.submit(_enrich_one, a) for a in articles]
        for fut in as_completed(futures):
            try:
                a = fut.result()
            except Exception:
                continue
            if a.get("verified"):
                verified.append(a)
    verified.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)
    print(f"  [验证] 富集 {len(articles)} 条，通过 {len(verified)} 条")
    return verified

