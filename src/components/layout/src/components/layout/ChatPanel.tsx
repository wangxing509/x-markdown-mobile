import { MessageSquare, Send, Trash2, Bot, User } from 'lucide-react'
import { useChat } from '@/hooks/useChat'
import { useSettings } from '@/hooks/useSettings'
import { useStore } from '@/stores/useStore'
import { useRef, useEffect, useState } from 'react'

export function ChatPanel() {
  const { messages, loading, send, clear, agentId, agents, setAgentId, references } = useChat()
  const { llmAvailable, setLlmAvailable } = useStore()
  const { loadAll } = useSettings()
  const [input, setInput] = useState('')
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    void loadAll()
  }, [loadAll])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    // 检测 LLM 状态
    if (window.xmarkdown?.llmStatus) {
      window.xmarkdown.llmStatus().then((status) => setLlmAvailable(status.available))
    }
  }, [setLlmAvailable])

  const handleSend = async () => {
    if (!input.trim() || loading) return
    const msg = input.trim()
    setInput('')
    await send(msg)
  }

  return (
    <aside className="flex h-full w-80 flex-col border-l border-slate-700/50 bg-slate-900/80 backdrop-blur-xl">
      {/* 标题 */}
      <div className="flex items-center gap-2 border-b border-slate-700/50 px-4 py-3">
        <MessageSquare size={18} className="text-blue-400" />
        <span className="font-semibold text-slate-100">Chat 对话</span>
        <button
          onClick={clear}
          className="ml-auto rounded p-1 text-slate-400 hover:bg-slate-700/50 hover:text-slate-200 transition cursor-pointer"
          title="清空对话"
        >
          <Trash2 size={14} />
        </button>
      </div>

      {/* LLM 状态指示 */}
      <div className="flex items-center gap-1.5 border-b border-slate-700/30 px-4 py-1.5 text-xs">
        <span className={`h-1.5 w-1.5 rounded-full ${llmAvailable ? 'bg-emerald-400' : 'bg-amber-400'}`} />
        <span className={llmAvailable ? 'text-emerald-400' : 'text-amber-400'}>
          {llmAvailable ? 'LLM 已连接' : 'LLM 未就绪（需启动 IDE 或 Ollama）'}
        </span>
      </div>

      {/* 子 Agent 选择 */}
      <div className="border-b border-slate-700/30 px-4 py-1.5">
        <select
          value={agentId}
          onChange={(e) => setAgentId(e.target.value)}
          className="w-full cursor-pointer rounded-md border border-slate-600/50 bg-slate-800/60 px-2 py-1.5 text-xs text-slate-200 outline-none"
          title="选择子 Agent（检索范围与回答风格不同）"
        >
          {agents.length === 0 && <option value="general_ai">通用AI资讯助手</option>}
          {agents.map((a) => (
            <option key={a.id} value={a.id} title={a.desc}>
              {a.name}
            </option>
          ))}
        </select>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
        {messages.length === 0 ? (
          <div className="py-12 text-center text-sm text-slate-500">
            <Bot size={28} className="mx-auto mb-2 opacity-40" />
            <p>向 AI 提问，或检索知识库</p>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                msg.role === 'user' ? 'bg-blue-600/20 text-blue-400' : 'bg-purple-600/20 text-purple-400'
              }`}>
                {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
              </div>
              <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                msg.role === 'user'
                  ? 'bg-blue-600/20 text-slate-100'
                  : 'bg-slate-700/40 text-slate-200'
              }`}>
                <p className="whitespace-pre-wrap break-words">{msg.content}</p>
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex gap-2">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-purple-600/20 text-purple-400">
              <Bot size={14} className="animate-pulse" />
            </div>
            <div className="rounded-lg bg-slate-700/40 px-3 py-2 text-sm text-slate-400">
              思考中...
            </div>
          </div>
        )}
        {!loading && references.length > 0 && (
          <div className="rounded-lg border border-slate-700/40 bg-slate-800/30 px-3 py-2 text-[11px] text-slate-400">
            <p className="mb-1 font-medium text-slate-300">引用文章</p>
            {references.map((r) => (
              <p key={r} className="truncate py-0.5">• {r}</p>
            ))}
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* 输入框 */}
      <div className="border-t border-slate-700/50 p-3">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            placeholder="输入问题，Enter 发送..."
            rows={2}
            className="flex-1 resize-none rounded-lg bg-slate-800/60 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 border border-slate-700/50 focus:border-blue-500/50 focus:outline-none focus:ring-1 focus:ring-blue-500/30 transition"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="card-hover flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition cursor-pointer"
          >
            <Send size={15} />
          </button>
        </div>
      </div>
    </aside>
  )
}
