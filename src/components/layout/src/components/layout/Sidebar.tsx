import {
  BookOpenText,
  CheckSquare,
  ChevronDown,
  ChevronRight,
  FileText,
  FolderOpen,
  FolderTree,
  Layers,
  ListChecks,
  MinusSquare,
  RefreshCw,
  Search,
  Square,
  Trash2,
  User,
  X,
} from 'lucide-react'
import { useKnowledgeBase } from '@/hooks/useKnowledgeBase'
import { useStore } from '@/stores/useStore'
import { api } from '@/api/client'
import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type {
  Category,
  Domain,
  KbSearchResult,
  KbTreeCategory,
  KbTreeInfo,
  KnowledgeBaseItem,
  Lang,
} from '@/types'

function toast(type: 'success' | 'error' | 'info', message: string) {
  window.dispatchEvent(new CustomEvent('xmarkdown:toast', { detail: { type, message } }))
}

// ==================== 模糊匹配工具 ====================

function normalize(s: string): string {
  return (s || '')
    .toLowerCase()
    .replace(/[\s\-_·.,，。！？、；："'()（）[\]{}《》【】/\\:+]+/g, '')
}

function isSubsequence(q: string, text: string): boolean {
  if (!q) return true
  let i = 0
  for (const ch of text) {
    if (ch === q[i]) i += 1
    if (i === q.length) return true
  }
  return i === q.length
}

/** 模糊匹配打分：完全一致 > 子串 > 多词全命中 > 子序列（容忍漏字/错字） */
function fuzzyScore(query: string, text: string): number {
  const q = normalize(query)
  const t = normalize(text)
  if (!q || !t) return -1
  if (t === q) return 100
  if (t.includes(q)) return 90 + Math.min(9, (q.length / t.length) * 10)
  const tokens = q.split(/[，,、\s]+/).filter(Boolean)
  if (tokens.length > 1 && tokens.every((tok) => tok && t.includes(tok))) {
    return 70 + Math.min(15, tokens.length * 3)
  }
  if (isSubsequence(q, t)) return 45 + (q.length / Math.max(t.length, 1)) * 25
  return -1
}

// ==================== 树形数据工具 ====================

interface FlatEntry {
  item: KnowledgeBaseItem
  author: string
  topic: string
  categoryLabel: string
  categoryKey: string
}

function flattenTree(tree: KbTreeInfo | null): FlatEntry[] {
  if (!tree) return []
  const out: FlatEntry[] = []
  for (const cat of tree.categories) {
    for (const topic of cat.topics) {
      for (const author of topic.authors) {
        for (const item of author.items) {
          out.push({
            item,
            author: author.author,
            topic: topic.topic,
            categoryLabel: cat.label,
            categoryKey: cat.key,
          })
        }
      }
    }
  }
  return out
}

function categoryItemPaths(cat: KbTreeCategory): string[] {
  return cat.topics.flatMap((t) => t.authors.flatMap((a) => a.items.map((i) => i.path)))
}

function topicItemPaths(topic: KbTreeCategory['topics'][number]): string[] {
  return topic.authors.flatMap((a) => a.items.map((i) => i.path))
}

function authorItemPaths(author: KbTreeCategory['topics'][number]['authors'][number]): string[] {
  return author.items.map((i) => i.path)
}

function treeKeys(tree: KbTreeInfo | null, levels: 'all' | 'top' = 'all'): string[] {
  if (!tree) return []
  const keys: string[] = []
  for (const cat of tree.categories) {
    keys.push(`cat:${cat.key}`)
    if (levels === 'top') continue
    for (const t of cat.topics) {
      keys.push(`topic:${cat.key}|${t.topic}`)
      for (const a of t.authors) {
        keys.push(`author:${cat.key}|${t.topic}|${a.author}`)
      }
    }
  }
  return keys
}

// ==================== 行组件 ====================

interface NodeRowProps {
  icon: ReactNode
  label: string
  count: number
  indent: number
  expanded: boolean
  managing: boolean
  checkState: 'all' | 'some' | 'none'
  onToggleExpand: () => void
  onToggleSelect: () => void
}

function NodeRow({
  icon,
  label,
  count,
  indent,
  expanded,
  managing,
  checkState,
  onToggleExpand,
  onToggleSelect,
}: NodeRowProps) {
  return (
    <div
      className="group flex items-center gap-1 rounded-md py-1 pr-2 transition hover:bg-slate-700/30"
      style={{ paddingLeft: `${6 + indent * 14}px` }}
    >
      {managing && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            onToggleSelect()
          }}
          className="shrink-0 rounded p-0.5 text-slate-400 transition hover:text-blue-300 cursor-pointer"
          title="选择/取消此分组下全部文章"
        >
          {checkState === 'all' ? (
            <CheckSquare size={14} className="text-blue-400" />
          ) : checkState === 'some' ? (
            <MinusSquare size={14} className="text-blue-300" />
          ) : (
            <Square size={14} />
          )}
        </button>
      )}
      <button
        onClick={onToggleExpand}
        className="flex min-w-0 flex-1 items-center gap-1.5 text-left transition cursor-pointer"
      >
        {expanded ? (
          <ChevronDown size={14} className="shrink-0 text-slate-500" />
        ) : (
          <ChevronRight size={14} className="shrink-0 text-slate-500" />
        )}
        {icon}
        <span className="truncate text-xs font-medium text-slate-300 group-hover:text-white">
          {label}
        </span>
        <span className="ml-auto shrink-0 rounded bg-slate-700/60 px-1 text-[10px] text-slate-400">
          {count}
        </span>
      </button>
    </div>
  )
}

