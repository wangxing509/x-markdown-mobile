# -*- coding: utf-8 -*-
"""
Skill frontmatter 模板（参照 CodeBuddy rules/*.md 格式）
"""


def generate_skill_frontmatter(name: str, description: str, version: str = "1.0.0") -> str:
    """生成 Skill frontmatter"""
    return f"""---
name: {name}
description: {description}
version: {version}
alwaysApply: false
allowed-tools:
disable: false
---"""


def build_skill_doc(name: str, description: str, content: str) -> str:
    """构建完整的 Skill 文档"""
    frontmatter = generate_skill_frontmatter(name, description)
    return f"{frontmatter}\n\n{content}"


def get_distill_prompt(text: str, skill_name: str) -> str:
    """构建蒸馏 LLM prompt"""
    return f"""你是一个 Skill 蒸馏专家。请将以下内容蒸馏为一个标准化、可直接使用的 Skill 文档。

要求：
1. 提取核心工作流、代码模板、最佳实践
2. 去除冗余叙述和背景介绍
3. 输出 Markdown 格式，包含 frontmatter（name, description, version, alwaysApply）
4. Skill 名称: {skill_name}
5. 内容结构清晰，包含步骤编号和代码示例
6. 控制在 300 行以内

原始内容：
{text}"""
