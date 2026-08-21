# -*- coding: utf-8 -*-
"""
Markdown 转换 API 端点
"""
from fastapi import APIRouter, HTTPException
from models import MarkdownConvertRequest, MarkdownConvertResponse, SubtitleConvertRequest, SubtitleConvertResponse
from converter.html_to_md import convert_url_to_markdown
from converter.subtitle_to_md import fetch_bilibili_subtitle

router = APIRouter(prefix="/api/md", tags=["markdown"])


@router.post("/convert", response_model=MarkdownConvertResponse)
def convert_to_markdown(req: MarkdownConvertRequest):
    """将网页 URL 转为 Markdown"""
    try:
        result = convert_url_to_markdown(req.url)
        return MarkdownConvertResponse(
            markdown=result["markdown"],
            title=result["title"],
            sourceUrl=result["sourceUrl"],
            category=result["category"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")


@router.post("/subtitle", response_model=SubtitleConvertResponse)
def convert_subtitle(req: SubtitleConvertRequest):
    """将视频字幕转为结构化文章"""
    try:
        result = fetch_bilibili_subtitle(req.videoUrl)
        return SubtitleConvertResponse(
            markdown=result["markdown"],
            videoTitle=result["videoTitle"],
            duration=result["duration"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"字幕转换失败: {str(e)}")
