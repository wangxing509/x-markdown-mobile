# -*- coding: utf-8 -*-
"""知识库「作者 + 主题」索引单元测试"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import kb_index

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  OK {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {detail}")


def test_extract_author():
    md = "# 标题\n\n- 作者：朱卫军\n- 类型：article\n"
    check("中文作者行", kb_index.extract_author(md) == "朱卫军", kb_index.extract_author(md))

    md2 = "# 标题\n\nauthor: Alice\n"
    check("英文 author 行", kb_index.extract_author(md2) == "Alice", kb_index.extract_author(md2))

    check("无作者回退来源", kb_index.extract_author("no meta", "GitHub") == "GitHub")
    check("无作者无来源", kb_index.extract_author("no meta") == "未标注作者")


def test_extract_topic():
    md = (
        "这是一篇介绍如何使用 pandas 进行数据清洗和数据分析的文章，"
        "包含 groupby、merge、apply 等常用操作。https://zhuanlan.zhihu.com/p/123 "
        "更多内容请看 www.example.com 与 github.com 上的示例。"
    )
    topic = kb_index.extract_topic("pandas 数据清洗实战", md)
    check("主题包含 pandas", "pandas" in topic.lower(), topic)
    check("主题不含 URL 噪声", "com" not in topic.lower() and "https" not in topic.lower(), topic)

    topic2 = kb_index.extract_topic("测试文章", "")
    check("空正文有兜底主题", bool(topic2), topic2)


def main():
    print("== 知识库索引模块测试 ==")
    test_extract_author()
    test_extract_topic()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
