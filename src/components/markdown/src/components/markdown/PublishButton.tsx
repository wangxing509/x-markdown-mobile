import { Share2, FileCode2, FileText, FileDown, Copy, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { useStore } from '@/stores/useStore'
import { useMarkdown } from '@/hooks/useMarkdown'
import { buildExportHtml } from '@/lib/exportHtml'

function toast(type: 'success' | 'error', message: string) {
  window.dispatchEvent(new CustomEvent('xmarkdown:toast', { detail: { type, message } }))
}

export function PublishButton() {
  const { currentArticle, currentMarkdown, currentTranslatedMarkdown, currentTheme, showTranslated } = useStore()
  const { download, copyRendered } = useMarkdown()
  const [open, setOpen] = useState(false)

  const base = currentArticle?.title?.replace(/[\\/:*?"<>|]/g, '_').slice(0, 60) || 'untitled'
  const content = (showTranslated && currentTranslatedMarkdown) ? currentTranslatedMarkdown : currentMarkdown

  const exportHtml = async () => {
    if (!content) return
    try {
      const html = buildExportHtml(content, currentTheme, base)
      const filepath = await window.xmarkdown.showSaveDialog(`${base}.html`)
      if (filepath) {
        await window.xmarkdown.saveMarkdownToPath(filepath, html)
        toast('success', `已导出 HTML：${filepath}`)
      }
    } catch (e) {
      toast('error', `导出 HTML 失败：${(e as Error).message}`)
    }
    setOpen(false)
  }

  const exportPdf = async () => {
    if (!content) return
    try {
      const html = buildExportHtml(content, currentTheme, base)
      const filepath = await window.xmarkdown.exportPdf(html, `${base}.pdf`)
      if (filepath) toast('success', `已导出 PDF：${filepath}`)
    } catch (e) {
      toast('error', `导出 PDF 失败：${(e as Error).message}`)
    }
    setOpen(false)
  }

  const exportMd = async (type: 'original' | 'translated') => {
    await download(`${base}_${type === 'translated' ? '译文' : '原文'}.md`, type === 'translated' ? currentTranslatedMarkdown : currentMarkdown)
    setOpen(false)
  }

  const copy = async () => {
    const ok = await copyRendered(content)
    if (ok) toast('success', '已复制渲染内容到剪贴板')
    setOpen(false)
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        disabled={!content}
        className="card-hover flex items-center gap-1 rounded-md bg-rose-600/80 px-2.5 py-1 text-xs font-medium text-white hover:bg-rose-600 disabled:opacity-50 transition cursor-pointer"
      >
        <Share2 size={13} /> 发布 <ChevronDown size={12} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full z-50 mt-1 w-60 overflow-hidden rounded-lg border border-slate-700 bg-slate-800 py-1 shadow-xl">
            <button onClick={() => void exportHtml()} className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-slate-200 hover:bg-slate-700/60 transition cursor-pointer">
              <FileCode2 size={13} className="text-blue-400" /> 导出 HTML（单文件）
            </button>
            <button onClick={() => void exportPdf()} className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-slate-200 hover:bg-slate-700/60 transition cursor-pointer">
              <FileText size={13} className="text-rose-400" /> 导出 PDF（A4）
            </button>
            <button onClick={() => void exportMd('original')} className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-slate-200 hover:bg-slate-700/60 transition cursor-pointer">
              <FileDown size={13} className="text-emerald-400" /> 导出 Markdown（原文）
            </button>
            {currentTranslatedMarkdown && (
              <button onClick={() => void exportMd('translated')} className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-slate-200 hover:bg-slate-700/60 transition cursor-pointer">
                <FileDown size={13} className="text-emerald-400" /> 导出 Markdown（译文）
              </button>
            )}
            <button onClick={() => void copy()} className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-slate-200 hover:bg-slate-700/60 transition cursor-pointer">
              <Copy size={13} className="text-amber-400" /> 复制渲染内容到剪贴板
            </button>
          </div>
        </>
      )}
    </div>
  )
}

