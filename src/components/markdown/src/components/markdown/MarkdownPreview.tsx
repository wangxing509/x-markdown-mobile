import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { useStore } from '@/stores/useStore'

interface Props {
  content: string
}

export function MarkdownPreview({ content }: Props) {
  const {
    currentTheme,
    currentArticle,
    setCurrentMarkdown,
    setCurrentArticle,
    setWorkspaceTab,
    setCurrentTranslatedMarkdown,
    setCurrentSkillMarkdown,
    setShowTranslated,
    setShowSkill,
  } = useStore()

  // 打开索引中的相对链接（知识库 .md 文件）
  const openKbFile = async (href: string) => {
    const baseUrl = currentArticle?.url
    if (!baseUrl) return
    // Windows 路径反斜杠 → 统一为斜杠，再取目录部分拼接目标文件
    const normalizedBase = baseUrl.replace(/\\/g, '/')
    const base = normalizedBase.split('/').slice(0, -1).join('/')
    let relative = href
    try {
      relative = decodeURIComponent(relative)
    } catch {
      // 非 URL 编码的原始文件名，原样使用
    }
    const target = `${base}/${relative}`
    try {
      const fileContent = window.xmarkdown
        ? await window.xmarkdown.readMarkdown(target)
        : null
      if (!fileContent) return
      setCurrentTranslatedMarkdown('')
      setCurrentSkillMarkdown('')
      setShowTranslated(false)
      setShowSkill(false)
      setCurrentMarkdown(fileContent)
      // 从索引点击文章时保持预览呈现，直接渲染该文
      setWorkspaceTab('preview')
      setCurrentArticle({
        id: 0,
        rank: 0,
        title: href
          .replace(/\.md$/, '')
          .replace(/^\d{8}_/, '')
          .replace(/_原文$/, ''),
        url: target,
        summary: '',
        source: '知识库',
        sourceAuthority: 0.5,
        publishedAt: null,
        category: 'article',
        score: 0,
        tags: '',
        verified: true,
      })
    } catch (e) {
      console.error('打开知识库文件失败:', e)
    }
  }

  return (
    <div
      className="md-render-container h-full overflow-y-auto"
      data-theme={currentTheme}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          a: ({ href, children }) => (
            <a
              href={href}
              onClick={(e) => {
                if (href && href.endsWith('.md')) {
                  e.preventDefault()
                  void openKbFile(href)
                }
              }}
              className={href?.endsWith('.md') ? 'text-blue-400 underline hover:text-blue-300' : undefined}
            >
              {children}
            </a>
          ),
        }}
      >
        {content || '*暂无内容*'}
      </ReactMarkdown>
    </div>
  )
}
