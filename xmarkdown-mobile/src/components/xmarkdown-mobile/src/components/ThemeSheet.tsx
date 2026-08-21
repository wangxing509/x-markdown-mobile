import { X } from 'lucide-react'
import { useAppStore } from '../store'
import type { ThemeName } from '../lib/types'

const THEMES: Array<{ id: ThemeName; name: string; desc: string; bg: string }> = [
  { id: 'minimalist-white', name: '极简白', desc: '白底黑字，大量留白', bg: '#ffffff' },
  { id: 'tech-blue', name: '科技蓝', desc: '深蓝渐变，青色强调', bg: '#0d1117' },
  { id: 'magazine-gray', name: '杂志灰', desc: '灰底衬线，杂志排版', bg: '#f0f0f0' },
  { id: 'classic-red', name: '经典红', desc: '暖色调，红色标题', bg: '#fff8f0' },
  { id: 'ink-green', name: '墨绿雅刊', desc: '墨绿背景，古风雅致', bg: '#1a2e1a' },
]

export function ThemeSheet({ onClose }: { onClose: () => void }) {
  const current = useAppStore((s) => s.currentTheme)
  const setTheme = useAppStore((s) => s.setTheme)

  return (
    <div className="fade-in fixed inset-0 z-40 flex flex-col justify-end bg-black/50" onClick={onClose}>
      <div
        className="rounded-t-2xl border-t border-slate-800 bg-slate-900 p-4 pb-[calc(env(safe-area-inset-bottom)+1rem)]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-100">阅读主题</h3>
          <button onClick={onClose} className="rounded-full p-1 text-slate-400 hover:bg-slate-800">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-2">
          {THEMES.map((t) => (
            <button
              key={t.id}
              onClick={() => setTheme(t.id)}
              className={`flex w-full items-center gap-3 rounded-xl border p-3 text-left transition ${
                current === t.id ? 'border-blue-500/60 bg-blue-500/10' : 'border-slate-800 bg-slate-800/40'
              }`}
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-black/10 text-xs font-bold text-black/70" style={{ background: t.bg }}>
                文
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-medium text-slate-100">{t.name}</span>
                <span className="block truncate text-xs text-slate-500">{t.desc}</span>
              </span>
              {current === t.id && <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-blue-500" />}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
