import { Copy, Check } from 'lucide-react'
import { useStore } from '@/stores/useStore'
import { useMarkdown } from '@/hooks/useMarkdown'
import { useState } from 'react'

export function CopyButton() {
  const { currentMarkdown, currentTranslatedMarkdown, currentSkillMarkdown, copyRendered } = useMarkdown()
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    // 复制渲染后的内容（优先译文 > Skill > 原文）
    const content = currentTranslatedMarkdown || currentSkillMarkdown || currentMarkdown
    if (!content) {
      alert('暂无可复制内容')
      return
    }
    const ok = await copyRendered(content)
    if (ok) {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <button
      onClick={handleCopy}
      className="card-hover flex items-center gap-1 rounded-md bg-rose-600/80 px-2.5 py-1 text-xs font-medium text-white hover:bg-rose-600 transition cursor-pointer"
    >
      {copied ? <Check size={13} className="text-green-300" /> : <Copy size={13} />}
      {copied ? '已复制' : '复制到小红书/知乎'}
    </button>
  )
}
