import type {
  Top100Response,
  Top100Stats,
  RefreshResponse,
  MarkdownConvertResponse,
  SubtitleConvertResponse,
  TranslateResponse,
  DistillResponse,
  ChatResponse,
  ChatReference,
  Category,
  Domain,
  Lang,
  ProxyConfig,
  KnowledgeBaseItem,
  KbSearchResult,
  KbTreeInfo,
  ZhihuColumnJob,
  ZhihuColumnStartResponse,
  ZhihuCookieStatus,
  ZhihuColumnInfo,
  KbIndexInfo,
  AgentConfig,
  Settings,
  LlmConfig,
  SourceConfig,
  RefreshLogItem,
} from '@/types'

const BASE = 'http://127.0.0.1:8765'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${path} 失败 (${res.status}): ${text}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  // 每日精选
  getTop100: (category?: Category, domain?: Domain, lang?: Lang) => {
    const params = new URLSearchParams()
    if (category) params.set('category', category)
    if (domain) params.set('domain', domain)
    if (lang) params.set('lang', lang)
    const qs = params.toString()
    return request<Top100Response>(`/api/top100${qs ? `?${qs}` : ''}`)
  },

  refresh: () =>
    request<RefreshResponse>('/api/refresh', { method: 'POST' }),

  refreshLogs: (limit = 5) =>
    request<{ logs: RefreshLogItem[] }>(`/api/refresh-logs?limit=${limit}`),

  // Markdown 转换
  convertUrl: (url: string) =>
    request<MarkdownConvertResponse>('/api/md/convert', {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),

  convertSubtitle: (videoUrl: string) =>
    request<SubtitleConvertResponse>('/api/md/subtitle', {
      method: 'POST',
      body: JSON.stringify({ videoUrl }),
    }),

  // 翻译：优先 Electron LLM 桥接，桥接不可用/失败时降级到后端 MyMemory
  translate: async (text: string, targetLang = 'zh-CN') => {
    if (window.xmarkdown?.llmTranslate) {
      try {
        const translated = await window.xmarkdown.llmTranslate(text, targetLang)
        if (translated && translated.trim()) {
          return { translated } as TranslateResponse
        }
        // 空结果也降级
        throw new Error('LLM 桥接返回空')
      } catch (e) {
        console.warn('[翻译] Electron LLM 桥接失败，降级到后端 MyMemory:', (e as Error).message)
      }
    }
    // 后端 MyMemory fallback（永远可用）：后端返回 {results: [{original, translated}]}
    const res = await request<{ results?: Array<{ translated: string }>; translated?: string }>(
      '/api/translate',
      {
        method: 'POST',
        body: JSON.stringify({ texts: [text], target_lang: targetLang }),
      }
    )
    const translated =
      res.translated ||
      (Array.isArray(res.results) && res.results[0] ? res.results[0].translated : '') ||
      ''
    if (!translated.trim()) {
      throw new Error('后端翻译返回为空')
    }
    return { translated } as TranslateResponse
  },

  // Skill 蒸馏（走 Electron LLM 桥接）
  distill: async (text: string, skillName: string) => {
    if (window.xmarkdown?.llmDistill) {
      const content = await window.xmarkdown.llmDistill(text, skillName)
      const skillPath = await window.xmarkdown.exportSkill(skillName, content)
      return { skillName, content, skillPath } as DistillResponse
    }
    return request<DistillResponse>('/api/distill', {
      method: 'POST',
      body: JSON.stringify({ text, skillName }),
    })
  },

  // 知识库
  listKnowledgeBase: async (): Promise<KnowledgeBaseItem[]> => {
    const res = await request<{ items: KnowledgeBaseItem[] }>('/api/kb')
    return res.items
  },

  saveToKnowledgeBase: (payload: {
    url: string
    title: string
    originalMd: string
    translatedMd?: string
    domain: Domain
    category?: Category
    lang?: Lang
    source?: string
    tags?: string[]
    force?: boolean
  }) =>
    request<{
      success: boolean
      duplicate: boolean
      id?: number
      originalPath: string
      translatedPath: string
      message: string
    }>('/api/kb/save', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Chat（走 Electron LLM 桥接）
  chat: async (message: string, agentId = 'general_ai', systemPrompt = '') => {
    // 由后端构建子 Agent 检索上下文与引用
    const kbRes = await request<{ context: string; references: ChatReference[] }>('/api/chat/context', {
      method: 'POST',
      body: JSON.stringify({ message, agentId }),
    }).catch(() => null)
    const context = kbRes?.context ?? ''
    const references = kbRes?.references ?? []
    if (window.xmarkdown?.llmChat) {
      try {
        const reply = await window.xmarkdown.llmChat(message, context, systemPrompt || undefined)
        return { reply, references: references.map((r) => r.name) } as ChatResponse
      } catch (e) {
        // LLM 桥接不可用/失败时降级到后端回复，保证检索结果与引用仍然可见
        console.warn('[Chat] Electron LLM 桥接失败，降级到后端回复:', (e as Error).message)
      }
    }
    return request<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message, context: agentId }),
    })
  },

  // 知识库全文检索（FTS5 + jieba，支持过滤）
  searchKnowledgeBase: (query: string, filters?: { domain?: string; lang?: string; category?: string }) =>
    request<{ results: KbSearchResult[] }>(`/api/kb/search?q=${encodeURIComponent(query)}` +
      (filters?.domain ? `&domain=${filters.domain}` : '') +
      (filters?.lang ? `&lang=${filters.lang}` : '') +
      (filters?.category ? `&category=${filters.category}` : '')),

  // Bright Data：配置 / 失败页面 / 重试 / 单页抓取
  brightdataConfig: () =>
    request<{ enabled: boolean; zone: string; hasApiKey: boolean; apiKeyMasked: string }>(
      '/api/brightdata/config'
    ),

  saveBrightdataConfig: (payload: { enabled?: boolean; apiKey?: string; zone?: string }) =>
    request<{ enabled: boolean; zone: string; hasApiKey: boolean; apiKeyMasked: string }>(
      '/api/brightdata/config',
      { method: 'POST', body: JSON.stringify(payload) }
    ),

  brightdataFailed: () =>
    request<{
      items: Array<{
        url: string
        title?: string
        source?: string
        first_failed_at?: string
        last_error?: string
        retried?: boolean
        last_success_at?: string
      }>
      count: number
    }>('/api/brightdata/failed'),

  brightdataRetry: (urls?: string[]) =>
    request<{
      success: boolean
      results: Array<{ url: string; success: boolean; title: string; error: string }>
      succeeded: number
      failed: number
    }>('/api/brightdata/retry', {
      method: 'POST',
      body: JSON.stringify({ urls: urls ?? [] }),
    }),

  brightdataFetch: (url: string) =>
    request<MarkdownConvertResponse>('/api/brightdata/fetch', {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),

  // 子 Agent
  getAgents: () =>
    request<AgentConfig[]>('/api/agents'),

  saveAgents: (agents: AgentConfig[]) =>
    request<AgentConfig[]>('/api/agents', {
      method: 'POST',
      body: JSON.stringify(agents),
    }),

  // 设置
  getSettings: () =>
    request<Settings>('/api/settings'),

  saveSettings: (settings: Partial<Settings>) =>
    request<Settings>('/api/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    }),

  // LLM 翻译通道
  getLlmConfig: () =>
    request<LlmConfig>('/api/llm-config'),

  saveLlmConfig: (cfg: Partial<LlmConfig>) =>
    request<LlmConfig>('/api/llm-config', {
      method: 'POST',
      body: JSON.stringify(cfg),
    }),

  // 来源启停
  getSources: () =>
    request<SourceConfig[]>('/api/sources'),

  toggleSource: (name: string, enabled: boolean) =>
    request<{ success: boolean; sources: SourceConfig[] }>('/api/sources/toggle', {
      method: 'POST',
      body: JSON.stringify({ name, enabled }),
    }),

  // 健康检查
  health: () => request<{ status: string; timestamp: string }>('/api/health'),

  // 代理配置（优先走 Electron 本地文件；后端兜底）
  getProxy: () =>
    request<ProxyConfig>('/api/proxy'),

  setProxy: (enabled: boolean, url: string) =>
    request<ProxyConfig>('/api/proxy', {
      method: 'POST',
      body: JSON.stringify({ enabled, url }),
    }),

  // ==================== 知乎专栏下载 ====================
  zhihuStart: (payload: {
    columnId: string
    outputDir?: string
    downloadVideos?: boolean
    maxItems?: number
    autoImport?: boolean
  }) =>
    request<ZhihuColumnStartResponse>('/api/zhihu/column/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  zhihuStatus: (jobId: string) =>
    request<ZhihuColumnJob>(`/api/zhihu/column/status/${encodeURIComponent(jobId)}`),

  zhihuJobs: () =>
    request<{ jobs: ZhihuColumnJob[] }>('/api/zhihu/column/jobs'),

  zhihuColumnInfo: (columnId: string) =>
    request<ZhihuColumnInfo>('/api/zhihu/column/info', {
      method: 'POST',
      body: JSON.stringify({ columnId }),
    }),

  zhihuCookie: () =>
    request<ZhihuCookieStatus>('/api/zhihu/cookie'),

  zhihuSaveCookie: (zC0: string) =>
    request<ZhihuCookieStatus>('/api/zhihu/cookie', {
      method: 'POST',
      body: JSON.stringify({ zC0 }),
    }),

  // ==================== 知识库删除 ====================
  deleteKnowledgeBase: (payload: { ids?: number[]; paths?: string[] }) =>
    request<{ success: boolean; deleted: number }>('/api/kb/delete', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // ==================== 知识库索引（作者 + 主题） ====================
  getKbIndex: (force = false) =>
    request<KbIndexInfo>(`/api/kb/index${force ? '?force=true' : ''}`),

  rebuildKbIndex: () =>
    request<KbIndexInfo>('/api/kb/index?force=true'),

  // 知识库目录树（聚合类别 → 主题 → 作者 → 文章）
  getKbTree: () =>
    request<KbTreeInfo>('/api/kb/tree'),

  // ==================== 一键同步手机端 ====================
  syncSiteStatus: () =>
    request<{
      root: string
      mobileExists: boolean
      python: boolean
      npm: boolean
      git: boolean
    }>('/api/sync/site/status'),

  syncSite: (payload?: { repo?: string; push?: boolean }) =>
    request<{
      success: boolean
      exported: boolean
      built: boolean
      pushed: boolean
      errors: string[]
    }>('/api/sync/site', {
      method: 'POST',
      body: JSON.stringify(payload ?? { push: false }),
    }),
}
