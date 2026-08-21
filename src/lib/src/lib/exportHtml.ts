import type { ThemeName } from '@/types'

/**
 * 生成可导出的单文件 HTML（内联当前主题 CSS + Markdown 渲染样式）
 * 供“发布 → 导出 HTML / PDF”使用。
 */

const THEME_VARS: Record<ThemeName, Record<string, string>> = {
  'minimalist-white': {
    '--md-bg': '#ffffff', '--md-text': '#1e293b', '--md-heading': '#0f172a',
    '--md-link': '#2563eb', '--md-code-bg': '#f1f5f9', '--md-code-text': '#db2777',
    '--md-pre-bg': '#1e293b', '--md-pre-text': '#e2e8f0', '--md-quote': '#3b82f6',
    '--md-quote-bg': '#eff6ff', '--md-quote-text': '#475569', '--md-border': '#e2e8f0',
    '--md-th-bg': '#f8fafc', '--md-font': "'Noto Sans', system-ui, sans-serif",
  },
  'tech-blue': {
    '--md-bg': '#0d1117', '--md-text': '#c9d1d9', '--md-heading': '#58a6ff',
    '--md-link': '#58a6ff', '--md-code-bg': '#161b22', '--md-code-text': '#f0883e',
    '--md-pre-bg': '#161b22', '--md-pre-text': '#c9d1d9', '--md-quote': '#1f6feb',
    '--md-quote-bg': '#0d1117', '--md-quote-text': '#8b949e', '--md-border': '#30363d',
    '--md-th-bg': '#161b22', '--md-font': "'JetBrains Mono', 'Noto Sans', sans-serif",
  },
  'magazine-gray': {
    '--md-bg': '#f0f0f0', '--md-text': '#4a4a4a', '--md-heading': '#2c2c2c',
    '--md-link': '#6366f1', '--md-code-bg': '#e4e4e4', '--md-code-text': '#b91c1c',
    '--md-pre-bg': '#2c2c2c', '--md-pre-text': '#d0d0d0', '--md-quote': '#8b5cf6',
    '--md-quote-bg': '#e8e3f3', '--md-quote-text': '#5a5a5a', '--md-border': '#d0d0d0',
    '--md-th-bg': '#e4e4e4', '--md-font': "'Noto Serif SC', Georgia, serif",
  },
  'classic-red': {
    '--md-bg': '#fff8f0', '--md-text': '#5c3a3a', '--md-heading': '#c0392b',
    '--md-link': '#d35400', '--md-code-bg': '#fce4d6', '--md-code-text': '#a04000',
    '--md-pre-bg': '#3d1f1f', '--md-pre-text': '#f5d0c5', '--md-quote': '#c0392b',
    '--md-quote-bg': '#fce4d6', '--md-quote-text': '#7c4a4a', '--md-border': '#f5d0c5',
    '--md-th-bg': '#fce4d6', '--md-font': "'Noto Serif SC', Georgia, serif",
  },
  'ink-green': {
    '--md-bg': '#1a2e1a', '--md-text': '#a8c8a8', '--md-heading': '#7dcc7d',
    '--md-link': '#8bc34a', '--md-code-bg': '#234c23', '--md-code-text': '#b5d6a8',
    '--md-pre-bg': '#0d1a0d', '--md-pre-text': '#a8c8a8', '--md-quote': '#4a7c4a',
    '--md-quote-bg': '#234c23', '--md-quote-text': '#88a888', '--md-border': '#2a4a2a',
    '--md-th-bg': '#234c23', '--md-font': "'Noto Serif SC', serif",
  },
}

