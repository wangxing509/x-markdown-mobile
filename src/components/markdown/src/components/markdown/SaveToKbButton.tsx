import { BookmarkPlus, ChevronDown, Languages } from 'lucide-react'
import { useState } from 'react'
import { useStore } from '@/stores/useStore'
import { useMarkdown } from '@/hooks/useMarkdown'
import type { Domain } from '@/types'

function toast(type: 'success' | 'error', message: string) {
  window.dispatchEvent(new CustomEvent('xmarkdown:toast', { detail: { type, message } }))
}

export function SaveToKbButton() {
  const { currentArticle, currentMarkdown, currentTranslatedMarkdown } = useStore()
  const { saveToKnowledgeBase, translate, markdownLoading } = useMarkdown()
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)

  const doSave = async (includeTranslation: boolean) => {
    if (!currentArticle || !currentMarkdown) return
    setSaving(true)
    try {
      let translated = currentTranslatedMarkdown || ''
      const lang = currentArticle.lang || (currentArticle.source === '粘贴链接' ? undefined : undefined)
      if (includeTranslation && !translated && lang !== 'cn') {
        // 尚未翻译：先调用翻译
        const t = await translate(currentMarkdown)
        translated = t ?? ''
      }
      const domain = (currentArticle.domain ?? 'ai_general') as Domain
      const res = await saveToKnowledgeBase({
        url: currentArticle.url,
        title: currentArticle.title,
        originalMd: currentMarkdown,
        translatedMd: translated || undefined,
        domain,
        lang: (currentArticle.lang as 'cn' | 'en' | undefined) || undefined,
        category: currentArticle.category,
        source: currentArticle.source,
      })
      if (res.success) {
        toast('success', res.message || '已保存到知识库')
        window.dispatchEvent(new CustomEvent('xmarkdown:kb-updated'))
      } else if (res.duplicate) {
        toast('error', `已存在：${res.message}`)
      } else {
        toast('error', res.message || '保存失败')
      }
    } catch (e) {
      toast('error', `保存失败：${(e as Error).message}`)
    } finally {
      setSaving(false)
      setOpen(false)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        disabled={saving || !currentMarkdown}
        className="card-hover flex items-center gap-1 rounded-md bg-indigo-600/80 px-2.5 py-1 text-xs font-medium text-white hover:bg-indigo-600 disabled:opacity-50 transition cursor-pointer"
        title="保存到知识库"
      >
        <BookmarkPlus size={13} />
        {saving ? '保存中...' : '保存知识库'}
        <ChevronDown size={12} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full z-50 mt-1 w-56 overflow-hidden rounded-lg border border-slate-700 bg-slate-800 py-1 shadow-xl">
            <button
              onClick={() => void doSave(false)}
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-slate-200 hover:bg-slate-700/60 transition cursor-pointer"
            >
              <BookmarkPlus size={13} className="text-indigo-400" />
              仅保存原文
            </button>
            <button
              onClick={() => void doSave(true)}
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-slate-200 hover:bg-slate-700/60 transition cursor-pointer"
            >
              <Languages size={13} className="text-emerald-400" />
              翻译并保存（原文+译文）
            </button>
          </div>
        </>
      )}
    </div>
  )
}

