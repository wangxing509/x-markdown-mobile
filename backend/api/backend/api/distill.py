# -*- coding: utf-8 -*-
"""
Skill 蒸馏 API 端点
"""
from fastapi import APIRouter, HTTPException
from models import DistillRequest, DistillResponse
from distiller.skill_distiller import distill_content, export_skill
from distiller.skill_template import get_distill_prompt

router = APIRouter(prefix="/api", tags=["distill"])


@router.post("/distill", response_model=DistillResponse)
def distill_skill(req: DistillRequest):
    """
    Skill 蒸馏
    后端生成 prompt，实际 LLM 调用由 Electron 主进程完成
    若无 LLM，使用简化规则蒸馏
    """
    try:
        # 生成 prompt（供前端调用 LLM）
        prompt = get_distill_prompt(req.text, req.skillName)

        # 简化规则蒸馏（无 LLM 时的 fallback）
        # 提取标题和前 50 行
        lines = req.text.split("\n")
        content_lines = [l for l in lines if l.strip() and not l.startswith("!")][:50]
        simplified_content = "\n".join(content_lines)

        distilled = distill_content(req.text, req.skillName, llm_response=simplified_content)
        skill_path = export_skill(req.skillName, distilled)

        return DistillResponse(
            skillName=req.skillName,
            content=distilled,
            skillPath=skill_path,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"蒸馏失败: {str(e)}")
