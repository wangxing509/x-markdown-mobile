import { Palette } from 'lucide-react'
import { useStore } from '@/stores/useStore'
import { THEMES } from '@/types'
import type { ThemeName } from '@/types'

const themeDot: Record<ThemeName, string> = {
  'minimalist-white': 'bg-white border border-slate-300',
  'tech-blue': 'bg-slate-900 border border-blue-500',
  'magazine-gray': 'bg-slate-300',
  'classic-red': 'bg-orange-50 border border-red-400',
  'ink-green': 'bg-green-900 border border-green-500',
}

export function ThemeSwitcher() {
  const { currentTheme, setTheme } = useStore()

  return (
    <div className="flex items-center gap-1.5">
      <Palette size={14} className="text-slate-400" />
      <div className="flex items-center gap-1">
        {THEMES.map((theme) => (
          <button
            key={theme.id}
            onClick={() => setTheme(theme.id)}
            title={`${theme.name} - ${theme.description}`}
            className={`h-5 w-5 rounded-full ${themeDot[theme.id]} transition hover:scale-110 ${
              currentTheme === theme.id ? 'ring-2 ring-blue-500 ring-offset-1 ring-offset-slate-800' : ''
            } cursor-pointer`}
          />
        ))}
      </div>
    </div>
  )
}
