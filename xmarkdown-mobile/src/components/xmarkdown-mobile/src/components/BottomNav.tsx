import { Flame, Library, BookOpen, Palette } from 'lucide-react'
import { useAppStore, type Tab } from '../store'

const tabs: Array<{ id: Tab; label: string; icon: typeof Flame }> = [
  { id: 'top100', label: '精选', icon: Flame },
  { id: 'kb', label: '知识库', icon: Library },
  { id: 'reader', label: '阅读', icon: BookOpen },
]

export function BottomNav({ onOpenTheme }: { onOpenTheme: () => void }) {
  const tab = useAppStore((s) => s.tab)
  const setTab = useAppStore((s) => s.setTab)

  return (
    <nav className="no-select border-t border-slate-800 bg-slate-900/95 pb-[env(safe-area-inset-bottom)] backdrop-blur">
      <div className="flex items-center justify-around">
        {tabs.map(({ id, label, icon: Icon }) => {
          const active = tab === id
          return (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex flex-col items-center gap-0.5 px-4 py-2 text-[11px] transition ${
                active ? 'text-blue-400' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <Icon size={22} strokeWidth={active ? 2.4 : 2} />
              {label}
            </button>
          )
        })}
        <button
          onClick={onOpenTheme}
          className="flex flex-col items-center gap-0.5 px-4 py-2 text-[11px] text-slate-500 hover:text-slate-300"
        >
          <Palette size={22} />
          主题
        </button>
      </div>
    </nav>
  )
}
