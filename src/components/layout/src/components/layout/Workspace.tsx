import { Top100List } from '@/components/top100/Top100List'
import { MarkdownEditor } from '@/components/markdown/MarkdownEditor'
import { ThemeSwitcher } from '@/components/markdown/ThemeSwitcher'
import { TranslateButton } from '@/components/markdown/TranslateButton'
import { DistillButton } from '@/components/markdown/DistillButton'
import { DownloadButton } from '@/components/markdown/DownloadButton'
import { CopyButton } from '@/components/markdown/CopyButton'
import { SaveToKbButton } from '@/components/markdown/SaveToKbButton'
import { PublishButton } from '@/components/markdown/PublishButton'
import { ProxySettings } from '@/components/common/ProxySettings'
import { SettingsModal } from '@/components/common/SettingsModal'
import { ZhihuColumnModal } from '@/components/zhihu/ZhihuColumnModal'
import { SyncButton } from '@/components/common/SyncButton'
import { Globe, Newspaper, Settings } from 'lucide-react'
import { useState } from 'react'
import { useStore } from '@/stores/useStore'

export function Workspace() {
  const { currentArticle, setWorkspaceTab, workspaceTab } = useStore()
  const [proxyOpen, setProxyOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [zhihuOpen, setZhihuOpen] = useState(false)

  return (
    <main className="flex h-full flex-1 flex-col bg-slate-900/40">
      {/* 顶部工具栏 */}
      <header className="flex flex-wrap items-center gap-3 border-b border-slate-700/50 bg-slate-800/40 px-4 py-2 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            X markdown
          </h1>
        </div>

        {/* 操作按钮组 */}
        {currentArticle && (
          <div className="flex items-center gap-2">
            <TranslateButton />
            <DistillButton />
            <SaveToKbButton />
            <PublishButton />
            <DownloadButton />
            <CopyButton />
          </div>
        )}

        <div className="ml-auto flex items-center gap-3">
          <button
            onClick={() => setSettingsOpen(true)}
            className="flex items-center gap-1.5 rounded-md bg-slate-700/60 px-2.5 py-1 text-xs text-slate-200 hover:bg-slate-700 transition cursor-pointer"
            title="应用设置（翻译通道/调度/来源）"
          >
            <Settings size={13} /> 设置
          </button>
          <button
            onClick={() => setZhihuOpen(true)}
            className="flex items-center gap-1.5 rounded-md bg-blue-600/25 px-2.5 py-1 text-xs text-blue-300 hover:bg-blue-600/40 transition cursor-pointer"
            title="知乎专栏下载：输入专栏 ID 批量下载文章/回答/视频，保存为 Markdown 并生成 Excel"
          >
            <Newspaper size={13} /> 知乎专栏
          </button>
          <button
            onClick={() => setProxyOpen(true)}
            className="flex items-center gap-1.5 rounded-md bg-slate-700/60 px-2.5 py-1 text-xs text-slate-200 hover:bg-slate-700 transition cursor-pointer"
            title="网络代理设置（抓取外网内容需要）"
          >
            <Globe size={13} /> 代理设置
          </button>
          <SyncButton />
          <ThemeSwitcher />
          {currentArticle && (
            <button
              onClick={() => setWorkspaceTab('list')}
              className="shrink-0 rounded-md bg-slate-700/60 px-2.5 py-1 text-xs text-slate-200 hover:bg-slate-700 transition cursor-pointer"
            >
              返回列表
            </button>
          )}
        </div>
      </header>

      {/* 主内容区 */}
      <div className="flex-1 overflow-hidden">
        {currentArticle && workspaceTab !== 'list' ? (
          <MarkdownEditor />
        ) : (
          <Top100List />
        )}
      </div>

      {/* 代理设置弹窗 */}
      <ProxySettings open={proxyOpen} onClose={() => setProxyOpen(false)} />
      {/* 应用设置弹窗 */}
      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      {/* 知乎专栏下载弹窗 */}
      <ZhihuColumnModal open={zhihuOpen} onClose={() => setZhihuOpen(false)} />
    </main>
  )
}
