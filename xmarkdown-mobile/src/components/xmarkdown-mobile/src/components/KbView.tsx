import { useCallback, useEffect, useMemo, useState } from 'react'
import { Search, Library, FileText, ChevronRight, RefreshCw } from 'lucide-react'
import { useAppStore } from '../store'
import { loadKbList, loadArticle } from '../lib/data'
import type { KbMeta, KbArticle } from '../lib/types'

interface KbViewProps {
  onToast: (t: string, m: string) => void
}

export function KbView({ onToast }: KbViewProps) {
  const [list, setList] = useState<KbMeta[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [q, setQ] = useState('')
  const [langFilter, setLangFilter] = useState<'all' | 'cn' | 'en'>('all')
  const setTab = useAppStore((s) => s.setTab)

  const doLoad = useCallback(
    async (force = false) => {
      try {
        const items = await loadKbList()
        setList(items)
        setLoading(false)
        if (force) onToast('success', '知识库已刷新')
      } catch {
        setLoading(false)
        onToast('error', '知识库加载失败')
      }
    },
    [onToast]
  )

  useEffect(() => {
    doLoad()
  }, [doLoad])

  const open = useCallback(
    async (m: KbMeta) => {
      try {
        const art = await loadArticle(m.id)
        sessionStorage.setItem('xmd-reader-kb', JSON.stringify(art))
        setTab('reader')
      } catch {
        onToast('error', '文章内容加载失败')
      }
    },
    [onToast, setTab]
  )

  const filtered = useMemo(() => {
    let items = list
    if (langFilter !== 'all') items = items.filter((i) => i.lang === langFilter)
    if (q.trim()) {
      const k = q.trim().toLowerCase()
      items = items.filter(
        (i) => i.title.toLowerCase().includes(k) || i.source.toLowerCase().includes(k)
      )
    }
    return items
  }, [list, q, langFilter])

  return (
    <div className="flex h-full flex-col">
      <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/90 px-4 pb-3 pt-4 backdrop-blur">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-300">
              <Library size={18} />
            </span>
            <div>
              <h1 className="text-lg font-bold text-slate-100">知识库</h1>
              <p className="text-[11px] text-slate-500">共 {list.length} 篇收藏文章</p>
            </div>
          </div>
          <button
            onClick={() => {
              setRefreshing(true)
              doLoad(true).finally(() => setRefreshing(false))
            }}
            disabled={refreshing}
            className="flex items-center gap-1 rounded-full bg-indigo-600/20 px-3 py-1.5 text-xs font-medium text-indigo-300 active:bg-indigo-600/40"
          >
            <RefreshCw size={13} className={refreshing ? 'pull-spinner' : ''} />
            刷新
          </button>
        </div>
        <div className="relative mt-3">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="搜索标题 / 来源…"
            className="w-full rounded-xl border border-slate-800 bg-slate-900 py-2 pl-9 pr-3 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-blue-500/50"
          />
        </div>
        <div className="no-select mt-2 flex gap-1.5">
          {(['all', 'cn', 'en'] as const).map((l) => (
            <button
              key={l}
              onClick={() => setLangFilter(l)}
              className={`rounded-full px-3 py-1 text-xs ${
                langFilter === l ? 'bg-indigo-600 text-white' : 'bg-slate-800/70 text-slate-300'
              }`}
            >
              {l === 'all' ? '全部语言' : l === 'cn' ? '中文' : '英文'}
            </button>
          ))}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-3 py-2">
        {loading && list.length === 0 ? (
          <div className="py-16 text-center text-sm text-slate-500">加载中…</div>
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center text-sm text-slate-500">未找到匹配文章</div>
        ) : (
          <div className="space-y-1.5">
            {filtered.map((m) => (
              <KbRow key={m.id} m={m} onOpen={() => open(m)} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function KbRow({ m, onOpen }: { m: KbMeta; onOpen: () => void }) {
  return (
    <button
      onClick={onOpen}
      className="fade-in flex w-full items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/50 p-3 text-left active:bg-slate-900"
    >
      <FileText size={18} className="shrink-0 text-slate-500" />
      <div className="min-w-0 flex-1">
        <p className="line-clamp-2 text-[14px] font-medium leading-snug text-slate-100">{m.title}</p>
        <div className="mt-1 flex items-center gap-1.5 text-[11px] text-slate-500">
          <span>{m.source}</span>
          {m.lang === 'en' && <span className="rounded bg-violet-500/15 px-1 text-violet-300">EN</span>}
          {m.domain === 'ai_audit' && <span className="rounded bg-amber-500/15 px-1 text-amber-300">AI×审计</span>}
          {m.hasTranslation && <span className="rounded bg-emerald-500/15 px-1 text-emerald-300">译文</span>}
        </div>
      </div>
      <ChevronRight size={16} className="shrink-0 text-slate-600" />
    </button>
  )
}
