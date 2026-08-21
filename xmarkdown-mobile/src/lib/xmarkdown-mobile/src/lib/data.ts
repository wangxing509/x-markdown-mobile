// 数据加载层：从 GitHub Pages 上的静态 JSON / MD 读取数据
// 支持缓存、自动刷新（轮询 + 可见性）+ 手动刷新
import type { SiteIndex, KbMeta, KbArticle } from './types'

const DATA_BASE = './data'
const CACHE_KEY = 'xmd-index-cache'
let lastFetched = 0

async function fetchJson<T>(path: string, opts?: { noCache?: boolean }): Promise<T> {
  const url = `${DATA_BASE}/${path}`
  const cacheBust = opts?.noCache ? `?t=${Date.now()}` : ''
  const res = await fetch(`${url}${cacheBust}`, { cache: 'no-cache' })
  if (!res.ok) throw new Error(`加载 ${path} 失败 (${res.status})`)
  return res.json() as Promise<T>
}

export async function loadIndex(opts?: { force?: boolean }): Promise<SiteIndex> {
  // 优先本地缓存（快速首屏），随后尝试网络最新
  if (!opts?.force && Date.now() - lastFetched < 8000) {
    // 命中内存缓存
  }
  try {
    const data = await fetchJson<SiteIndex>('index.json')
    lastFetched = Date.now()
    return data
  } catch (e) {
    // 离线回退到 localStorage 缓存
    const cached = localStorage.getItem(CACHE_KEY)
    if (cached) return JSON.parse(cached) as SiteIndex
    throw e
  }
}

export async function loadKbList(): Promise<KbMeta[]> {
  return fetchJson<KbMeta[]>('kb.json')
}

const CHUNK_SIZE = 120
const chunkCache = new Map<string, Record<string, KbArticle>>()

export async function loadArticle(id: number): Promise<KbArticle> {
  const chunk = Math.floor(id / CHUNK_SIZE) // id 从 0 开始，c0 含 id 0-119, c1 含 120-239 ...
  const chunkFile = `articles/c${chunk}.json`
  let data = chunkCache.get(chunkFile)
  if (!data) {
    data = await fetchJson<Record<string, KbArticle>>(chunkFile)
    chunkCache.set(chunkFile, data)
  }
  const entry = data[String(id)]
  if (!entry) throw new Error(`文章 ${id} 不存在`)
  return { meta: { id }, original: entry.original, translated: entry.translated || undefined }
}

export function getGeneratedHint(index: SiteIndex | null): string {
  if (!index?.generatedAt) return ''
  return index.generatedAt
}

export function refreshKeyFor(index: SiteIndex | null): string {
  return index?.generatedAt ?? ''
}

// 自动刷新：每 60s 探测一次数据是否更新；页面可见时立即探测
export function startAutoRefresh(onNew: () => void, intervalMs = 60000) {
  const timer = setInterval(() => onNew(), intervalMs)
  const onVisible = () => {
    if (document.visibilityState === 'visible') onNew()
  }
  document.addEventListener('visibilitychange', onVisible)
  return () => {
    clearInterval(timer)
    document.removeEventListener('visibilitychange', onVisible)
  }
}
