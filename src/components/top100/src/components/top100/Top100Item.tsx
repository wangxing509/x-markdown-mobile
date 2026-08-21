import { ExternalLink, ThumbsUp, MessageCircle, Star } from 'lucide-react'
import type { Top100Item as Top100ItemType, Category } from '@/types'

const categoryColors: Record<Category, string> = {
  article: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
  tutorial: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  application: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
}

const categoryNames: Record<Category, string> = {
  article: '文章',
  tutorial: '教程',
  application: '应用案例',
}

// 确保 URL 有协议前缀
function normalizeUrl(url: string): string {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  return `https://${url}`
}

interface Props {
  item: Top100ItemType
  onOpen: (item: Top100ItemType) => void
}

export function Top100ItemCard({ item, onOpen }: Props) {
  const normalizedUrl = normalizeUrl(item.url)

  // 打开外部链接（用系统浏览器）
  const handleOpenExternal = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (normalizedUrl) {
      window.open(normalizedUrl, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <div
      onClick={() => onOpen(item)}
      className="card-hover cursor-pointer rounded-xl border border-slate-700/50 bg-slate-800/60 p-4 hover:border-blue-500/40 hover:bg-slate-800/80 group"
    >
      <div className="flex items-start gap-3">
        {/* 排名 */}
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 text-sm font-bold text-blue-300">
          {item.rank}
        </div>

        <div className="min-w-0 flex-1">
          {/* 标题行 */}
          <div className="flex items-start gap-2">
            <h3
              className="line-clamp-2 text-sm font-medium text-slate-100 group-hover:text-white cursor-pointer"
              onClick={(e) => {
                e.stopPropagation()
                onOpen(item)
              }}
            >
              {item.title}
            </h3>
          </div>

          {/* 摘要 */}
          {item.summary && (
            <p className="mt-1 line-clamp-2 text-xs text-slate-400">{item.summary}</p>
          )}

          {/* 标签行 */}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span className={`rounded border px-1.5 py-0.5 text-[10px] ${categoryColors[item.category]}`}>
              {categoryNames[item.category]}
            </span>
            {item.domain === 'ai_audit' && (
              <span className="rounded border border-amber-500/40 bg-amber-500/15 px-1.5 py-0.5 text-[10px] text-amber-300">
                AI×审计
              </span>
            )}
            {item.lang && (
              <span className={`rounded border px-1.5 py-0.5 text-[10px] ${
                item.lang === 'en'
                  ? 'border-violet-500/40 bg-violet-500/15 text-violet-300'
                  : 'border-cyan-500/40 bg-cyan-500/15 text-cyan-300'
              }`}>
                {item.lang === 'en' ? 'EN' : '中'}
              </span>
            )}
            {item.verified !== false && (
              <span className="rounded border border-emerald-500/40 bg-emerald-500/15 px-1.5 py-0.5 text-[10px] text-emerald-300" title={`正文 ${item.mdLength ?? 0} 字符`}>
                ✓ 已验证
              </span>
            )}
            <span className="rounded bg-slate-700/40 px-1.5 py-0.5 text-[10px] text-slate-400">
              {item.source}
            </span>
            {item.tags && item.tags.split(',').slice(0, 3).map((tag) => (
              <span key={tag} className="rounded bg-slate-700/30 px-1.5 py-0.5 text-[10px] text-slate-500">
                {tag}
              </span>
            ))}
          </div>

          {/* 互动数据 */}
          <div className="mt-2 flex items-center gap-3 text-[11px] text-slate-500">
            {item.likes !== undefined && item.likes > 0 && (
              <span className="flex items-center gap-1">
                <ThumbsUp size={11} /> {item.likes.toLocaleString()}
              </span>
            )}
            {item.comments !== undefined && item.comments > 0 && (
              <span className="flex items-center gap-1">
                <MessageCircle size={11} /> {item.comments.toLocaleString()}
              </span>
            )}
            <span className="flex items-center gap-1 text-amber-400">
              <Star size={11} /> {item.score.toFixed(1)}
            </span>
            {/* 原文链接按钮 */}
            <a
              href={normalizedUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={handleOpenExternal}
              className="ml-auto flex items-center gap-1 text-slate-400 hover:text-blue-400 transition cursor-pointer"
              title="在浏览器中打开原文"
            >
              <ExternalLink size={11} /> 原文
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
