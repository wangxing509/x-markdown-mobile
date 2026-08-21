import { useMemo, useState, useCallback } from 'react'
import { RefreshCw, Flame, ChevronRight } from 'lucide-react'
import { useAppStore } from '../store'
import { usePullRefresh } from '../lib/usePullRefresh'
import { loadIndex } from '../lib/data'
import type { SiteIndex, Top100Item, Category, Domain, Lang } from '../lib/types'

const categories: Array<{ id: Category | null; name: string }> = [
  { id: null, name: '全部' },
  { id: 'article', name: '文章' },
  { id: 'tutorial', name: '教程' },
  { id: 'application', name: '应用' },
]
const domains: Array<{ id: Domain | null; name: string }> = [
  { id: null, name: '通用' },
  { id: 'ai_audit', name: 'AI×审计' },
]
const langs: Array<{ id: Lang | null; name: string }> = [
  { id: null, name: '中/英' },
  { id: 'cn', name: '中文' },
  { id: 'en', name: '英文' },
]

export function Top100View({
  index,
  loading,
  onToast,
}: {
  index: SiteIndex | null
  loading: boolean
  onToast: (t: string, m: string) => void
  onOpenTheme: () => void
}) {
  const [cat, setCat] = useState<Category | null>(null)
  const [dom, setDom] = useState<Domain | null>(null)
  const [lang, setLang] = useState<Lang | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const setReader = useAppStore((s) => s.setTab)

  const openArticle = useCallback(
    (item: Top100Item) => {
      sessionStorage.setItem('xmd-reader-item', JSON.stringify(item))
      setReader('reader')
    },
    [setReader]
  )

  const doRefresh = useCallback(async () => {
    setRefreshing(true)
    try {
      const d = await loadIndex({ force: true })
      onToast('success', '已刷新最新内容')
      return d
    } catch {
      onToast('error', '刷新失败，请检查网络')
      return null
    } finally {
      setRefreshing(false)
    }
  }, [onToast])

  const { pullRef, pulling, distance } = usePullRefresh(doRefresh)

  const filtered = useMemo(() => {
    if (!index) return []
    return index.top100.filter((it) => {
      if (cat && it.category !== cat) return false
      if (dom && it.domain !== dom) return false
      if (lang && it.lang !== lang) return false
      return true
    })
  }, [index, cat, dom, lang])

  const stats = index?.stats

  return (
    <div ref={pullRef} className="flex h-full flex-col overflow-y-auto overscroll-contain">
      {/* 下拉刷新指示 */}
      <div
        className="flex items-center justify-center gap-2 text-xs text-slate-400 transition-transform"
        style={{ height: distance ? `${distance}px` : '0px', transform: `translateY(${distance ? 0 : 0}px)` }}
      >
        {pulling && (
          <span className="flex items-center gap-1.5">
            <RefreshCw size={14} className="pull-spinner" />
            {distance >= 70 ? '松开刷新' : '下拉刷新'}
          </span>
        )}
      </div>

      {/* 顶部标题 */}
      <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/90 px-4 pb-3 pt-4 backdrop-blur">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-500">
              <Flame size={18} className="text-white" />
            </span>
            <div>
              <h1 className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-lg font-bold text-transparent">
                X-markdown
              </h1>
              <p className="text-[11px] text-slate-500">每日 AI 精选 · 知识库</p>
            </div>
          </div>
          <button
            onClick={() => doRefresh()}
            disabled={refreshing}
            className="flex items-center gap-1 rounded-full bg-blue-600/20 px-3 py-1.5 text-xs font-medium text-blue-300 active:bg-blue-600/40"
          >
            <RefreshCw size={13} className={refreshing ? 'pull-spinner' : ''} />
            {refreshing ? '刷新中' : '刷新'}
          </button>
        </div>
      </header>

      {/* 统计条 */}
      {stats && (
        <div className="flex items-center gap-3 border-b border-slate-800/70 bg-slate-900/40 px-4 py-2 text-[11px] text-slate-400">
          <span>
            今日 <b className="text-blue-300">{stats.total}</b>/{stats.target}
          </span>
          <span>
            英 <b className="text-violet-300">{stats.en}</b> / 中 <b className="text-cyan-300">{stats.cn}</b>
          </span>
          <span>
            审计 <b className="text-amber-300">{stats.audit}</b>
          </span>
          <span className="ml-auto text-slate-600">
            {index?.generatedAt ? `更新 ${fmtTime(index.generatedAt)}` : ''}
          </span>
        </div>
      )}

      {/* 筛选 chips */}
      <div className="no-select flex items-center gap-1.5 overflow-x-auto border-b border-slate-800/70 bg-slate-900/20 px-3 py-2">
        {domains.map((d) => (
          <Chip key={d.id ?? 'd'} active={dom === d.id} onClick={() => setDom(d.id)}>
            {d.name}
          </Chip>
        ))}
        <Divider />
        {langs.map((l) => (
          <Chip key={l.id ?? 'l'} active={lang === l.id} onClick={() => setLang(l.id)}>
            {l.name}
          </Chip>
        ))}
        <Divider />
        {categories.map((c) => (
          <Chip key={c.id ?? 'c'} active={cat === c.id} onClick={() => setCat(c.id)}>
            {c.name}
          </Chip>
        ))}
      </div>

      {/* 列表 */}
      <div className="flex-1 px-3 py-2">
        {loading && !index ? (
          <div className="py-16 text-center text-sm text-slate-500">加载中…</div>
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center text-sm text-slate-500">暂无内容，下拉或点右上角刷新</div>
        ) : (
          <div className="space-y-2">
            {filtered.map((it) => (
              <Top100Card key={it.id} item={it} onOpen={() => openArticle(it)} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium transition ${
        active ? 'bg-blue-600 text-white' : 'bg-slate-800/70 text-slate-300'
      }`}
    >
      {children}
    </button>
  )
}

function Divider() {
  return <span className="mx-0.5 h-4 w-px shrink-0 bg-slate-700" />
}

function fmtTime(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const catColor: Record<string, string> = {
  article: 'text-blue-300 bg-blue-500/15',
  tutorial: 'text-emerald-300 bg-emerald-500/15',
  application: 'text-rose-300 bg-rose-500/15',
}
const catName: Record<string, string> = { article: '文章', tutorial: '教程', application: '应用' }

function Top100Card({ item, onOpen }: { item: Top100Item; onOpen: () => void }) {
  return (
    <div
      onClick={onOpen}
      className="fade-in rounded-2xl border border-slate-800 bg-slate-900/60 p-3.5 active:scale-[0.99] active:bg-slate-900"
    >
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500/25 to-purple-500/25 text-sm font-bold text-blue-300">
          {item.rank}
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="line-clamp-2 text-[15px] font-semibold leading-snug text-slate-100">{item.title}</h3>
          {item.summary && <p className="mt-1 line-clamp-2 text-[13px] text-slate-400">{item.summary}</p>}
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <span className={`rounded px-1.5 py-0.5 text-[10px] ${catColor[item.category]}`}>{catName[item.category]}</span>
            {item.domain === 'ai_audit' && (
              <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] text-amber-300">AI×审计</span>
            )}
            {item.lang && (
              <span className={`rounded px-1.5 py-0.5 text-[10px] ${item.lang === 'en' ? 'bg-violet-500/15 text-violet-300' : 'bg-cyan-500/15 text-cyan-300'}`}>
                {item.lang === 'en' ? 'EN' : '中'}
              </span>
            )}
            <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-500">{item.source}</span>
            <span className="ml-auto flex items-center gap-0.5 text-amber-400">
              {item.score.toFixed(1)}
              <ChevronRight size={14} className="text-slate-600" />
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