interface ItemRowProps {
  item: KnowledgeBaseItem
  author?: string
  topic?: string
  snippet?: string
  contentHit?: boolean
  managing: boolean
  selected: boolean
  indent: number
  onToggleSelect: (path: string) => void
  onOpen: (item: KnowledgeBaseItem) => void
  onDelete: (item: KnowledgeBaseItem) => void
}

function ItemRow({
  item,
  author,
  topic,
  snippet,
  contentHit,
  managing,
  selected,
  indent,
  onToggleSelect,
  onOpen,
  onDelete,
}: ItemRowProps) {
  return (
    <div
      onClick={() => (managing ? onToggleSelect(item.path) : onOpen(item))}
      className={`group relative w-full rounded-md py-1.5 pr-2 text-left transition cursor-pointer ${
        managing
          ? selected
            ? 'bg-blue-600/20'
            : 'hover:bg-slate-700/40'
          : 'hover:bg-slate-700/40'
      }`}
      style={{ paddingLeft: `${10 + indent * 14}px` }}
    >
      <div className="flex items-start gap-2">
        {managing ? (
          <span className="mt-0.5 shrink-0 text-slate-400">
            {selected ? (
              <CheckSquare size={15} className="text-blue-400" />
            ) : (
              <Square size={15} />
            )}
          </span>
        ) : (
          <FileText size={14} className="mt-0.5 shrink-0 text-slate-500 group-hover:text-blue-400" />
        )}
        <div className="min-w-0 flex-1">
          <div className={`truncate text-sm ${selected ? 'text-blue-200' : 'text-slate-200 group-hover:text-white'}`}>
            {item.name}
          </div>
          <div className="mt-0.5 flex items-center gap-1">
            {contentHit && (
              <span className="rounded bg-cyan-500/15 px-1 text-[9px] text-cyan-300">全文</span>
            )}
            {author && (
              <span className="rounded bg-violet-500/10 px-1 text-[9px] text-violet-300">
                {author}
              </span>
            )}
            {topic && (
              <span className="rounded bg-amber-500/10 px-1 text-[9px] text-amber-300/90">
                {topic}
              </span>
            )}
            {item.domain === 'ai_audit' && (
              <span className="rounded bg-amber-500/15 px-1 text-[9px] text-amber-300">AI×审计</span>
            )}
            {item.lang === 'en' && (
              <span className="rounded bg-violet-500/15 px-1 text-[9px] text-violet-300">EN</span>
            )}
            {item.hasTranslation && (
              <span className="rounded bg-emerald-500/15 px-1 text-[9px] text-emerald-300">含译文</span>
            )}
          </div>
          <div className="truncate text-xs text-slate-500">
            {snippet
              ? snippet
              : `${(item.size / 1024).toFixed(1)} KB · ${
                  item.modified ? new Date(item.modified).toLocaleDateString('zh-CN') : ''
                }`}
          </div>
        </div>
        {!managing && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDelete(item)
            }}
            className="absolute right-1.5 top-1.5 hidden rounded p-1 text-red-400 hover:bg-red-500/20 group-hover:block transition cursor-pointer"
            title="删除这篇文章"
          >
            <Trash2 size={13} />
          </button>
        )}
      </div>
    </div>
  )
}

