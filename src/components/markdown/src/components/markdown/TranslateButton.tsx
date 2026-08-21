import { Languages } from 'lucide-react'
import { useStore } from '@/stores/useStore'
import { useMarkdown } from '@/hooks/useMarkdown'

export function TranslateButton() {
  const { currentMarkdown, currentTranslatedMarkdown, translate, markdownLoading } = useMarkdown()
  const { setWorkspaceTab, setShowTranslated, setShowSkill, showTranslated } = useStore()

  const handleTranslate = async () => {
    await translate()
    setShowTranslated(true)
    setShowSkill(false)
    setWorkspaceTab('preview')
  }

  const toggleTranslated = () => {
    // 切换原文/译文显示
    setShowTranslated(!showTranslated)
    setShowSkill(false)
  }

  return (
    <div className="flex items-center gap-1">
      <button
        onClick={handleTranslate}
        disabled={markdownLoading || !currentMarkdown}
        className="card-hover flex items-center gap-1 rounded-md bg-emerald-600/80 px-2.5 py-1 text-xs font-medium text-white hover:bg-emerald-600 disabled:opacity-50 transition cursor-pointer"
      >
        <Languages size={13} />
        {markdownLoading ? '翻译中...' : '英译中'}
      </button>
      {currentTranslatedMarkdown && (
        <button
          onClick={toggleTranslated}
          className={`rounded px-2 py-1 text-xs transition cursor-pointer ${
            showTranslated
              ? 'bg-emerald-600/30 text-emerald-300'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          {showTranslated ? '✓ 译文' : '看译文'}
        </button>
      )}
    </div>
  )
}
