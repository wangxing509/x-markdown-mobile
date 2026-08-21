import { useStore } from '@/stores/useStore'
import { MarkdownPreview } from './MarkdownPreview'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

export function MarkdownEditor() {
  const {
    currentMarkdown,
    currentTranslatedMarkdown,
    currentSkillMarkdown,
    showTranslated,
    showSkill,
    setCurrentMarkdown,
    workspaceTab,
    markdownLoading,
    currentArticle,
  } = useStore()

  if (markdownLoading) {
    return <LoadingSpinner text="正在获取原文 Markdown..." />
  }

  // 根据切换状态决定显示哪份内容
  // 优先级：Skill > 译文 > 原文（译文/Skill 为空时回退原文，避免空内容导致锁死编辑）
  const displayContent = showSkill && currentSkillMarkdown
    ? currentSkillMarkdown
    : showTranslated && currentTranslatedMarkdown
      ? currentTranslatedMarkdown
      : currentMarkdown

  // 编辑模式只能编辑原文（译文/Skill 是只读预览），且必须有内容才视为只读
  const isReadOnly =
    (showSkill && !!currentSkillMarkdown) ||
    (showTranslated && !!currentTranslatedMarkdown)

  return (
    <div className="flex h-full flex-col">
      {/* 文章信息 */}
      {currentArticle && (
        <div className="border-b border-slate-700/50 bg-slate-800/30 px-4 py-2">
          <h2 className="text-sm font-semibold text-slate-100">{currentArticle.title}</h2>
          <p className="mt-0.5 text-xs text-slate-500">
            {currentArticle.source} · {currentArticle.category}
            {showSkill && <span className="ml-2 text-amber-400">[Skill]</span>}
            {showTranslated && <span className="ml-2 text-emerald-400">[译文]</span>}
          </p>
        </div>
      )}

      {/* 编辑/预览切换 */}
      <div className="flex items-center gap-1 border-b border-slate-700/50 bg-slate-800/20 px-3 py-1.5">
        {(['editor', 'preview', 'split'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => useStore.getState().setWorkspaceTab(tab)}
            disabled={isReadOnly && tab === 'editor'}
            className={`rounded px-3 py-1 text-xs font-medium transition cursor-pointer ${
              workspaceTab === tab
                ? 'bg-blue-600 text-white'
                : 'text-slate-300 hover:bg-slate-700/40'
            } ${isReadOnly && tab === 'editor' ? 'opacity-30 cursor-not-allowed' : ''}`}
          >
            {tab === 'editor' ? '编辑' : tab === 'preview' ? '预览' : '分栏'}
          </button>
        ))}
        {/* 当前显示模式提示 */}
        <div className="ml-auto text-xs text-slate-500">
          {showSkill ? '正在预览 Skill' : showTranslated ? '正在预览译文' : '原文'}
        </div>
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-hidden">
        {workspaceTab === 'editor' && !isReadOnly && (
          <textarea
            value={currentMarkdown}
            onChange={(e) => setCurrentMarkdown(e.target.value)}
            className="h-full w-full resize-none bg-slate-900 p-4 font-mono text-sm text-slate-200 outline-none border-none focus:ring-1 focus:ring-blue-500/30"
            spellCheck={false}
          />
        )}
        {workspaceTab === 'editor' && isReadOnly && (
          // 只读模式下编辑器位置显示预览
          <MarkdownPreview content={displayContent} />
        )}
        {workspaceTab === 'preview' && (
          <MarkdownPreview content={displayContent} />
        )}
        {workspaceTab === 'split' && (
          <div className="flex h-full">
            {!isReadOnly ? (
              <>
                <textarea
                  value={currentMarkdown}
                  onChange={(e) => setCurrentMarkdown(e.target.value)}
                  className="h-full w-1/2 resize-none bg-slate-900 p-4 font-mono text-sm text-slate-200 outline-none border-r border-slate-700/50"
                  spellCheck={false}
                />
                <div className="w-1/2 overflow-y-auto">
                  <MarkdownPreview content={currentMarkdown} />
                </div>
              </>
            ) : (
              <div className="w-full overflow-y-auto">
                <MarkdownPreview content={displayContent} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
