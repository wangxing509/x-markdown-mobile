import { FixedSizeList as List, ListChildComponentProps } from 'react-window'
import { useTop100 } from '@/hooks/useTop100'
import { useMarkdown } from '@/hooks/useMarkdown'
import { api } from '@/api/client'
import { Top100ItemCard } from './Top100Item'
import { RefreshButton } from './RefreshButton'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useStore } from '@/stores/useStore'
import type { Category, Top100Item, Domain, Lang } from '@/types'
import { useState } from 'react'

const categories: Array<{ id: Category | null; name: string }> = [
  { id: null, name: '全部' },
  { id: 'article', name: '文章' },
  { id: 'tutorial', name: '教程' },
  { id: 'application', name: '应用案例' },
]

const domains: Array<{ id: Domain | null; name: string }> = [
  { id: null, name: '全部领域' },
  { id: 'ai_general', name: '通用AI' },
  { id: 'ai_audit', name: 'AI×审计' },
]

const langs: Array<{ id: Lang | null; name: string }> = [
  { id: null, name: '全部语言' },
  { id: 'en', name: '英文' },
  { id: 'cn', name: '中文' },
]

function Row({ data, index, style }: ListChildComponentProps<{ items: Top100Item[]; onOpen: (i: Top100Item) => void }>) {
  const item = data.items[index]
  return (
    <div style={style}>
      <Top100ItemCard item={item} onOpen={data.onOpen} />
    </div>
  )
}

