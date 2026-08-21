import { Download } from 'lucide-react'
import { useStore } from '@/stores/useStore'
import { useMarkdown } from '@/hooks/useMarkdown'

export function DownloadButton() {
  const { currentMarkdown, currentTranslatedMarkdown, currentSkillMarkdown, download } = useMarkdown()
  const { currentArticle } = useStore()

  const handleDownload = async (type: 'original' | 'translated' | 'skill') => {
    let content = ''
    let name = ''
    const base = currentArticle?.title?.replace(/[\\/:*?"<>|]/g, '_').slice(0, 60) || 'untitled'
    if (type === 'original') {
      content = currentMarkdown
      name = `${base}_原文.md`
    } else if (type === 'translated') {
      content = currentTranslatedMarkdown
      name = `${base}_译文.md`
    } else {
      content = currentSkillMarkdown
      name = `${base}_SKILL.md`
    }
    if (!content) {
      alert('暂无可下载内容')
      return
    }
    await download(name, content)
  }

  return (
    <div className="flex items-center gap-1">
      <button
        onClick={() => handleDownload('original')}
        disabled={!currentMarkdown}
        title="下载原文 Markdown"
        className="card-hover flex items-center gap-1 rounded-md bg-slate-700/60 px-2 py-1 text-xs text-slate-200 hover:bg-slate-700 disabled:opacity-50 transition cursor-pointer"
      >
        <Download size={12} /> 原文
      </button>
      {currentTranslatedMarkdown && (
        <button
          onClick={() => handleDownload('translated')}
          title="下载译文 Markdown"
          className="card-hover flex items-center gap-1 rounded-md bg-slate-700/60 px-2 py-1 text-xs text-slate-200 hover:bg-slate-700 transition cursor-pointer"
        >
          <Download size={12} /> 译文
        </button>
      )}
      {currentSkillMarkdown && (
        <button
          onClick={() => handleDownload('skill')}
          title="下载 Skill Markdown"
          className="card-hover flex items-center gap-1 rounded-md bg-slate-700/60 px-2 py-1 text-xs text-slate-200 hover:bg-slate-700 transition cursor-pointer"
        >
          <Download size={12} /> Skill
        </button>
      )}
    </div>
  )
}
