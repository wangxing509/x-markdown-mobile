import { FlaskConical } from 'lucide-react'
import { useStore } from '@/stores/useStore'
import { useMarkdown } from '@/hooks/useMarkdown'
import { useState } from 'react'

export function DistillButton() {
  const { currentMarkdown, distill, markdownLoading, currentSkillMarkdown } = useMarkdown()
  const { setCurrentSkillMarkdown, setWorkspaceTab, setShowSkill, setShowTranslated, showSkill } = useStore()
  const [showSkillName, setShowSkillName] = useState(false)
  const [skillName, setSkillName] = useState('')

  const handleDistill = async () => {
    if (!skillName.trim()) return
    const result = await distill(currentMarkdown, skillName.trim())
    if (result) {
      setCurrentSkillMarkdown(result.content)
      setShowSkill(true)
      setShowTranslated(false)
      setShowSkillName(false)
      setSkillName('')
      setWorkspaceTab('preview')
      alert(`Skill 蒸馏成功！\n已写入: ${result.skillPath}`)
    }
  }

  const toggleSkill = () => {
    setShowSkill(!showSkill)
    setShowTranslated(false)
  }

  return (
    <div className="relative">
      <button
        onClick={() => setShowSkillName(!showSkillName)}
        disabled={markdownLoading || !currentMarkdown}
        className="card-hover flex items-center gap-1 rounded-md bg-amber-600/80 px-2.5 py-1 text-xs font-medium text-white hover:bg-amber-600 disabled:opacity-50 transition cursor-pointer"
      >
        <FlaskConical size={13} />
        蒸馏 Skill
      </button>
      {currentSkillMarkdown && (
        <button
          onClick={toggleSkill}
          className={`rounded px-2 py-1 text-xs transition cursor-pointer ${
            showSkill
              ? 'bg-amber-600/30 text-amber-300'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          {showSkill ? '✓ Skill' : '看 Skill'}
        </button>
      )}
      {showSkillName && (
        <div className="absolute right-0 top-full z-50 mt-1 w-64 rounded-lg border border-slate-700/50 bg-slate-800 p-3 shadow-xl">
          <label className="text-xs text-slate-400">Skill 名称</label>
          <input
            type="text"
            value={skillName}
            onChange={(e) => setSkillName(e.target.value)}
            placeholder="如: ai-news-aggregator"
            className="mt-1 w-full rounded bg-slate-900 px-2 py-1.5 text-sm text-slate-200 border border-slate-700/50 focus:border-blue-500/50 outline-none"
            onKeyDown={(e) => e.key === 'Enter' && handleDistill()}
          />
          <div className="mt-2 flex gap-2">
            <button
              onClick={handleDistill}
              disabled={!skillName.trim() || markdownLoading}
              className="flex-1 rounded bg-amber-600 px-2 py-1 text-xs text-white hover:bg-amber-700 disabled:opacity-50 cursor-pointer"
            >
              {markdownLoading ? '蒸馏中...' : '确认蒸馏'}
            </button>
            <button
              onClick={() => setShowSkillName(false)}
              className="rounded bg-slate-700 px-2 py-1 text-xs text-slate-300 hover:bg-slate-600 cursor-pointer"
            >
              取消
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
