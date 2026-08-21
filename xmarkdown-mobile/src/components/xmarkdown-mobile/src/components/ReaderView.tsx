import { useEffect, useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { ArrowLeft, ExternalLink, Pencil, Eye, RefreshCw, Languages } from 'lucide-react'
import { useAppStore } from '../store'
import { loadArticle } from '../lib/data'
import type { Top100Item, KbArticle } from '../lib/types'

export function ReaderView({ onToast }: { onToast: (t: string, m: string) => void }) {
  const setTab = useAppStore((s) => s.setTab)
  const theme = useAppStore((s) => s.currentTheme)
  const [kb, setKb] = useState<KbArticle | null>(null)
  const [kbLoading, setKbLoading] = useState(false)
  const [editing, setEditing] = useState(false)
  const [showTranslated, setShowTranslated] = useState(false)
  const [editText, setEditText] = useState('')

  // Top100 文章（仅摘要/链接）
  const topItem = useMemo<Top100Item | null>(() => {
    const raw = sessionStorage.getItem('xmd-reader-item')
    return raw ? (JSON.parse(raw) as Top100Item) : null
  }, [])

  // KB 文章（完整内容）
  useEffect(() => {
    const raw = sessionStorage.getItem('xmd-reader-kb')
    if (raw) {
      const art = JSON.parse(raw) as KbArticle
      setKb(art)
      setEditText(art.original)
    } else {
      setKb(null)
    }
  }, [])

  // 内容决定：KB 文章优先，其次 Top100
  const isKb = !!kb
  const content = isKb ? (showTranslated && kb!.translated ? kb!.translated : kb!.original) : (topItem?.summary ?? '')

  const refreshKb = async () => {
    if (!isKb) return
    setKbLoading(true)
    try {
      const art = await loadArticle(kb!.meta.id)
      setKb(art)
      setEditText(art.original)
      onToast('success', '文章已刷新')
    } catch {
      onToast('error', '刷新失败')
    } finally {
      setKbLoading(false)
    }
  }

  const back = () => {
    sessionStorage.removeItem('xmd-reader-item')
    sessionStorage.removeItem('xmd-reader-kb')
    setTab(isKb ? 'kb' : 'top100')
  }

  const title = isKb ? kb!.meta.title : topItem?.title ?? ''

  return (
    <div className="flex h-full flex-col">
      {/* 顶栏 */}
      <header className="no-select sticky top-0 z-10 flex items-center gap-2 border-b border-slate-800 bg-slate-950/95 px-2 py-2 backdrop-blur">
        <button onClick={back} className="rounded-full p-2 text-slate-300 active:bg-slate-800">
          <ArrowLeft size={20} />
        </button>
        <h1 className="min-w-0 flex-1 truncate text-sm font-semibold text-slate-100">{title}</h1>
        {!isKb && topItem?.url && (
          <a
            href={topItem.url}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full p-2 text-blue-400 active:bg-slate-800"
          >
            <ExternalLink size={18} />
          </a>
        )}
        {isKb && (
          <>
            {kb!.translated && (
              <button
                onClick={() => setShowTranslated((v) => !v)}
                className={`flex items-center gap-1 rounded-full px-2.5 py-1.5 text-xs font-medium ${
                  showTranslated ? 'bg-emerald-600 text-white' : 'bg-emerald-600/20 text-emerald-300'
                }`}
              >
                <Languages size={13} /> {showTranslated ? '译文' : '原文'}
              </button>
            )}
            <button
              onClick={refreshKb}
              className="rounded-full p-2 text-slate-300 active:bg-slate-800"
              disabled={kbLoading}
            >
              <RefreshCw size={18} className={kbLoading ? 'pull-spinner' : ''} />
            </button>
          </>
        )}
      </header>

      {/* 编辑/预览切换（KB 文章可编辑） */}
      {isKb && (
        <div className="no-select flex items-center gap-1 border-b border-slate-800 bg-slate-900/40 px-3 py-1.5">
          <button
            onClick={() => setEditing(false)}
            className={`flex items-center gap-1 rounded-full px-3 py-1 text-xs ${!editing ? 'bg-blue-600 text-white' : 'text-slate-400'}`}
          >
            <Eye size={13} /> 阅读
          </button>
          <button
            onClick={() => setEditing(true)}
            className={`flex items-center gap-1 rounded-full px-3 py-1 text-xs ${editing ? 'bg-blue-600 text-white' : 'text-slate-400'}`}
          >
            <Pencil size={13} /> 编辑
          </button>
          <span className="ml-auto text-[10px] text-slate-600">{showTranslated ? '译文（只读）' : '原文'}</span>
        </div>
      )}

      {/* 内容区 */}
      <div className="flex-1 overflow-y-auto">
        {isKb && editing && !showTranslated ? (
          <textarea
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            className="h-full w-full resize-none bg-slate-900 p-4 font-mono text-[13px] leading-relaxed text-slate-200 outline-none"
            spellCheck={false}
          />
        ) : (
          <div className="md-render" data-theme={theme}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
              components={{
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer">
                    {children}
                  </a>
                ),
              }}
            >
              {content || '*暂无内容*'}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
