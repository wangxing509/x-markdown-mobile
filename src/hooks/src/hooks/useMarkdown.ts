import { useCallback } from 'react'
import { useStore } from '@/stores/useStore'
import { api } from '@/api/client'
import type { Top100Item, Domain, Lang, Category } from '@/types'

export function useMarkdown() {
  const {
    currentArticle,
    currentMarkdown,
    currentTranslatedMarkdown,
    currentSkillMarkdown,
    workspaceTab,
    markdownLoading,
    currentTheme,
    setCurrentArticle,
    setCurrentMarkdown,
    setCurrentTranslatedMarkdown,
    setCurrentSkillMarkdown,
    setWorkspaceTab,
    setMarkdownLoading,
    setTheme,
  } = useStore()

  const fetchMarkdown = useCallback(async (article: Top100Item, strict = false) => {
    setMarkdownLoading(true)
    setCurrentArticle(article)
    setWorkspaceTab('editor')
    // 切换文章时清理旧译文/蒸馏，避免上一次翻译失败的错误信息污染新文章预览
    const store = useStore.getState()
    store.setCurrentTranslatedMarkdown('')
    store.setCurrentSkillMarkdown('')
    store.setShowTranslated(false)
    store.setShowSkill(false)
    try {
      const data = await api.convertUrl(article.url)
      const failMarkers = ['抓取失败', '无法解析正文', '内容过长已截断', '转换失败']
      const failed = !data.markdown ||
        data.markdown.length < 300 ||
        failMarkers.some((m) => data.markdown.slice(0, 300).includes(m))
      if (strict && failed) {
        window.dispatchEvent(new CustomEvent('xmarkdown:toast', {
          detail: { type: 'error', message: '原文获取失败：该链接无法提取正文（可能需代理或需登录）' },
        }))
        return
      }
      setCurrentMarkdown(data.markdown)
    } catch (e) {
      console.error('获取 Markdown 失败:', e)
      if (strict) {
        window.dispatchEvent(new CustomEvent('xmarkdown:toast', {
          detail: { type: 'error', message: `原文获取失败：${(e as Error).message}` },
        }))
        return
      }
      // 降级：使用摘要作为内容
      setCurrentMarkdown(`# ${article.title}\n\n> 来源: ${article.source}\n\n${article.summary}`)
    } finally {
      setMarkdownLoading(false)
    }
  }, [setCurrentArticle, setCurrentMarkdown, setWorkspaceTab, setMarkdownLoading])

  const translate = useCallback(async (text?: string) => {
    const source = text ?? currentMarkdown
    if (!source) return
    setMarkdownLoading(true)
    try {
      const res = await api.translate(source)
      setCurrentTranslatedMarkdown(res.translated)
      return res.translated
    } catch (e) {
      // 翻译失败时，绝不污染 currentTranslatedMarkdown，避免影响其他文章预览
      console.error('[翻译失败]', (e as Error).message)
      window.dispatchEvent(new CustomEvent('xmarkdown:toast', {
        detail: { type: 'error', message: `翻译失败：${(e as Error).message}` },
      }))
      return null
    } finally {
      setMarkdownLoading(false)
    }
  }, [currentMarkdown, setCurrentTranslatedMarkdown, setMarkdownLoading])

  const distill = useCallback(async (text: string, skillName: string) => {
    setMarkdownLoading(true)
    try {
      const res = await api.distill(text, skillName)
      setCurrentSkillMarkdown(res.content)
      return res
    } catch (e) {
      console.error('蒸馏失败:', e)
      return null
    } finally {
      setMarkdownLoading(false)
    }
  }, [setCurrentSkillMarkdown, setMarkdownLoading])

  const download = useCallback(async (filename: string, content: string) => {
    try {
      const filepath = await window.xmarkdown.showSaveDialog(filename)
      if (filepath) {
        await window.xmarkdown.saveMarkdownToPath(filepath, content)
      }
      return filepath
    } catch (e) {
      console.error('下载失败:', e)
      return null
    }
  }, [])

  const copyRendered = useCallback(async (content: string) => {
    try {
      await window.xmarkdown.copyToClipboard(content)
      return true
    } catch (e) {
      console.error('复制失败:', e)
      return false
    }
  }, [])

  const saveToKnowledgeBase = useCallback(async (opts: {
    url: string
    title: string
    originalMd: string
    translatedMd?: string
    domain?: Domain
    lang?: Lang
    category?: Category
    source?: string
    tags?: string[]
  }) => {
    const res = await api.saveToKnowledgeBase({
      url: opts.url,
      title: opts.title,
      originalMd: opts.originalMd,
      translatedMd: opts.translatedMd,
      domain: opts.domain ?? 'ai_general',
      lang: opts.lang,
      category: opts.category ?? 'article',
      source: opts.source,
      tags: opts.tags,
    })
    return res
  }, [])

  return {
    currentArticle,
    currentMarkdown,
    currentTranslatedMarkdown,
    currentSkillMarkdown,
    workspaceTab,
    markdownLoading,
    currentTheme,
    fetchMarkdown,
    translate,
    distill,
    download,
    copyRendered,
    saveToKnowledgeBase,
    setWorkspaceTab,
    setTheme,
    setCurrentMarkdown,
  }
}