export function Top100List() {
  const {
    top100, loading, category, domain, lang, updateTime, stats,
    refreshLogs, setCategory, setDomain, setLang, fetchTop100,
  } = useTop100()
  const { fetchMarkdown } = useMarkdown()
  const [pasteUrl, setPasteUrl] = useState('')
  const [pasteDomain, setPasteDomain] = useState<Domain>('ai_general')
  const [pasteLoading, setPasteLoading] = useState(false)
  const [bdBusy, setBdBusy] = useState(false)

  const handleBrightDataRetry = async () => {
    if (bdBusy) return
    setBdBusy(true)
    try {
      const failed = await api.brightdataFailed()
      if (failed.count === 0) {
        window.dispatchEvent(new CustomEvent('xmarkdown:toast', {
          detail: { type: 'info', message: '没有已记录的失败页面' },
        }))
        return
      }
      const res = await api.brightdataRetry()
      window.dispatchEvent(new CustomEvent('xmarkdown:toast', {
        detail: {
          type: res.failed === 0 ? 'success' : 'error',
          message: `Bright Data 重试完成：成功 ${res.succeeded} 条，失败 ${res.failed} 条`,
        },
      }))
    } catch (e) {
      window.dispatchEvent(new CustomEvent('xmarkdown:toast', {
        detail: { type: 'error', message: `Bright Data 重试失败：${(e as Error).message}` },
      }))
    } finally {
      setBdBusy(false)
    }
  }

  if (top100.length === 0 && !loading) {
    void fetchTop100()
  }

  const handlePasteConvert = async () => {
    const url = pasteUrl.trim()
    if (!url || !/^https?:\/\//i.test(url)) {
      window.dispatchEvent(new CustomEvent('xmarkdown:toast', {
        detail: { type: 'error', message: '请输入有效的 http(s) 链接' },
      }))
      return
    }
    setPasteLoading(true)
    try {
      const pseudoItem: Top100Item = {
        id: -1,
        rank: 0,
        title: url,
        url,
        summary: '',
        source: '粘贴链接',
        sourceAuthority: 0.5,
        publishedAt: null,
        category: 'article',
        score: 0,
        tags: '',
        domain: pasteDomain,
        lang: url.toLowerCase().includes('.cn') || /[\u4e00-\u9fff]/.test(url) ? 'cn' : 'en',
      }
      await fetchMarkdown(pseudoItem, true)
      if (useStore.getState().currentArticle?.url === url) {
        setPasteUrl('')
        window.dispatchEvent(new CustomEvent('xmarkdown:toast', {
          detail: { type: 'success', message: '链接已转为 Markdown，进入编辑模式' },
        }))
      }
    } catch (e) {
      window.dispatchEvent(new CustomEvent('xmarkdown:toast', {
        detail: { type: 'error', message: `转换失败：${(e as Error).message}` },
      }))
    } finally {
      setPasteLoading(false)
    }
  }

  const stat = stats ?? { total: top100.length, target: 40, cn: 0, en: 0, audit: 0, general: 0, shortfall: 0 }
  const lastLog = refreshLogs[0]
  const enPct = stat.total > 0 ? Math.round((stat.en / stat.total) * 100) : 0
  const auditPct = stat.total > 0 ? Math.round((stat.audit / stat.total) * 100) : 0

  return (
    <div className="flex h-full flex-col">
      {/* 统计条 */}
      <div className="flex items-center gap-4 border-b border-slate-700/50 bg-slate-800/40 px-4 py-2 text-xs text-slate-300">
        <span>
          今日精选 <b className="text-blue-300">{stat.total}</b>/{stat.target}
          {stat.shortfall > 0 && <span className="ml-1 text-amber-400">（缺 {stat.shortfall}）</span>}
        </span>
        <span>英 <b className="text-violet-300">{stat.en}</b>（{enPct}%）/ 中 <b className="text-cyan-300">{stat.cn}</b>（{100 - enPct}%）</span>
        <span>审计×AI <b className="text-amber-300">{stat.audit}</b>（{auditPct}%）</span>
        <span className="text-emerald-400">
          验证通过 {lastLog ? lastLog.verified : '—'}
        </span>
        {updateTime && (
          <span className="ml-auto text-slate-500">更新于 {new Date(updateTime).toLocaleString('zh-CN')}</span>
        )}
        <button
          onClick={() => void handleBrightDataRetry()}
          disabled={bdBusy}
          className="shrink-0 rounded-md bg-emerald-700/70 px-2.5 py-1 text-xs text-white hover:bg-emerald-700 disabled:opacity-50 transition cursor-pointer"
          title="用 Bright Data 重新爬取之前抓取失败的页面"
        >
          {bdBusy ? '重试中...' : 'BD 重试失败页'}
        </button>
        <RefreshButton />
      </div>

      {/* 粘贴链接一键转 Markdown */}
      <div className="flex items-center gap-2 border-b border-slate-700/50 bg-slate-800/30 px-3 py-2">
        <span className="shrink-0 text-xs text-slate-400">粘贴链接</span>
        <input
          value={pasteUrl}
          onChange={(e) => setPasteUrl(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') void handlePasteConvert() }}
          placeholder="粘贴任一网页链接，一键转为 Markdown 进入编辑…"
          className="min-w-0 flex-1 rounded-md border border-slate-600/50 bg-slate-900/60 px-3 py-1.5 text-xs text-slate-200 outline-none placeholder:text-slate-500 focus:border-blue-500"
        />
        <select
          value={pasteDomain}
          onChange={(e) => setPasteDomain(e.target.value as Domain)}
          className="shrink-0 rounded-md border border-slate-600/50 bg-slate-900/60 px-2 py-1.5 text-xs text-slate-200 outline-none"
          title="标注领域（AI×审计 或 通用AI）"
        >
          <option value="ai_general">通用AI</option>
          <option value="ai_audit">AI×审计</option>
        </select>
        <button
          onClick={() => void handlePasteConvert()}
          disabled={pasteLoading}
          className="shrink-0 rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-50 cursor-pointer"
        >
          {pasteLoading ? '转换中…' : '转换'}
        </button>
      </div>

      {/* 筛选：领域 / 语言 / 分类 */}
      <div className="flex items-center gap-1.5 overflow-x-auto border-b border-slate-700/50 bg-slate-800/20 px-3 py-2">
        {domains.map((d) => (
          <button
            key={d.id ?? 'all-domain'}
            onClick={() => setDomain(d.id)}
            className={`shrink-0 rounded-md px-2.5 py-1 text-xs font-medium transition cursor-pointer ${
              domain === d.id ? 'bg-amber-600 text-white' : 'bg-slate-700/40 text-slate-300 hover:bg-slate-700/60'
            }`}
          >
            {d.name}
          </button>
        ))}
        <span className="mx-1 h-4 w-px bg-slate-700" />
        {langs.map((l) => (
          <button
            key={l.id ?? 'all-lang'}
            onClick={() => setLang(l.id)}
            className={`shrink-0 rounded-md px-2.5 py-1 text-xs font-medium transition cursor-pointer ${
              lang === l.id ? 'bg-violet-600 text-white' : 'bg-slate-700/40 text-slate-300 hover:bg-slate-700/60'
            }`}
          >
            {l.name}
          </button>
        ))}
        <span className="mx-1 h-4 w-px bg-slate-700" />
        {categories.map((cat) => (
          <button
            key={cat.name}
            onClick={() => setCategory(cat.id)}
            className={`shrink-0 rounded-md px-2.5 py-1 text-xs font-medium transition cursor-pointer ${
              category === cat.id
                ? 'bg-blue-600 text-white shadow-soft'
                : 'bg-slate-700/40 text-slate-300 hover:bg-slate-700/60'
            }`}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {/* 列表 */}
      <div className="flex-1 overflow-hidden">
        {loading && top100.length === 0 ? (
          <LoadingSpinner text="正在获取每日精选..." />
        ) : top100.length === 0 ? (
          <div className="py-12 text-center text-slate-500">
            <p className="text-sm">暂无数据</p>
            <button
              onClick={() => fetchTop100()}
              className="mt-2 text-xs text-blue-400 hover:underline cursor-pointer"
            >
              重新加载
            </button>
          </div>
        ) : (
          <List
            height={window.innerHeight - 230}
            itemCount={top100.length}
            itemSize={130}
            width="100%"
            itemData={{ items: top100, onOpen: fetchMarkdown }}
          >
            {Row}
          </List>
        )}
      </div>
    </div>
  )
}
