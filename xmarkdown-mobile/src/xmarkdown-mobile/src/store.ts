import { create } from 'zustand'
import type { ThemeName } from './lib/types'

export type Tab = 'top100' | 'kb' | 'reader'

interface AppState {
  tab: Tab
  currentTheme: ThemeName
  autoRefresh: boolean
  setTab: (t: Tab) => void
  setTheme: (t: ThemeName) => void
  setAutoRefresh: (v: boolean) => void
}

const savedTheme = (localStorage.getItem('xmd-theme') as ThemeName) || 'minimalist-white'
const savedAuto = localStorage.getItem('xmd-auto-refresh') !== 'off'

export const useAppStore = create<AppState>((set) => ({
  tab: 'top100',
  currentTheme: savedTheme,
  autoRefresh: savedAuto,
  setTab: (t) => set({ tab: t }),
  setTheme: (t) => {
    localStorage.setItem('xmd-theme', t)
    set({ currentTheme: t })
  },
  setAutoRefresh: (v) => {
    localStorage.setItem('xmd-auto-refresh', v ? 'on' : 'off')
    set({ autoRefresh: v })
  },
}))