const SHARED_CSS = `
.md-render-container {
  background: var(--md-bg, #fff); color: var(--md-text, #1e293b);
  font-family: var(--md-font, sans-serif); padding: 2rem 2.5rem;
  line-height: 1.8; max-width: 900px; margin: 0 auto;
}
.md-render-container h1, .md-render-container h2, .md-render-container h3, .md-render-container h4 {
  color: var(--md-heading, #1e293b); font-weight: 600; margin-top: 1.8em; margin-bottom: 0.8em;
  border-bottom: 1px solid var(--md-border, #e2e8f0); padding-bottom: 0.3em;
}
.md-render-container h1 { font-size: 1.9em; }
.md-render-container h2 { font-size: 1.55em; }
.md-render-container h3 { font-size: 1.25em; border-bottom: none; }
.md-render-container p { margin: 0.8em 0; }
.md-render-container a { color: var(--md-link, #2563eb); text-decoration: none; }
.md-render-container code {
  background: var(--md-code-bg, #f1f5f9); color: var(--md-code-text, #db2777);
  padding: 0.15em 0.4em; border-radius: 4px; font-size: 0.88em;
}
.md-render-container pre {
  background: var(--md-pre-bg, #1e293b); color: var(--md-pre-text, #e2e8f0);
  padding: 1rem 1.2rem; border-radius: 8px; overflow-x: auto; margin: 1.2em 0;
}
.md-render-container pre code { background: transparent; color: inherit; padding: 0; }
.md-render-container blockquote {
  border-left: 4px solid var(--md-quote, #3b82f6); background: var(--md-quote-bg, #f0f4ff);
  margin: 1em 0; padding: 0.6em 1.2em; color: var(--md-quote-text, #475569);
  border-radius: 0 6px 6px 0;
}
.md-render-container table { border-collapse: collapse; margin: 1.2em 0; width: 100%; }
.md-render-container th, .md-render-container td {
  border: 1px solid var(--md-border, #e2e8f0); padding: 0.5em 0.8em; text-align: left;
}
.md-render-container th { background: var(--md-th-bg, #f8fafc); font-weight: 600; }
.md-render-container img { max-width: 100%; border-radius: 8px; margin: 1em 0; }
.md-render-container ul, .md-render-container ol { padding-left: 1.5em; margin: 0.6em 0; }
.md-render-container hr { border: none; border-top: 1px solid var(--md-border, #e2e8f0); margin: 2em 0; }
.md-render-container pre code.hljs { background: transparent; }
@media print { body { margin: 0; } }
`

/** 简单 Markdown → HTML（表格/代码/标题/列表/链接等常用语法） */
function mdToHtml(md: string): string {
  let html = md
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  // 代码块（先占位保护）
  const codeBlocks: string[] = []
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_m, lang: string, code: string) => {
    codeBlocks.push(`<pre><code class="hljs language-${lang || 'text'}">${code}</code></pre>`)
    return `\u0000CODE${codeBlocks.length - 1}\u0000`
  })
  html = html.replace(/^\s{4}.*$/gm, (line) => `<pre>${line.trim()}</pre>`)
  // 标题
  html = html.replace(/^###### (.*)$/gm, '<h6>$1</h6>')
  html = html.replace(/^##### (.*)$/gm, '<h5>$1</h5>')
  html = html.replace(/^#### (.*)$/gm, '<h4>$1</h4>')
  html = html.replace(/^### (.*)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.*)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.*)$/gm, '<h1>$1</h1>')
  // 引用、分割线
  html = html.replace(/^&gt;\s?(.*)$/gm, '<blockquote>$1</blockquote>')
  html = html.replace(/^---\s*$/gm, '<hr/>')
  // 行内样式
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
  // 列表
  html = html.replace(/^- (.*)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>')
  // 段落
  html = html.replace(/^(?!<[hupbl]|\u0000CODE|<\/)(.+)$/gm, '<p>$1</p>')
  // 还原代码块
  html = html.replace(/\u0000CODE(\d+)\u0000/g, (_m, i: string) => codeBlocks[Number(i)])
  return html
}

export function buildExportHtml(md: string, theme: ThemeName, title = 'X-markdown 发布'): string {
  const vars = Object.entries(THEME_VARS[theme] || THEME_VARS['minimalist-white'])
    .map(([k, v]) => `${k}: ${v};`)
    .join(' ')
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>${title.replace(/</g, '&lt;')}</title>
<style>
body { margin: 0; background: var(--md-bg, #fff); }
${SHARED_CSS}
.md-render-container { ${vars} }
</style>
</head>
<body>
<div class="md-render-container">
${mdToHtml(md)}
</div>
</body>
</html>`
}

