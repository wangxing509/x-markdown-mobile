import { create } from 'zustand'
import type {
  Top100Item,
  Top100Stats,
  ThemeName,
  ChatMessage,
  Category,
  Domain,
  Lang,
  AgentConfig,
  Settings,
  LlmConfig,
  SourceConfig,
  RefreshLogItem,
  KnowledgeBaseItem,
  KbTreeInfo,
} from '@/types'

interface AppState {
  // 每日精选
  top100: Top100Item[]
  top100Loading: boolean
  top100Category: Category | null
  top100Domain: Domain | null
  top100Lang: Lang | null
  top100UpdateTime: string
  nextRefresh: string
  top100Stats: Top100Stats | null
  refreshLogs: RefreshLogItem[]

  // 当前工作区
  currentArticle: Top100Item | null
  currentMarkdown: string
  currentTranslatedMarkdown: string
  currentSkillMarkdown: string
  showTranslated: boolean
  showSkill: boolean
  workspaceTab: 'list' | 'editor' | 'preview' | 'split'
  markdownLoading: boolean

  // 主题
  currentTheme: ThemeName

  // Chat
  chatMessages: ChatMessage[]
  chatLoading: boolean
  chatAgentId: string
  chatReferences: string[]

  // 知识库
  kbItems: KnowledgeBaseItem[]
  kbLoading: boolean
  kbTree: KbTreeInfo | null
  kbTreeLoading: boolean

  // LLM 状态
  llmAvailable: boolean

  // 设置
  agents: AgentConfig[]
  settings: Settings | null
  llmConfig: LlmConfig | null
  sources: SourceConfig[]

  // Actions
  setTop100: (items: Top100Item[]) => void
  setTop100Loading: (v: boolean) => void
  setTop100Category: (c: Category | null) => void
  setTop100Domain: (d: Domain | null) => void
  setTop100Lang: (l: Lang | null) => void
  setTop100Meta: (update: string, next: string, stats: Top100Stats | null) => void
  setRefreshLogs: (logs: RefreshLogItem[]) => void
  setCurrentArticle: (a: Top100Item | null) => void
  setCurrentMarkdown: (md: string) => void
  setCurrentTranslatedMarkdown: (md: string) => void
  setCurrentSkillMarkdown: (md: string) => void
  setShowTranslated: (v: boolean) => void
  setShowSkill: (v: boolean) => void
  setWorkspaceTab: (t: 'list' | 'editor' | 'preview' | 'split') => void
  setMarkdownLoading: (v: boolean) => void
  setTheme: (t: ThemeName) => void
  addChatMessage: (m: ChatMessage) => void
  setChatLoading: (v: boolean) => void
  setChatAgentId: (id: string) => void
  setChatReferences: (refs: string[]) => void
  clearChat: () => void
  setKbItems: (items: AppState['kbItems']) => void
  setKbLoading: (v: boolean) => void
  setKbTree: (tree: AppState['kbTree']) => void
  setKbTreeLoading: (v: boolean) => void
  setLlmAvailable: (v: boolean) => void
  setAgents: (agents: AgentConfig[]) => void
  setSettings: (s: Settings) => void
  setLlmConfig: (c: LlmConfig) => void
  setSources: (s: SourceConfig[]) => void
}

export const useStore = create<AppState>((set) => ({
  top100: [],
  top100Loading: false,
  top100Category: null,
  top100Domain: null,
  top100Lang: null,
  top100UpdateTime: '',
  nextRefresh: '',
  top100Stats: null,
  refreshLogs: [],

  currentArticle: null,
  currentMarkdown: '',
  currentTranslatedMarkdown: '',
  currentSkillMarkdown: '',
  showTranslated: false,
  showSkill: false,
  workspaceTab: 'list',
  markdownLoading: false,

  currentTheme: 'minimalist-white',

  chatMessages: [],
  chatLoading: false,
  chatAgentId: 'general_ai',
  chatReferences: [],

  kbItems: [],
  kbLoading: false,
  kbTree: null,
  kbTreeLoading: false,

  llmAvailable: false,

  agents: [],
  settings: null,
  llmConfig: null,
  sources: [],

  setTop100: (items) => set({ top100: items }),
  setTop100Loading: (v) => set({ top100Loading: v }),
  setTop100Category: (c) => set({ top100Category: c }),
  setTop100Domain: (d) => set({ top100Domain: d }),
  setTop100Lang: (l) => set({ top100Lang: l }),
  setTop100Meta: (update, next, stats) => set({ top100UpdateTime: update, nextRefresh: next, top100Stats: stats }),
  setRefreshLogs: (logs) => set({ refreshLogs: logs }),
  setCurrentArticle: (a) => set({ currentArticle: a }),
  setCurrentMarkdown: (md) => set({ currentMarkdown: md }),
  setCurrentTranslatedMarkdown: (md) => set({ currentTranslatedMarkdown: md }),
  setCurrentSkillMarkdown: (md) => set({ currentSkillMarkdown: md }),
  setShowTranslated: (v) => set({ showTranslated: v }),
  setShowSkill: (v) => set({ showSkill: v }),
  setWorkspaceTab: (t) => set({ workspaceTab: t }),
  setMarkdownLoading: (v) => set({ markdownLoading: v }),
  setTheme: (t) => set({ currentTheme: t }),
  addChatMessage: (m) => set((s) => ({ chatMessages: [...s.chatMessages, m] })),
  setChatLoading: (v) => set({ chatLoading: v }),
  setChatAgentId: (id) => set({ chatAgentId: id }),
  setChatReferences: (refs) => set({ chatReferences: refs }),
  clearChat: () => set({ chatMessages: [] }),
  setKbItems: (items) => set({ kbItems: items }),
  setKbLoading: (v) => set({ kbLoading: v }),
  setKbTree: (tree) => set({ kbTree: tree }),
  setKbTreeLoading: (v) => set({ kbTreeLoading: v }),
  setLlmAvailable: (v) => set({ llmAvailable: v }),
  setAgents: (agents) => set({ agents }),
  setSettings: (s) => set({ settings: s }),
  setLlmConfig: (c) => set({ llmConfig: c }),
  setSources: (sources) => set({ sources }),
}))
