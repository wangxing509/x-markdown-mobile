import { useCallback } from 'react'
import { useStore } from '@/stores/useStore'
import { api } from '@/api/client'

export function useChat() {
  const {
    chatMessages,
    chatLoading,
    chatAgentId,
    chatReferences,
    agents,
    addChatMessage,
    setChatLoading,
    setChatAgentId,
    setChatReferences,
    clearChat,
  } = useStore()

  const send = useCallback(async (message: string) => {
    const userMsg = {
      role: 'user' as const,
      content: message,
      timestamp: new Date().toISOString(),
    }
    addChatMessage(userMsg)
    setChatLoading(true)
    try {
      const agent = agents.find((a) => a.id === chatAgentId)
      const res = await api.chat(message, chatAgentId, agent?.systemPrompt)
      addChatMessage({
        role: 'assistant',
        content: res.reply,
        timestamp: new Date().toISOString(),
      })
      setChatReferences(res.references ?? [])
      return res
    } catch (e) {
      const errMsg = (e as Error).message
      addChatMessage({
        role: 'assistant',
        content: `[错误] ${errMsg}`,
        timestamp: new Date().toISOString(),
      })
      return null
    } finally {
      setChatLoading(false)
    }
  }, [chatAgentId, agents, addChatMessage, setChatLoading, setChatReferences])

  return {
    messages: chatMessages,
    loading: chatLoading,
    agentId: chatAgentId,
    agents,
    references: chatReferences,
    send,
    setAgentId: setChatAgentId,
    clear: clearChat,
  }
}
