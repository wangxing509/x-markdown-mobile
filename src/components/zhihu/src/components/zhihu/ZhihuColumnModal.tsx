import { useCallback, useEffect, useRef, useState } from 'react'
import {
  X,
  Download,
  Loader2,
  CheckCircle2,
  XCircle,
  KeyRound,
  FileSpreadsheet,
  FolderOpen,
  Newspaper,
  History,
} from 'lucide-react'
import { api } from '@/api/client'
import type { ZhihuColumnInfo, ZhihuColumnJob, ZhihuCookieStatus } from '@/types'

interface ZhihuColumnModalProps {
  open: boolean
  onClose: () => void
}

const TERMINAL: Array<ZhihuColumnJob['status']> = ['done', 'error']

export function ZhihuColumnModal({ open, onClose }: ZhihuColumnModalProps) {
  const [columnId, setColumnId] = useState('')
  const [downloadVideos, setDownloadVideos] = useState(false)
  const [autoImport, setAutoImport] = useState(true)
  const [maxItems, setMaxItems] = useState(0)
  const [outputDir, setOutputDir] = useState('')
  const [columnInfo, setColumnInfo] = useState<ZhihuColumnInfo | null>(null)
  const [columnInfoLoading, setColumnInfoLoading] = useState(false)
  const [columnInfoError, setColumnInfoError] = useState('')
  const [cookie, setCookie] = useState<ZhihuCookieStatus | null>(null)
  const [zC0, setZC0] = useState('')
  const [cookieSaved, setCookieSaved] = useState(false)
  const [cookieSaving, setCookieSaving] = useState(false)

  const [job, setJob] = useState<ZhihuColumnJob | null>(null)
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')
  const [recentJobs, setRecentJobs] = useState<ZhihuColumnJob[]>([])
  const logRef = useRef<HTMLDivElement | null>(null)

  const refreshMeta = useCallback(async () => {
    try {
      setCookie(await api.zhihuCookie())
      const res = await api.zhihuJobs()
      setRecentJobs(res.jobs)
    } catch (e) {
      console.warn('[知乎专栏] 加载状态失败:', e)
    }
  }, [])

  // 输入防抖查询专栏信息（展示作者与文章总数）
  useEffect(() => {
    const raw = columnId.trim()
    if (!raw || !open) {
      setColumnInfo(null)
      setColumnInfoError('')
      return
    }
    setColumnInfoLoading(true)
    setColumnInfoError('')
    const timer = setTimeout(async () => {
      try {
        const info = await api.zhihuColumnInfo(raw)
        setColumnInfo(info)
      } catch (e) {
        setColumnInfo(null)
        setColumnInfoError((e as Error).message || '无法获取专栏信息')
      } finally {
        setColumnInfoLoading(false)
      }
    }, 600)
    return () => {
      clearTimeout(timer)
      setColumnInfoLoading(false)
    }
  }, [columnId, open])

  useEffect(() => {
    if (!open) return
    setError('')
    setJob(null)
    setActiveJobId(null)
    refreshMeta()
  }, [open, refreshMeta])

  // 轮询任务进度
  useEffect(() => {
    if (!open || !activeJobId) return
    let stopped = false
    const timer = setInterval(async () => {
      try {
        const s = await api.zhihuStatus(activeJobId)
        if (stopped) return
        setJob(s)
        if (TERMINAL.includes(s.status)) {
          setActiveJobId(null)
          refreshMeta()
        }
      } catch (e) {
        console.warn('[知乎专栏] 状态查询失败:', e)
      }
    }, 1500)
    return () => {
      stopped = true
      clearInterval(timer)
    }
  }, [open, activeJobId, refreshMeta])

  // 日志自动滚动到底部
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [job?.logs.length])

  const handleStart = async () => {
    const col = columnId.trim()
    if (!col) {
      setError('请输入知乎专栏 ID 或链接')
      return
    }
    setError('')
    setStarting(true)
    try {
      const res = await api.zhihuStart({
        columnId: col,
        downloadVideos,
        autoImport,
        maxItems: Math.max(0, Math.floor(maxItems)),
        outputDir: outputDir.trim(),
      })
      setJob(null)
      setActiveJobId(res.jobId)
      const s = await api.zhihuStatus(res.jobId)
      setJob(s)
    } catch (e) {
      setError((e as Error).message || '启动下载失败')
    } finally {
      setStarting(false)
    }
  }

  const handleSaveCookie = async () => {
    const val = zC0.trim()
    if (!val) {
      setError('请先粘贴 z_c0 再保存')
      return
    }
    setError('')
    setCookieSaving(true)
    try {
      setCookie(await api.zhihuSaveCookie(val))
      setZC0('')
      setCookieSaved(true)
      setTimeout(() => setCookieSaved(false), 2500)
    } catch (e) {
      setError((e as Error).message || 'Cookie 保存失败')
    } finally {
      setCookieSaving(false)
    }
  }

  if (!open) return null

  const running = job && !TERMINAL.includes(job.status)
  const progressPct =
    job && job.total > 0 ? Math.min(100, Math.round((job.progress / job.total) * 100)) : 0

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="flex max-h-[90vh] w-[680px] flex-col rounded-xl border border-slate-700/60 bg-slate-900 shadow-2xl">
        {/* 头部 */}
        <div className="flex items-center gap-2 border-b border-slate-700/50 px-5 py-3.5">
          <Newspaper size={18} className="text-blue-400" />
          <span className="font-semibold text-slate-100">知乎专栏下载</span>
          <span className="rounded-full bg-slate-700/60 px-2 py-0.5 text-[10px] text-slate-300">
            输入专栏 ID，一键下载文章/回答/视频为 Markdown + Excel
          </span>
          <button
            onClick={onClose}
            className="ml-auto rounded p-1 text-slate-400 hover:bg-slate-700/50 hover:text-slate-200 transition cursor-pointer"
          >
            <X size={16} />
          </button>
        </div>

        {/* 内容区 */}
        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4">
          {error && (
            <div className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
              <XCircle size={15} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Cookie 状态 */}
          <div className="rounded-lg border border-slate-700/50 bg-slate-800/40 p-3.5">
            <div className="mb-2 flex items-center gap-2 text-sm">
              <KeyRound size={14} className="text-amber-400" />
              <span className="font-medium text-slate-200">知乎登录 Cookie（z_c0）</span>
              {cookie?.hasCookie ? (
                <span className="ml-auto flex items-center gap-1 text-xs text-emerald-400">
                  <CheckCircle2 size={13} /> 已配置 {cookie.zC0Masked}
                </span>
              ) : (
                <span className="ml-auto text-xs text-amber-400">未配置，下载可能受限</span>
              )}
            </div>
            <div className="flex gap-2">
              <input
                type="password"
                value={zC0}
                onChange={(e) => setZC0(e.target.value)}
                placeholder={
                  cookie?.hasCookie
                    ? 'z_c0 已配置，留空保持不变；如需更新请粘贴新值'
                    : '粘贴浏览器中的 z_c0（F12 → Application → Cookies → zhihu.com）'
                }
                className="min-w-0 flex-1 rounded-md bg-slate-800/60 px-3 py-2 text-xs text-slate-200 placeholder-slate-500 border border-slate-700/50 focus:border-blue-500/50 focus:outline-none focus:ring-1 focus:ring-blue-500/30 transition"
              />
              <button
                onClick={handleSaveCookie}
                disabled={cookieSaving}
                className="shrink-0 rounded-md bg-amber-500/15 px-3 py-2 text-xs text-amber-300 hover:bg-amber-500/25 transition disabled:opacity-50 cursor-pointer"
              >
                {cookieSaving ? <Loader2 size={13} className="animate-spin" /> : cookieSaved ? '已保存' : '保存'}
              </button>
            </div>
          </div>

          {/* 专栏输入 */}
          <div className="rounded-lg border border-slate-700/50 bg-slate-800/40 p-3.5">
            <label className="mb-2 block text-sm font-medium text-slate-200">
              知乎专栏 ID 或链接
            </label>
            <input
              value={columnId}
              onChange={(e) => setColumnId(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !starting && handleStart()}
              placeholder="例如：c_1020247688083775488 或 https://www.zhihu.com/column/c_1020247688083775488"
              className="w-full rounded-md bg-slate-800/60 px-3 py-2.5 text-sm text-slate-200 placeholder-slate-500 border border-slate-700/50 focus:border-blue-500/50 focus:outline-none focus:ring-1 focus:ring-blue-500/30 transition"
            />
            <div className="mt-1.5 flex items-center gap-2 text-[11px] text-slate-500">
              <span>支持专栏链接或作者个人主页（自动解析同名专栏）</span>
              {columnInfoLoading && <Loader2 size={11} className="animate-spin text-blue-400" />}
            </div>
            {columnInfo && (
              <div className="mt-2 rounded-md border border-blue-500/20 bg-blue-500/10 px-3 py-2 text-xs text-slate-200">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-blue-300">{columnInfo.columnName}</span>
                  {columnInfo.resolvedFrom && (
                    <span className="rounded bg-blue-500/20 px-1.5 py-0.5 text-[10px] text-blue-200">
                      已自动解析
                    </span>
                  )}
                </div>
                <div className="mt-1 text-slate-400">
                  作者：{columnInfo.author || '未知'} · 共 {columnInfo.itemsCount || 0} 条内容
                  {columnInfo.description && ` · ${columnInfo.description.slice(0, 40)}`}
                </div>
              </div>
            )}
            {columnInfoError && (
              <div className="mt-1.5 rounded-md bg-red-500/10 px-2.5 py-1.5 text-[11px] text-red-300">
                {columnInfoError}
              </div>
            )}
            <div className="mt-3 grid grid-cols-2 gap-3">
              <label className="flex cursor-pointer items-center justify-between rounded-lg bg-slate-800/60 px-3 py-2.5">
                <div>
                  <div className="text-xs font-medium text-slate-200">下载视频文件</div>
                  <div className="text-[11px] text-slate-500">关闭则仅在 Markdown 中保留视频链接</div>
                </div>
                <input
                  type="checkbox"
                  checked={downloadVideos}
                  onChange={(e) => setDownloadVideos(e.target.checked)}
                  className="h-4 w-4 accent-blue-500"
                />
              </label>
              <label className="flex cursor-pointer items-center justify-between rounded-lg bg-slate-800/60 px-3 py-2.5">
                <div>
                  <div className="text-xs font-medium text-slate-200">最大条数</div>
                  <div className="text-[11px] text-slate-500">0 = 全部下载</div>
                </div>
                <input
                  type="number"
                  min={0}
                  value={maxItems}
                  onChange={(e) => setMaxItems(parseInt(e.target.value || '0', 10))}
                  className="w-16 rounded-md bg-slate-800/80 px-2 py-1 text-right text-xs text-slate-200 border border-slate-700/50 focus:border-blue-500/50 focus:outline-none"
                />
              </label>
            </div>
            <label className="mt-2 flex cursor-pointer items-center justify-between rounded-lg bg-slate-800/60 px-3 py-2.5">
              <div>
                <div className="text-xs font-medium text-slate-200">下载完成后自动导入知识库</div>
                <div className="text-[11px] text-slate-500">导入后可在左侧知识库中查看、编辑、预览与发布</div>
              </div>
              <input
                type="checkbox"
                checked={autoImport}
                onChange={(e) => setAutoImport(e.target.checked)}
                className="h-4 w-4 accent-blue-500"
              />
            </label>
            <div className="mt-2">
              <label className="block text-[11px] text-slate-500">
                保存目录（可选，默认 ~/.xmarkdown/zhihu）
              </label>
              <input
                value={outputDir}
                onChange={(e) => setOutputDir(e.target.value)}
                placeholder="留空使用默认目录"
                className="mt-1 w-full rounded-md bg-slate-800/60 px-3 py-2 text-xs text-slate-200 placeholder-slate-500 border border-slate-700/50 focus:border-blue-500/50 focus:outline-none transition"
              />
            </div>
            <button
              onClick={handleStart}
              disabled={starting}
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-500 transition disabled:opacity-50 cursor-pointer"
            >
              {starting ? (
                <>
                  <Loader2 size={15} className="animate-spin" /> 正在启动...
                </>
              ) : (
                <>
                  <Download size={15} /> 开始下载
                </>
              )}
            </button>
          </div>

          {/* 任务进度 */}
          {job && (
            <div className="rounded-lg border border-slate-700/50 bg-slate-800/40 p-3.5">
              {job.resolvedFrom && (
                <div className="mb-2 rounded-md bg-blue-500/10 px-2.5 py-1.5 text-xs text-blue-300">
                  {job.resolvedFrom}
                </div>
              )}
              <div className="mb-2 flex items-center gap-2 text-sm">
                <span className="font-medium text-slate-200">{job.columnName || job.columnId}</span>
                {running ? (
                  <span className="flex items-center gap-1 text-xs text-blue-400">
                    <Loader2 size={12} className="animate-spin" />{' '}
                    {job.status === 'scanning'
                      ? '正在扫描'
                      : job.status === 'importing'
                        ? '正在导入知识库'
                        : '正在下载'}
                  </span>
                ) : job.status === 'done' ? (
                  <span className="flex items-center gap-1 text-xs text-emerald-400">
                    <CheckCircle2 size={12} /> 已完成
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs text-red-400">
                    <XCircle size={12} /> 失败
                  </span>
                )}
                {job.total > 0 && (
                  <span className="ml-auto text-xs text-slate-400">
                    {job.progress} / {job.total}（{progressPct}%）
                  </span>
                )}
              </div>

              {job.total > 0 && (
                <div className="mb-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-700/60">
                  <div
                    className={`h-full rounded-full transition-all ${
                      job.status === 'error' ? 'bg-red-500' : 'bg-blue-500'
                    }`}
                    style={{ width: `${progressPct}%` }}
                  />
                </div>
              )}

              {job.currentTitle && (
                <div className="mb-2 truncate text-xs text-slate-400">
                  当前：{job.currentTitle}
                </div>
              )}

              {/* 日志 */}
              <div
                ref={logRef}
                className="max-h-40 overflow-y-auto rounded-md bg-slate-950/70 p-2 font-mono text-[11px] leading-relaxed text-slate-400"
              >
                {job.logs.length === 0 ? (
                  <div className="text-slate-600">等待任务日志...</div>
                ) : (
                  job.logs.slice(-30).map((line, i) => <div key={i}>{line}</div>)
                )}
              </div>

              {/* 结果 */}
              {job.status === 'done' && (
                <div className="mt-3 space-y-2 rounded-md bg-emerald-500/5 p-3 text-xs text-slate-300">
                  <div className="flex items-center gap-2">
                    <FileSpreadsheet size={14} className="shrink-0 text-emerald-400" />
                    <span className="break-all">{job.excelPath || 'Excel 生成中...'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <FolderOpen size={14} className="shrink-0 text-blue-400" />
                    <span className="break-all">{job.outputDir || '输出目录'}</span>
                  </div>
                  {job.importResult && (
                    <div className="text-slate-300">
                      知识库导入：新增 {job.importResult.imported} 篇
                      {job.importResult.skipped > 0 && `，跳过重复 ${job.importResult.skipped} 篇`}
                      {job.importResult.failed > 0 && `，失败 ${job.importResult.failed} 篇`}
                    </div>
                  )}
                  {job.items.filter((i) => i.status === 'error').length > 0 && (
                    <div className="text-red-400">
                      {job.items.filter((i) => i.status === 'error').length} 条处理失败，详见日志
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* 最近任务 */}
          {recentJobs.length > 0 && (
            <div className="rounded-lg border border-slate-700/50 bg-slate-800/40 p-3.5">
              <div className="mb-2 flex items-center gap-2 text-sm text-slate-300">
                <History size={14} className="text-slate-500" />
                <span className="font-medium">最近任务</span>
              </div>
              <div className="space-y-1.5">
                {recentJobs.slice(0, 5).map((j) => (
                  <button
                    key={j.jobId}
                    onClick={() => {
                      setActiveJobId(j.jobId)
                      setJob(j)
                    }}
                    className="flex w-full items-center gap-2 rounded-md bg-slate-800/60 px-3 py-2 text-left text-xs text-slate-300 hover:bg-slate-700/50 transition cursor-pointer"
                  >
                    <span className="truncate">{j.columnName || j.columnId}</span>
                    <span className="ml-auto shrink-0 text-[10px] text-slate-500">{j.createdAt}</span>
                    {TERMINAL.includes(j.status) ? (
                      j.status === 'done' ? (
                        <CheckCircle2 size={13} className="shrink-0 text-emerald-400" />
                      ) : (
                        <XCircle size={13} className="shrink-0 text-red-400" />
                      )
                    ) : (
                      <Loader2 size={13} className="shrink-0 animate-spin text-blue-400" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          <p className="text-[11px] leading-relaxed text-slate-500">
            说明：下载需要知乎 Cookie（z_c0），未登录时部分正文可能无法获取。
            生成的 Excel 包含类型 / 标题 / 链接 / 创建时间 / 更新时间 / 简介 / 评论数 / 赞同数。
          </p>
        </div>
      </div>
    </div>
  )
}
