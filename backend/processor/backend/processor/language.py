# -*- coding: utf-8 -*-
"""
逐篇语言判定：标题+正文前 2000 字符的中文字符占比 > 0.15 判 CN，否则 EN。
"""
import re

CN_RATIO_THRESHOLD = 0.15

_cjk_re = re.compile(r"[\u4e00-\u9fff]")
_alpha_re = re.compile(r"[a-zA-Z]")


def detect_lang(article: dict) -> str:
    """返回 'cn' / 'en'；正文为空时回退平台标记"""
    title = article.get("title") or ""
    summary = article.get("summary") or ""
    raw = article.get("raw_text") or ""
    text = f"{title} {summary} {raw[:2000]}"
    cjk = len(_cjk_re.findall(text))
    alpha = len(_alpha_re.findall(text))
    total = cjk + alpha
    if total == 0:
        return article.get("lang") or "cn"
    return "cn" if cjk / total > CN_RATIO_THRESHOLD else "en"

