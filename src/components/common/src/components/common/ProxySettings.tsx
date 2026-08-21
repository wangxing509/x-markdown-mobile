import { useEffect, useState } from 'react'
import { X, Globe, Check, Loader2 } from 'lucide-react'
import { api } from '@/api/client'
import type { ProxyConfig } from '@/types'

interface ProxySettingsProps {
  open: boolean
  onClose: () => void
}

export function ProxySettings({ open, onClose }: ProxySettingsProps) {
  const [enabled, setEnabled] = useState(false)
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!open) return
    setLoading(true)
    setSaved(false)
    const fetchProxy = window.xmarkdown?.getProxy
      ? window.xmarkdown.getProxy()
      : api.getProxy()
    Promise.resolve(fetchProxy)
      .then((cfg: ProxyConfig) => {
        setEnabled(cfg.enabled)
        setUrl(cfg.url)
      })
      .catch(() => {
        setEnabled(false)
        setUrl('')
      })
      .finally(() => setLoading(false))
  }, [open])

  const handleSave = async () => {
    setSaving(true)
    setSaved(false)
    try {
      const normalized = url.trim()
      const save = window.xmarkdown?.setProxy
        ? window.xmarkdown.setProxy(enabled, normalized)
        : api.setProxy(enabled, normalized)
      const cfg: ProxyConfig = await Promise.resolve(save)
      setEnabled(cfg.enabled)
      setUrl(cfg.url)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      console.error('[代理] 保存失败:', e)
    } finally {
      setSaving(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-[460px] rounded-xl border border-slate-700/60 bg-slate-900 shadow-2xl">
        {/* 头部 */}
        <div className="flex items-center gap-2 border-b border-slate-700/50 px-5 py-3.5">
          <Globe size={18} className="text-emerald-400" />
          <span className="font-semibold text-slate-100">网络代理设置</span>
          <button
            onClick={onClose}
            className="ml-auto rounded p-1 text-slate-400 hover:bg-slate-700/50 hover:text-slate-200 transition cursor-pointer"
          >
            <X size={16} />
          </button>
        </div>

        {/* 内容 */}
        <div className="space-y-4 px-5 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-6 text-sm text-slate-400">
              <Loader2 size={16} className="mr-2 animate-spin" /> 加载中...
            </div>
          ) : (
            <>
              <p className="text-sm leading-relaxed text-slate-400">
                访问 Reddit、Hugging Face 等外网站点时需要使用代理。
                配置后下次刷新即可抓取外文内容（英文原文将正常呈现）。
              </p>

              <label className="flex cursor-pointer items-center justify-between rounded-lg bg-slate-800/50 px-3.5 py-3">
                <div>
                  <div className="text-sm font-medium text-slate-200">启用代理</div>
                  <div className="text-xs text-slate-500">关闭则直连（国内平台仍正常）</div>
                </div>
                <button
                  type="button"
                  onClick={() => setEnabled((v) => !v)}
                  className={`relative h-6 w-11 rounded-full transition cursor-pointer ${
                    enabled ? 'bg-emerald-500' : 'bg-slate-600'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all ${
                      enabled ? 'left-[22px]' : 'left-0.5'
                    }`}
                  />
                </button>
              </label>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-300">
                  代理地址
                </label>
                <input
                  type="text"
                  value={url}
                  disabled={!enabled}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="http://127.0.0.1:7890"
                  className="w-full rounded-md bg-slate-800/60 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 border border-slate-700/50 focus:border-emerald-500/50 focus:outline-none focus:ring-1 focus:ring-emerald-500/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <p className="mt-1.5 text-xs text-slate-500">
                  支持 http / https / socks5，例如 http://127.0.0.1:7890
                </p>
              </div>
            </>
          )}
        </div>

        {/* 底部 */}
        <div className="flex items-center justify-end gap-2 border-t border-slate-700/50 px-5 py-3.5">
          {saved && (
            <span className="mr-auto flex items-center gap-1 text-sm text-emerald-400">
              <Check size={14} /> 已保存
            </span>
          )}
          <button
            onClick={onClose}
            className="rounded-md px-3.5 py-1.5 text-sm text-slate-300 hover:bg-slate-700/50 transition cursor-pointer"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={loading || saving}
            className="rounded-md bg-emerald-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-emerald-500 transition disabled:opacity-50 cursor-pointer"
          >
            {saving ? '保存中...' : '保存'}
          </button>
        </div>
      </div>
    </div>
  )
}
