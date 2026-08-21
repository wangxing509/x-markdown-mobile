// X markdown 类型定义

export type Category = 'article' | 'tutorial' | 'application'

export type Domain = 'ai_general' | 'ai_audit'

export type Lang = 'cn' | 'en'

export type Platform =
  | 'WaytoAGI'
  | '魔搭ModelScope'
  | '微软AI教育社区'
  | '腾讯CodeBuddy'
  | 'DeepSeek'
  | '字节Trae'
  | 'Kimi'
  | 'GitHub'
  | 'Reddit'
  | 'Hugging Face'

export interface Top100Item {
  id: number
  rank: number
  title: string
  url: string
  summary: string
  source: string
  sourceAuthority: number
  publishedAt: string | null
  category: Category
  score: number
  tags: string
  likes?: number
  comments?: number
  author?: string
  authorFollowers?: number
  lang?: 'cn' | 'en'
  domain?: Domain
  verified?: boolean
  mdLength?: number
}

export interface Top100Stats {
  total: number
  target: number
  cn: number
  en: number
  audit: number
  general: number
  shortfall: number
  cells?: Record<string, number>
}

export interface Top100Response {
  updateTime: string
  nextRefresh: string
  items: Top100Item[]
  totalCount: number
  stats: Top100Stats
}

export interface RefreshResponse {
  success: boolean
  message: string
  rawCount?: number
  dedupCount?: number
  verifiedCount?: number
  curatedCount?: number
  enCount?: number
  cnCount?: number
  auditCount?: number
  generalCount?: number
  shortfall?: number
  stats?: Record<string, unknown>
}

export interface MarkdownConvertResponse {
  markdown: string
  title: string
  sourceUrl: string
  category: Category
}

export interface SubtitleConvertResponse {
  markdown: string
  videoTitle: string
  duration: string
}

export interface TranslateResponse {
  translated: string
}

export interface DistillResponse {
  skillName: string
  content: string
  skillPath: string
}

export interface KnowledgeBaseItem {
  name: string
  path: string
  size: number
  modified: string
  sourceUrl?: string
  domain?: Domain
  lang?: Lang
  category?: Category
  source?: string
  hasTranslation?: boolean
}

export interface KbTreeItem extends KnowledgeBaseItem {
  author: string
  topic: string
}

export interface KbTreeAuthor {
  author: string
  count: number
  items: KbTreeItem[]
}

export interface KbTreeTopic {
  topic: string
  count: number
  authors: KbTreeAuthor[]
}

export interface KbTreeCategory {
  key: string
  label: string
  domain: string
  category: string
  count: number
  topics: KbTreeTopic[]
}

export interface KbTreeInfo {
  total: number
  updatedAt: string
  categories: KbTreeCategory[]
}

