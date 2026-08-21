# -*- coding: utf-8 -*-
"""
翻译 API 端点（后端 fallback）
默认由 Electron LLM 桥接处理，后端提供 MyMemory 降级
"""
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from translator.llm_translator import translate_long_text

router = APIRouter(prefix="/api/translate", tags=["translate"])


class TranslateRequest(BaseModel):
    texts: List[str] = Field(..., max_length=10)
    source_lang: str = "auto"
    target_lang: str = "zh-CN"


class TranslationItem(BaseModel):
    original: str
    translated: str


class TranslateResponse(BaseModel):
    results: List[TranslationItem]


@router.post("", response_model=TranslateResponse)
def translate_texts(req: TranslateRequest):
    """批量翻译文本（英 → 中）"""
    try:
        results = []
        for text in req.texts:
            translated = translate_long_text(text)
            results.append(TranslationItem(original=text, translated=translated))
        return TranslateResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")
