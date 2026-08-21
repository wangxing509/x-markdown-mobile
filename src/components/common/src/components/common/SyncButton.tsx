import { useState } from 'react'
import { Smartphone, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import { api } from '@/api/client'

function toast(type: 'success' | 'error' | 'info', message: string) {
  window.dispatchEvent(new CustomEvent('xmarkdown:toast', { detail: { type, message } }))
}

export function SyncButton() {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<string>('')

  const handleSync = async () => {
    setBusy(true)
    setResult('')
    try {
      const res = await api.syncSite({ push: true })
      if (res.success) {
        setResult('同步成功：站点已更新并推送到 GitHub Pages。')
        toast('success', '手机端站点已同步')
      } else {
        setResult(`同步未完全成功：${(res.errors || []).join('；')}`)
        toast('error', '同步失败，请查看详情')
      }
    } catch (e) {
      setResult(`同步失败：${(e as Error).message}`)
      toast('error', `同步失败：${(e as Error).message}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 rounded-md bg-emerald-600/25 px-2.5 py-1 text-xs text-emerald-300 hover:bg-emerald-600/40 transition cursor-pointer"
        title="一键同步：把桌面端内容导出并部署到手机端（GitHub Pages）"
      >
        <Smartphone size={13} /> 同步手机端
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setOpen(false)}>
          <div
            className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 p-5 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-3 flex items-center justify-between">
              <h3 className="flex items-center gap-2 text-base font-semibold text-slate-100">
                <Smartphone size={18} className="text-emerald-400" /> 同步手机端
              </h3>
              <button onClick={() => setOpen(false)} className="rounded p-1 text-slate-400 hover:bg-slate-800">
                <XCircle size={18} />
              </button>
            </div>

            <p className="mb-4 text-sm leading-relaxed text-slate-400">
              将「每日精选 + 知识库」导出为静态数据，构建手机端 PWA 站点，并推送到 GitHub Pages。
              手机端支持自动/手动刷新查看最新内容。
            </p>

            {result && (
              <div className={`mb-3 flex items-start gap-2 rounded-lg border p-3 text-sm ${
                result.startsWith('同步成功') ? 'border-emerald-600/40 bg-emerald-600/10 text-emerald-300'
                  : 'border-red-600/40 bg-red-600/10 text-red-300'
              }`}>
                {result.startsWith('同步成功') ? (
                  <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
                ) : (
                  <XCircle size={16} className="mt-0.5 shrink-0" />
                )}
                <span className="whitespace-pre-wrap break-words">{result}</span>
              </div>
            )}

            <button
              onClick={() => void handleSync()}
              disabled={busy}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60"
            >
              {busy ? <Loader2 size={16} className="animate-spin" /> : <Smartphone size={16} />}
              {busy ? '正在同步（导出→构建→推送）…' : '开始一键同步'}
            </button>
            <p className="mt-3 text-center text-xs text-slate-500">
              需要 Node.js、Python 与 git 已安装；首次使用请先在 GitHub 创建仓库。
            </p>
          </div>
        </div>
      )}
    </>
  )
}