export interface KbSearchResult {
  id: number
  title: string
  path: string
  domain: string
  lang: string
  category: string
  source: string
  snippet: string
  score: number
  matchType?: 'title' | 'source' | 'fuzzy' | 'content' | ''
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface ChatResponse {
  reply: string
  references: string[]
}

export interface ChatReference {
  name: string
  path: string
  snippet: string
  domain: string
  lang: string
}

export interface AgentConfig {
  id: string
  name: string
  desc: string
  systemPrompt: string
  filters: Record<string, string>
  topK: number
  temperature: number
}

export interface Settings {
  top_n: number
  en_ratio: number
  audit_ratio: number
  schedule: { enabled: boolean; hour: number; minute: number }
}

export interface LlmConfig {
  provider: 'local' | 'api'
  apiBase: string
  apiKey: string
  model: string
  temperature: number
}

export interface SourceConfig {
  name: string
  enabled: boolean
  kind: string
  authority: number
  lang: string
  audit?: boolean
  feeds?: string[]
  urls?: string[]
}

export interface RefreshLogItem {
  id: number
  startedAt: string | null
  finishedAt: string | null
  status: string
  raw: number
  dedup: number
  verified: number
  curated: number
  en: number
  cn: number
  audit: number
  general: number
  shortfall: number
  error: string
}

export type ThemeName =
  | 'minimalist-white'
  | 'tech-blue'
  | 'magazine-gray'
  | 'classic-red'
  | 'ink-green'

export interface ThemeOption {
  id: ThemeName
  name: string
  description: string
}

export const THEMES: ThemeOption[] = [
  { id: 'minimalist-white', name: '极简白', description: '白底黑字，大量留白' },
  { id: 'tech-blue', name: '科技蓝', description: '深蓝渐变背景，青色强调' },
  { id: 'magazine-gray', name: '杂志灰', description: '灰底衬线字体，杂志排版' },
  { id: 'classic-red', name: '经典红', description: '暖色调，红色标题强调' },
  { id: 'ink-green', name: '墨绿雅刊', description: '墨绿背景，古风雅致' },
]

export interface LlmStatus {
  ideDetected: boolean
  llmPort: number | null
  isOllama: boolean
  available: boolean
}

export interface ProxyConfig {
  enabled: boolean
  url: string
}

// ==================== 知乎专栏下载 ====================

export interface ZhihuColumnItem {
  type: string
  id: string
  title: string
  url: string
  created?: string
  updated?: string
  excerpt?: string
  comments?: number
  likes?: number
  author?: string
  status?: string
  error?: string
  markdownPath?: string
  videoPath?: string
}

export type ZhihuColumnJobStatus =
  | 'queued'
  | 'scanning'
  | 'downloading'
  | 'importing'
  | 'done'
  | 'error'

export interface ZhihuColumnJob {
  jobId: string
  columnId: string
  columnName: string
  resolvedFrom?: string
  status: ZhihuColumnJobStatus
  progress: number
  total: number
  currentTitle: string
  message: string
  error: string
  createdAt: string
  outputDir: string
  excelPath: string
  downloadVideos: boolean
  autoImport: boolean
  maxItems: number
  items: ZhihuColumnItem[]
  logs: string[]
  importResult?: { imported: number; skipped: number; failed: number }
}

export interface ZhihuColumnStartResponse {
  success: boolean
  jobId: string
  columnId: string
  columnName: string
  resolvedFrom?: string
}

export interface ZhihuCookieStatus {
  hasCookie: boolean
  savedAt?: string
  zC0Masked?: string
}

export interface ZhihuColumnInfo {
  columnId: string
  columnName: string
  author: string
  itemsCount: number
  description?: string
  resolvedFrom?: string
}

export interface KbIndexInfo {
  path: string
  markdown: string
  updatedAt: string
  total?: number
  authors?: Array<{ name: string; count: number }>
  topics?: Array<[string, number]>
  cached?: boolean
  error?: string
}

// Electron preload 暴露的 API 类型
export interface XMarkdownApi {
  saveMarkdown: (filename: string, content: string) => Promise<string>
  saveMarkdownToPath: (filepath: string, content: string) => Promise<string>
  readMarkdown: (filepath: string) => Promise<string | null>
  listKnowledgeBase: () => Promise<KnowledgeBaseItem[]>
  copyToClipboard: (text: string) => Promise<boolean>
  showSaveDialog: (defaultName: string) => Promise<string | null>
  llmTranslate: (text: string, targetLang: string) => Promise<string>
  llmDistill: (text: string, skillName: string) => Promise<string>
  llmChat: (message: string, context: string, systemPrompt?: string) => Promise<string>
  llmStatus: () => Promise<LlmStatus>
  exportPdf: (html: string, defaultName: string) => Promise<string | null>
  exportSkill: (skillName: string, content: string) => Promise<string>
  backendStatus: () => Promise<{ started: boolean; port: number }>
  getProxy: () => Promise<ProxyConfig>
  setProxy: (enabled: boolean, url: string) => Promise<ProxyConfig>
}

declare global {
  interface Window {
    xmarkdown: XMarkdownApi
  }
}
