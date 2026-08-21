# -*- coding: utf-8 -*-
"""
二维配额选择：领域（ai_general / ai_audit）x 语言（cn / en）。
保证：总量 clamp[30,50]、EN 总量=round(0.4T)、审计占比 [20%,30%]、单源上限。
分类 article/tutorial/application 按 40/35/25 软配额。
"""
from collections import defaultdict

from config import TOP_N_MIN, TOP_N_MAX, EN_RATIO, PER_SOURCE_CAP, CATEGORY_QUOTA


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _pick(pool, target, used_urls, source_cap=PER_SOURCE_CAP, category_balance=True):
    """从候选池按 score 择优，遵守单源上限与分类软配额"""
    picked = []
    source_count = defaultdict(int)
    cat_count = defaultdict(int)

    def _can_add(a):
        if a.get("url") in used_urls:
            return False
        src = a.get("source", "")
        if src and src != "粘贴链接" and source_count[src] >= source_cap:
            return False
        return True

    def _add(a):
        picked.append(a)
        used_urls.add(a.get("url"))
        src = a.get("source", "")
        if src:
            source_count[src] += 1
        cat_count[a.get("category", "article")] += 1

    remaining = [a for a in pool if a.get("url") not in used_urls]
    remaining.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)

    if category_balance and target > 0:
        # 软配额：先按分类目标各取若干，避免同质刷屏
        buckets = defaultdict(list)
        for a in remaining:
            buckets[a.get("category", "article")].append(a)
        targets = {cat: int(target * ratio) for cat, ratio in CATEGORY_QUOTA.items()}
        for cat, cat_target in targets.items():
            if len(picked) >= target:
                break
            for a in buckets[cat]:
                if len(picked) >= target or cat_count[cat] >= cat_target:
                    break
                if _can_add(a):
                    _add(a)
        # 配额轮转后仍不足：按分数补齐
        for a in remaining:
            if len(picked) >= target:
                break
            if _can_add(a):
                _add(a)
    else:
        for a in remaining:
            if len(picked) >= target:
                break
            if _can_add(a):
                _add(a)
    return picked


def select_with_quotas(articles: list[dict], top_n: int = 40) -> tuple[list[dict], dict]:
    """
    返回 (selected, stats)
    stats: {total, en, cn, audit, general, shortfall, cells: {...}}
    """
    T = _clamp(top_n, TOP_N_MIN, TOP_N_MAX)
    en_target = round(T * EN_RATIO)
    audit_target = _clamp(round(T * 0.25), round(T * 0.20), round(T * 0.30))

    # 分解二维配额（audit/general 各自内部 4:6）
    audit_en = round(audit_target * EN_RATIO)
    audit_cn = audit_target - audit_en
    general_en = en_target - audit_en
    general_cn = T - audit_target - general_en

    cells = {
        ("ai_audit", "en"): audit_en,
        ("ai_audit", "cn"): audit_cn,
        ("ai_general", "en"): general_en,
        ("ai_general", "cn"): general_cn,
    }

    by_cell: dict[tuple, list[dict]] = defaultdict(list)
    for a in articles:
        domain = a.get("domain") or "ai_general"
        lang = a.get("lang") or "cn"
        by_cell[(domain, lang)].append(a)

    selected = []
    used_urls = set()
    stats_cells = {}
    for key, target in cells.items():
        picked = _pick(by_cell[key], target, used_urls)
        stats_cells[f"{key[0]}:{key[1]}"] = len(picked)
        selected.extend(picked)

    selected.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)
    for i, a in enumerate(selected, 1):
        a["rank"] = i

    en_count = sum(1 for a in selected if a.get("lang") == "en")
    audit_count = sum(1 for a in selected if a.get("domain") == "ai_audit")
    stats = {
        "total": len(selected),
        "target": T,
        "en": en_count,
        "cn": len(selected) - en_count,
        "audit": audit_count,
        "general": len(selected) - audit_count,
        "shortfall": max(0, T - len(selected)),
        "cells": stats_cells,
    }
    return selected, stats
