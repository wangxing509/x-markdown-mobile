# -*- coding: utf-8 -*-
"""
Chat API 端点（v2）：子 Agent 感知，后端构建知识库上下文与引用
"""
from fastapi import APIRouter, HTTPException
from models import ChatRequest, ChatResponse
from chat.knowledge_search import build_chat_context
from settings_store import get_agents

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat/context")
def chat_context(payload: dict):
    """构建子 Agent 检索上下文与引用（不调用 LLM，供 Electron 桥接使用）"""
    try:
        message = payload.get("message", "")
        agent_id = payload.get("agentId") or "general_ai"
        agent = next((a for a in get_agents() if a.get("id") == agent_id), None)
        filters = (agent or {}).get("filters") or {}
        top_k = int((agent or {}).get("topK", 5))
        context, references = build_chat_context(message, filters=filters, top_k=top_k)
        return {"context": context, "references": references, "agent": agent or {}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上下文构建失败: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """按子 Agent 检索知识库并构建上下文；LLM 回答由 Electron 主进程完成"""
    try:
        agent_id = req.context or "general_ai"
        agent = next((a for a in get_agents() if a.get("id") == agent_id), None)
        filters = (agent or {}).get("filters") or {}
        top_k = int((agent or {}).get("topK", 5))

        context, references = build_chat_context(req.message, filters=filters, top_k=top_k)

        reply = f"已收到您的问题（子 Agent：{(agent or {}).get('name', agent_id)}）：{req.message}\n\n"
        if context:
            reply += f"知识库相关内容：\n{context[:600]}\n\n"
        reply += "（完整回答需启动 CodeBuddy/WorkBuddy/Ollama 或配置 LLM API）"

        return ChatResponse(reply=reply, references=[r["name"] for r in references])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat 失败: {str(e)}")
