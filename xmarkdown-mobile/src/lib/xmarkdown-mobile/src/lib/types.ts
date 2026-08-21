// 手机端数据模型（与桌面端导出格式一致）

export type Category = 'article' | 'tutorial' | 'application'
export type Domain = 'ai_general' | 'ai_audit'
export type Lang = 'cn' | 'en'

export interface Top100Item {
  id: number
  rank: number
  title: string
  url: string
  summary: string
  source: string
  category: Category
  score: number
  tags: string
  likes?: number
  comments?: number
  author?: string
  lang?: Lang
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
}

export interface SiteIndex {
  generatedAt: string
  nextRefresh: string
  top100: Top100Item[]
  stats: Top100Stats
  kbCount: number
}

export interface KbMeta {
  id: number
  title: string
  source: string
  domain: string
  lang: string
  category: string
  savedAt: string
  hasTranslation: boolean
  size: number
}

export interface KbArticle {
  meta: KbMeta
  original: string
  translated?: string
}

export type ThemeName = 'minimalist-white' | 'tech-blue' | 'magazine-gray' | 'classic-red' | 'ink-green'

export interface ThemeOption {
  id: ThemeName
  name: string
  swatch: string
}
