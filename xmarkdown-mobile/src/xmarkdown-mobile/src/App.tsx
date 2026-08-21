import { useEffect, useState } from 'react'
import { useAppStore } from './store'
import { BottomNav } from './components/BottomNav'
import { Top100View } from './components/Top100View'
import { KbView } from './components/KbView'
import { ReaderView } from './components/ReaderView'
import { ThemeSheet } from './components/ThemeSheet'
import { Toast } from './components/Toast'
import { loadIndex, startAutoRefresh } from './lib/data'
import type { SiteIndex } from './lib/types'

export default function App() {
  const tab = useAppStore((s) => s.tab)
  const autoRefresh = useAppStore((s) => s.autoRefresh)
  const [index, setIndex] = useState<SiteIndex | null>(null)
  const [loading, setLoading] = useState(true)
  const [themeOpen, setThemeOpen] = useState(false)
  const [toast, setToast] = useState<{ type: string; msg: string } | null>(null)

  // 初始加载 + 自动刷新
  useEffect(() => {
    let alive = true
    loadIndex()
      .then((d) => {
        if (alive) {
          setIndex(d)
          setLoading(false)
        }
      })
      .catch(() => {
        if (alive) {
          setLoading(false)
          setToast({ type: 'error', msg: '数据加载失败，请检查网络' })
        }
      })

    const stop = startAutoRefresh(() => {
      if (!autoRefresh) return
      loadIndex({ force: true })
        .then((d) => {
          if (alive) {
            setIndex((prev) => {
              if (prev && prev.generatedAt !== d.generatedAt) {
                setToast({ type: 'info', msg: '内容已更新' })
              }
              return d
            })
          }
        })
        .catch(() => {})
    })

    return () => {
      alive = false
      stop()
    }
  }, [autoRefresh])

  const notify = (t: string, m: string) => setToast({ type: t, msg: m })

  return (
    <div className="flex h-full flex-col bg-slate-950 text-slate-100">
      <div className="flex-1 overflow-hidden">
        {tab === 'top100' && <Top100View index={index} loading={loading} onToast={notify} onOpenTheme={() => setThemeOpen(true)} />}
        {tab === 'kb' && <KbView onToast={notify} />}
        {tab === 'reader' && <ReaderView onToast={notify} />}
      </div>
      <BottomNav onOpenTheme={() => setThemeOpen(true)} />
      {themeOpen && <ThemeSheet onClose={() => setThemeOpen(false)} />}
      {toast && <Toast toast={toast} onDone={() => setToast(null)} />}
    </div>
  )
}
