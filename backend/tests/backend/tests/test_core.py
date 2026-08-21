# -*- coding: utf-8 -*-
"""核心算法单元测试：语言判定 / AI×审计领域判定 / 配额不变式 / 关键词匹配"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processor.language import detect_lang
from processor.domain import classify_domain
from processor.keywords import match_keywords
from processor.quota import select_with_quotas
from config import PER_SOURCE_CAP

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name} {detail}")


def test_language():
    print("[语言判定]")
    check("纯中文判 cn", detect_lang({"title": "人工智能审计应用实践", "raw_text": "本文介绍大模型在审计行业的落地案例。"}) == "cn")
    check("纯英文判 en", detect_lang({"title": "How LLMs improve audit analytics", "raw_text": "This article explores using large language models in auditing."}) == "en")
    check("中英混合（中文主导）判 cn", detect_lang({"title": "AI in 审计场景", "raw_text": "本文讨论机器学习和数据审计的结合。"}) == "cn")
    check("英文代码/工具内容判 en", detect_lang({"title": "llm-course", "raw_text": "Course to get into Large Language Models with roadmaps and Colab notebooks."}) == "en")


def test_keywords():
    print("[关键词匹配]")
    check("AI 不误命中 said", "AI" not in match_keywords("he said the train ran", ["AI"]))
    check("AI 命中标题", match_keywords("New AI agent framework", ["AI", "Agent"]) == ["AI", "Agent"])
    # 返回顺序跟随关键词列表顺序
    check("中文关键词命中", match_keywords("智能审计系统上线", ["审计", "智能"]) == ["审计", "智能"])


def test_domain():
    print("[AI×审计 领域判定]")
    check("审计∩AI → ai_audit",
          classify_domain({"title": "大模型赋能智能审计", "raw_text": "利用 LLM 进行审计底稿分析和连续审计。"}) == "ai_audit")
    check("英文 审计∩AI → ai_audit",
          classify_domain({"title": "Using AI in audit analytics", "raw_text": "Machine learning improves continuous auditing and fraud detection."}) == "ai_audit")
    check("纯审计无 AI → 剔除",
          classify_domain({"title": "审计准则修订解读", "raw_text": "本次修订涉及审计报告与质量控制程序。"}) is None)
    check("纯 AI 无审计 → ai_general",
          classify_domain({"title": "RAG 应用开发指南", "raw_text": "构建检索增强生成的智能问答系统。"}) == "ai_general")


def _make_pool(n, domain, lang, source_prefix="src"):
    out = []
    for i in range(n):
        out.append({
            "title": f"{domain}-{lang}-{i}",
            "url": f"https://{source_prefix}{i % 12}.example.com/{domain}/{lang}/{i}",
            "source": f"{source_prefix}{i % 12}",
            "domain": domain,
            "lang": lang,
            "category": ["article", "tutorial", "application"][i % 3],
            "score": 100.0 - i * 0.5,
        })
    return out


def test_quota():
    print("[配额选择]")
    for T in (30, 40, 50):
        pool = []
        pool += _make_pool(60, "ai_general", "cn", "gcn")
        pool += _make_pool(40, "ai_general", "en", "gen")
        pool += _make_pool(20, "ai_audit", "cn", "acn")
        pool += _make_pool(15, "ai_audit", "en", "aen")
        selected, stats = select_with_quotas(pool, T)
        total = len(selected)
        check(f"T={T}: 总量为 {T}", total == T, f"got {total}")
        en = stats["en"]
        check(f"T={T}: EN 比例≈40%（±1）", abs(en / T - 0.4) <= 0.1, f"en={en}/{T}")
        audit = stats["audit"]
        check(f"T={T}: 审计占比在 [20%,30%]", 0.2 * T <= audit <= 0.3 * T, f"audit={audit}/{T}")
        # 单源上限
        from collections import Counter
        src_counts = Counter(a["source"] for a in selected)
        over = {k: v for k, v in src_counts.items() if v > PER_SOURCE_CAP}
        check(f"T={T}: 单源 ≤{PER_SOURCE_CAP}", not over, f"{over}")
    # 池不足时
    # 池中只有中文通用候选：严格配额下仅填满 general_cn 格子（T=40 → 18 格）
    pool = _make_pool(20, "ai_general", "cn", "small")
    selected, stats = select_with_quotas(pool, 40)
    check("缺 EN/审计时严格配额：仅填 general_cn 格（18）", len(selected) == 18, f"got {len(selected)}")
    check("缺 EN/审计时 shortfall=22", stats["shortfall"] == 22, f"got {stats['shortfall']}")
    check("所选全部为 cn", all(a["lang"] == "cn" for a in selected))


if __name__ == "__main__":
    test_keywords()
    test_language()
    test_domain()
    test_quota()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    sys.exit(1 if FAIL else 0)