// ==================== 主组件 ====================

interface DisplayResult {
  key: string
  item: KnowledgeBaseItem
  contentHit: KbSearchResult | null
  score: number
  author: string
  topic: string
  categoryLabel: string
}

export function Sidebar() {
  const {
    kbItems,
    kbLoading,
    kbTree,
    kbTreeLoading,
    loadKb,
    loadKbTree,
    readArticle,
    searchKb,
  } = useKnowledgeBase()
  const {
    setCurrentMarkdown,
    setWorkspaceTab,
    setCurrentArticle,
    setCurrentTranslatedMarkdown,
    setCurrentSkillMarkdown,
    setShowTranslated,
    setShowSkill,
  } = useStore()

  const [search, setSearch] = useState('')
  const [managing, setManaging] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [allExpanded, setAllExpanded] = useState(false)
  const [contentHits, setContentHits] = useState<KbSearchResult[]>([])
  const [searchBusy, setSearchBusy] = useState(false)

  const q = search.trim()

  const flatEntries = useMemo<FlatEntry[]>(() => {
    const fromTree = flattenTree(kbTree)
    if (fromTree.length) return fromTree
    return kbItems.map((i) => ({
      item: i,
      author: '',
      topic: '',
      categoryLabel: '',
      categoryKey: '',
    }))
  }, [kbTree, kbItems])

  const allPaths = useMemo(() => flatEntries.map((e) => e.item.path), [flatEntries])

  // 目录树加载后默认展开「聚合类别」层
  useEffect(() => {
    if (!kbTree) return
    setExpanded((prev) => {
      const next = new Set(prev)
      let changed = false
      for (const key of treeKeys(kbTree, 'top')) {
        if (!next.has(key)) {
          next.add(key)
          changed = true
        }
      }
      return changed ? next : prev
    })
  }, [kbTree])

  const handleOpen = async (item: {
    path: string
    name: string
    source?: string
    category?: Category
    domain?: Domain
    lang?: Lang
  }) => {
    const { path, name } = item
    const content = await readArticle(path)
    if (content) {
      setCurrentTranslatedMarkdown('')
      setCurrentSkillMarkdown('')
      setShowTranslated(false)
      setShowSkill(false)
      setCurrentMarkdown(content)
      setWorkspaceTab('editor')
      setCurrentArticle({
        id: 0,
        rank: 0,
        title: name,
        url: path,
        summary: '',
        source: item?.source || 'knowledge-base',
        sourceAuthority: 0.5,
        publishedAt: null,
        category: item?.category || 'article',
        score: 0,
        tags: '',
        domain: item?.domain,
        lang: item?.lang,
        verified: true,
      })
    }
  }

  // ---------- 选中 / 删除 ----------

  const toggleSelect = (path: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(path)) {
        next.delete(path)
      } else {
        next.add(path)
      }
      return next
    })
  }

  const toggleSelectMany = (paths: string[]) => {
    if (!paths.length) return
    setSelected((prev) => {
      const next = new Set(prev)
      const allSelected = paths.every((p) => next.has(p))
      if (allSelected) {
        paths.forEach((p) => next.delete(p))
      } else {
        paths.forEach((p) => next.add(p))
      }
      return next
    })
  }

  const selectionState = (paths: string[]): 'all' | 'some' | 'none' => {
    if (!paths.length) return 'none'
    const count = paths.reduce((n, p) => n + (selected.has(p) ? 1 : 0), 0)
    if (count === paths.length) return 'all'
    if (count > 0) return 'some'
    return 'none'
  }

  const toggleSelectAll = () => {
    if (!allPaths.length) return
    if (allPaths.every((p) => selected.has(p))) {
      setSelected(new Set())
    } else {
      setSelected(new Set(allPaths))
    }
  }

  const doDelete = async (paths: string[], label: string) => {
    if (!paths.length) return
    const ok = window.confirm(
      `确定删除 ${label}（共 ${paths.length} 篇）？删除后文件与索引将一并移除，不可恢复。`
    )
    if (!ok) return
    try {
      const res = await api.deleteKnowledgeBase({ paths })
      toast('success', `已删除 ${res.deleted} 篇知识库文章`)
      setSelected(new Set())
      setManaging(false)
      await Promise.all([loadKb(), loadKbTree()])
      window.dispatchEvent(new CustomEvent('xmarkdown:kb-updated'))
    } catch (e) {
      toast('error', `删除失败：${(e as Error).message}`)
    }
  }

  // ---------- 模糊搜索 ----------

  const localHits = useMemo(
    () =>
      q
        ? flatEntries
            .map((entry) => {
              const { item, author, topic, categoryLabel } = entry
              const fields: Array<[string, string]> = [
                ['title', item.name],
                ['author', author],
                ['topic', topic],
                ['source', item.source || ''],
                ['category', categoryLabel],
                ['domain', item.domain || ''],
                ['lang', item.lang || ''],
              ]
              let best = -1
              let matchedField = ''
              for (const [name, text] of fields) {
                const s = fuzzyScore(q, text)
                if (s > best) {
                  best = s
                  matchedField = name
                }
              }
              return { entry, score: best, matchedField }
            })
            .filter((h) => h.score > 0)
            .sort((a, b) => b.score - a.score)
        : [],
    [q, flatEntries]
  )

  // 全文模糊检索（后端 FTS + 标题/子序列），防抖 300ms
  useEffect(() => {
    if (!q) {
      setContentHits([])
      setSearchBusy(false)
      return
    }
    setSearchBusy(true)
    const timer = setTimeout(() => {
      searchKb(q)
        .then((res) => setContentHits(res.results))
        .catch(() => setContentHits([]))
        .finally(() => setSearchBusy(false))
    }, 300)
    return () => {
      clearTimeout(timer)
      setSearchBusy(false)
    }
  }, [q, searchKb])

  const results = useMemo<DisplayResult[]>(() => {
    if (!q) return []
    const localPaths = new Set(localHits.map((h) => h.entry.item.path))
    const out: DisplayResult[] = localHits.map((h) => ({
      key: `local:${h.entry.item.path}`,
      item: h.entry.item,
      contentHit: null,
      score: h.score,
      author: h.entry.author,
      topic: h.entry.topic,
      categoryLabel: h.entry.categoryLabel,
    }))
    for (const hit of contentHits) {
      if (localPaths.has(hit.path)) continue
      out.push({
        key: `content:${hit.id}`,
        item: {
          name: hit.title,
          path: hit.path,
          size: 0,
          modified: '',
          sourceUrl: '',
          domain: (hit.domain || 'ai_general') as Domain,
          lang: (hit.lang || '') as Lang,
          category: (hit.category || 'article') as Category,
          source: hit.source,
          hasTranslation: false,
        },
        contentHit: hit,
        score: hit.score,
        author: '',
        topic: '',
        categoryLabel: '',
      })
    }
    return out.sort((a, b) => b.score - a.score).slice(0, 200)
  }, [q, localHits, contentHits])

  // ---------- 展开 / 收起 ----------

  const toggleExpand = (key: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  const toggleAllExpanded = () => {
    if (allExpanded) {
      setExpanded(new Set(treeKeys(kbTree, 'top')))
      setAllExpanded(false)
    } else {
      setExpanded(new Set(treeKeys(kbTree)))
      setAllExpanded(true)
    }
  }

  // ---------- 渲染 ----------

  const renderEmpty = (text: string) => (
    <div className="py-8 text-center text-sm text-slate-500">
      <FileText size={24} className="mx-auto mb-2 opacity-40" />
      {text}
    </div>
  )

  return (
    <aside className="flex h-full w-64 flex-col border-r border-slate-700/50 bg-slate-900/80 backdrop-blur-xl">
      {/* 标题 */}
      <div className="flex items-center gap-2 border-b border-slate-700/50 px-4 py-3">
        <FolderOpen size={18} className="text-blue-400" />
        <span className="font-semibold text-slate-100">
          {managing ? (
            <>已选 {selected.size} 篇</>
          ) : (
            <span className="flex items-center gap-1.5">
              知识库
              <span className="rounded bg-slate-700/60 px-1.5 py-0.5 text-[10px] font-normal text-slate-400">
                {kbTree?.total ?? kbItems.length} 篇
              </span>
            </span>
          )}
        </span>

        {managing ? (
          <>
            <button
              onClick={toggleSelectAll}
              className="ml-auto rounded p-1 text-slate-400 transition hover:bg-slate-700/50 hover:text-slate-200 cursor-pointer"
              title={allPaths.length && allPaths.every((p) => selected.has(p)) ? '取消全选' : '全选'}
            >
              {allPaths.length && allPaths.every((p) => selected.has(p)) ? (
                <CheckSquare size={15} />
              ) : (
                <Square size={15} />
              )}
            </button>
            <button
              onClick={() => void doDelete(Array.from(selected), '选中的文章')}
              disabled={selected.size === 0}
              className="rounded p-1 text-red-400 transition hover:bg-red-500/20 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
              title="删除选中"
            >
              <Trash2 size={15} />
            </button>
            <button
              onClick={() => {
                setManaging(false)
                setSelected(new Set())
              }}
              className="rounded p-1 text-slate-400 transition hover:bg-slate-700/50 hover:text-slate-200 cursor-pointer"
              title="退出管理"
            >
              <X size={15} />
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => {
                void loadKb()
                void loadKbTree()
              }}
              className="ml-auto rounded p-1 text-slate-400 transition hover:bg-slate-700/50 hover:text-slate-200 cursor-pointer"
              title="刷新知识库"
            >
              <RefreshCw size={14} />
            </button>
            <button
              onClick={toggleAllExpanded}
              disabled={!kbTree || kbTreeLoading}
              className="rounded p-1 text-slate-400 transition hover:bg-slate-700/50 hover:text-slate-200 cursor-pointer disabled:opacity-40"
              title={allExpanded ? '收起索引目录树' : '展开索引目录树（类别 → 主题 → 作者）'}
            >
              <BookOpenText size={15} />
            </button>
            <button
              onClick={() => {
                setManaging(true)
                setSelected(new Set())
              }}
              className="rounded p-1 text-slate-400 transition hover:bg-slate-700/50 hover:text-slate-200 cursor-pointer"
              title="批量管理（选择/删除）"
            >
              <ListChecks size={15} />
            </button>
          </>
        )}
      </div>

      {/* 模糊搜索 */}
      <div className="relative px-3 py-2">
        <Search size={14} className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-500" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="模糊搜索：标题/作者/主题/全文…"
          className="w-full rounded-md bg-slate-800/60 py-1.5 pl-7 pr-7 text-sm text-slate-200 placeholder-slate-500 border border-slate-700/50 focus:border-blue-500/50 focus:outline-none focus:ring-1 focus:ring-blue-500/30 transition"
        />
        {searchBusy && (
          <RefreshCw size={12} className="absolute right-4 top-1/2 -translate-y-1/2 animate-spin text-slate-500" />
        )}
      </div>

      {/* 列表：搜索结果 / 目录树 / 扁平兜底 */}
      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {q ? (
          results.length === 0 ? (
            !searchBusy ? renderEmpty('未找到匹配内容') : renderEmpty('搜索中…')
          ) : (
            <div className="mb-1 px-1 text-[10px] text-slate-500">
              共 {results.length} 条命中
            </div>
          )
        ) : null}

        {q ? (
          <div className="space-y-0.5">
            {results.map((r) => (
              <ItemRow
                key={r.key}
                item={r.item}
                author={r.author}
                topic={r.topic}
                snippet={r.contentHit?.snippet}
                contentHit={!!r.contentHit}
                managing={managing}
                selected={selected.has(r.item.path)}
                indent={0}
                onToggleSelect={toggleSelect}
                onOpen={(i) => void handleOpen(i)}
                onDelete={(i) => void doDelete([i.path], `《${i.name}》`)}
              />
            ))}
          </div>
        ) : kbTreeLoading && !kbTree ? (
          <div className="py-4 text-center text-sm text-slate-500">加载中…</div>
        ) : kbTree && kbTree.categories.length > 0 ? (
          <div className="space-y-0.5">
            {kbTree.categories.map((cat) => {
              const catKey = `cat:${cat.key}`
              const catOpen = expanded.has(catKey)
              return (
                <div key={catKey}>
                  <NodeRow
                    icon={<FolderTree size={14} className="shrink-0 text-blue-400" />}
                    label={cat.label}
                    count={cat.count}
                    indent={0}
                    expanded={catOpen}
                    managing={managing}
                    checkState={selectionState(categoryItemPaths(cat))}
                    onToggleExpand={() => toggleExpand(catKey)}
                    onToggleSelect={() => toggleSelectMany(categoryItemPaths(cat))}
                  />
                  {catOpen &&
                    cat.topics.map((topic) => {
                      const topicKey = `topic:${cat.key}|${topic.topic}`
                      const topicOpen = expanded.has(topicKey)
                      return (
                        <div key={topicKey}>
                          <NodeRow
                            icon={<Layers size={14} className="shrink-0 text-amber-400" />}
                            label={topic.topic}
                            count={topic.count}
                            indent={1}
                            expanded={topicOpen}
                            managing={managing}
                            checkState={selectionState(topicItemPaths(topic))}
                            onToggleExpand={() => toggleExpand(topicKey)}
                            onToggleSelect={() => toggleSelectMany(topicItemPaths(topic))}
                          />
                          {topicOpen &&
                            topic.authors.map((author) => {
                              const authorKey = `author:${cat.key}|${topic.topic}|${author.author}`
                              const authorOpen = expanded.has(authorKey)
                              return (
                                <div key={authorKey}>
                                  <NodeRow
                                    icon={<User size={14} className="shrink-0 text-violet-400" />}
                                    label={author.author}
                                    count={author.count}
                                    indent={2}
                                    expanded={authorOpen}
                                    managing={managing}
                                    checkState={selectionState(authorItemPaths(author))}
                                    onToggleExpand={() => toggleExpand(authorKey)}
                                    onToggleSelect={() => toggleSelectMany(authorItemPaths(author))}
                                  />
                                  {authorOpen &&
                                    author.items.map((item) => (
                                      <ItemRow
                                        key={item.path}
                                        item={item}
                                        author={author.author}
                                        topic={topic.topic}
                                        managing={managing}
                                        selected={selected.has(item.path)}
                                        indent={3}
                                        onToggleSelect={toggleSelect}
                                        onOpen={(i) => void handleOpen(i)}
                                        onDelete={(i) => void doDelete([i.path], `《${i.name}》`)}
                                      />
                                    ))}
                                </div>
                              )
                            })}
                        </div>
                      )
                    })}
                </div>
              )
            })}
          </div>
        ) : kbLoading ? (
          <div className="py-4 text-center text-sm text-slate-500">加载中…</div>
        ) : flatEntries.length === 0 ? (
          renderEmpty('暂无文章')
        ) : (
          <div className="space-y-0.5">
            {flatEntries.map(({ item }) => (
              <ItemRow
                key={item.path}
                item={item}
                managing={managing}
                selected={selected.has(item.path)}
                indent={0}
                onToggleSelect={toggleSelect}
                onOpen={(i) => void handleOpen(i)}
                onDelete={(i) => void doDelete([i.path], `《${i.name}》`)}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  )
}
