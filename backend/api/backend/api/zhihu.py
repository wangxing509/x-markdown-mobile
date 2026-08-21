# -*- coding: utf-8 -*-
"""
知乎专栏下载 API 端点
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import zhihu_column

router = APIRouter(prefix="/api/zhihu", tags=["zhihu"])


class ColumnStartRequest(BaseModel):
    """启动专栏下载请求"""
    columnId: str = Field(..., description="知乎专栏 ID 或链接")
    outputDir: str = Field("", description="保存根目录（留空使用默认 ~/.xmarkdown/zhihu）")
    downloadVideos: bool = Field(False, description="是否下载视频文件（默认仅保留链接）")
    maxItems: int = Field(0, description="最多下载条数，0 表示全部")
    autoImport: bool = Field(True, description="下载完成后是否自动导入知识库")


class ColumnInfoRequest(BaseModel):
    """查询专栏信息请求"""
    columnId: str = Field(..., description="知乎专栏 ID、链接或作者个人主页链接")


class CookieSaveRequest(BaseModel):
    """保存知乎 Cookie 请求"""
    zC0: str = Field(..., description="知乎登录 Cookie z_c0")
    dC0: str = Field("", description="可选 d_c0")


@router.post("/column/start")
def start_column_download(req: ColumnStartRequest):
    """输入专栏 ID/链接，后台启动下载任务"""
    try:
        job = zhihu_column.start_job(
            req.columnId,
            output_dir=req.outputDir.strip(),
            download_videos=req.downloadVideos,
            max_items=req.maxItems,
            auto_import=req.autoImport,
        )
        return {
            "success": True,
            "jobId": job["jobId"],
            "columnId": job["columnId"],
            "columnName": job["columnName"],
            "resolvedFrom": job.get("resolvedFrom") or "",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/column/info")
def get_column_info(req: ColumnInfoRequest):
    """解析输入（支持个人主页自动解析）并返回专栏信息与总条数"""
    try:
        info = zhihu_column.inspect_column(req.columnId)
        return {
            "columnId": info["columnId"],
            "columnName": info["title"],
            "author": info.get("author", ""),
            "itemsCount": info.get("itemsCount", 0),
            "description": info.get("description", ""),
            "resolvedFrom": info.get("resolvedFrom", ""),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"专栏信息获取失败: {str(e)}")


@router.get("/column/status/{job_id}")
def get_column_status(job_id: str):
    """查询下载任务进度"""
    job = zhihu_column.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
    return job


@router.get("/column/jobs")
def list_column_jobs(limit: int = 10):
    """最近的任务列表"""
    return {"jobs": zhihu_column.list_jobs(limit=limit)}


@router.get("/cookie")
def get_cookie_status():
    """查询知乎 Cookie 状态"""
    return zhihu_column.cookie_status()


@router.post("/cookie")
def save_cookie(req: CookieSaveRequest):
    """保存知乎 Cookie 到本地"""
    try:
        zhihu_column.save_cookie(req.zC0, req.dC0 or "")
        return {"success": True, **zhihu_column.cookie_status()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
