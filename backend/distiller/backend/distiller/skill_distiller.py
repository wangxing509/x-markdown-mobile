# -*- coding: utf-8 -*-
"""
Skill 蒸馏模块
通过 LLM 将原文蒸馏为标准化 SKILL.md
"""
from config import SKILLS_DIR
from distiller.skill_template import get_distill_prompt, build_skill_doc


def distill_content(text: str, skill_name: str, llm_response: str = "") -> str:
    """
    蒸馏内容为 Skill 格式
    如果提供了 LLM 响应，直接使用；否则构建 prompt 供外部 LLM 调用
    """
    if llm_response:
        # 如果 LLM 响应已包含 frontmatter，直接返回
        if llm_response.strip().startswith("---"):
            return llm_response.strip()
        # 否则补充 frontmatter
        description = f"基于「{skill_name}」内容蒸馏的自动化技能"
        return build_skill_doc(skill_name, description, llm_response)
    else:
        # 返回 prompt，供外部调用
        return get_distill_prompt(text, skill_name)


def export_skill(skill_name: str, content: str) -> str:
    """导出 Skill 到 ~/.codebuddy/skills/<name>/SKILL.md"""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    skill_dir = SKILLS_DIR / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    with open(skill_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [Skill] 已导出: {skill_path}")
    return str(skill_path)
