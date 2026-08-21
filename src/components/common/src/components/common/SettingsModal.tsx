import { X, Save, KeyRound, Clock, Globe2, Loader2 } from 'lucide-react'
import { useState, useEffect } from 'react'
import { useSettings } from '@/hooks/useSettings'
import { api } from '@/api/client'
import type { LlmConfig, Settings, SourceConfig } from '@/types'

interface Props {
  open: boolean
  onClose: () => void
}

export function SettingsModal({ open, onClose }: Props) {
  const { settings, llmConfig, sources, saveSettings, saveLlmConfig, toggleSource, loadAll } = useSettings()
  const [llmForm, setLlmForm] = useState<LlmConfig | null>(null)
  const [settingsForm, setSettingsForm] = useState<Settings | null>(null)
  const [bdForm, setBdForm] = useState<{ enabled: boolean; zone: string; apiKey: string } | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) {
      void loadAll()
    }
  }, [open, loadAll])

  useEffect(() => {
    if (llmConfig) setLlmForm({ ...llmConfig })
  }, [llmConfig])

  useEffect(() => {
    if (settings) setSettingsForm({ ...settings })
  }, [settings])

  useEffect(() => {
    if (open) {
      void api.brightdataConfig()
        .then((cfg) => setBdForm({ enabled: cfg.enabled, zone: cfg.zone || 'cli_unlocker', apiKey: '' }))
        .catch(() => setBdForm({ enabled: false, zone: 'cli_unlocker', apiKey: '' }))
    }
  }, [open])

  if (!open || !llmForm || !settingsForm) return null

  const saveAll = async () => {
    setSaving(true)
    try {
      await saveLlmConfig(llmForm)
      await saveSettings({
        top_n: settingsForm.top_n,
        audit_ratio: settingsForm.audit_ratio,
        schedule: settingsForm.schedule,
      })
      if (bdForm) {
        await api.saveBrightdataConfig({
          enabled: bdForm.enabled,
          zone: bdForm.zone || undefined,
          apiKey: bdForm.apiKey || undefined,
        })
      }
      window.dispatchEvent(new CustomEvent('xmarkdown:toast', {
        detail: { type: 'success', message: '设置已保存' },
      }))
      onClose()
    } catch (e) {
      window.dispatchEvent(new CustomEvent('xmarkdown:toast', {
        detail: { type: 'error', message: `保存失败：${(e as Error).message}` },
      }))
    } finally {
      setSaving(false)
    }
  }

  const toggle = async (src: SourceConfig) => {
    try {
      await toggleSource(src.name, !src.enabled)
    } catch (e) {
      window.dispatchEvent(new CustomEvent('xmarkdown:toast', {
        detail: { type: 'error', message: `切换失败：${(e as Error).message}` },
      }))
    }
  }

  const inputCls = 'w-full rounded-md border border-slate-600/50 bg-slate-900/60 px-2.5 py-1.5 text-xs text-slate-200 outline-none focus:border-blue-500'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="flex max-h-[85vh] w-[680px] flex-col overflow-hidden rounded-xl border border-slate-700 bg-slate-900 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="flex items-center gap-2 border-b border-slate-700/50 px-4 py-3">
          <h2 className="text-sm font-semibold text-slate-100">应用设置</h2>
          <button onClick={onClose} className="ml-auto rounded p-1 text-slate-400 hover:bg-slate-700/50 hover:text-slate-200 transition cursor-pointer">
            <X size={15} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-5">
          {/* 翻译通道 */}
          <section>
            <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-slate-300">
              <KeyRound size={13} className="text-emerald-400" /> LLM 翻译通道
            </h3>
            <div className="space-y-2 rounded-lg border border-slate-700/50 bg-slate-800/40 p-3">
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-1.5 text-xs text-slate-400">
                  <input
                    type="radio"
                    checked={llmForm.provider === 'local'}
                    onChange={() => setLlmForm({ ...llmForm, provider: 'local' })}
                    className="cursor-pointer"
                  />
                  本地 LLM（CodeBuddy/Ollama）
                </label>
                <label className="flex items-center gap-1.5 text-xs text-slate-400">
                  <input
                    type="radio"
                    checked={llmForm.provider === 'api'}
                    onChange={() => setLlmForm({ ...llmForm, provider: 'api' })}
                    className="cursor-pointer"
                  />
                  OpenAI 兼容 API
                </label>
              </div>
              {llmForm.provider === 'api' && (
                <>
                  <input
                    className={inputCls}
                    placeholder="API Base（如 https://api.deepseek.com/v1）"
                    value={llmForm.apiBase}
                    onChange={(e) => setLlmForm({ ...llmForm, apiBase: e.target.value })}
                  />
                  <input
                    className={inputCls}
                    type="password"
                    placeholder="API Key"
                    value={llmForm.apiKey}
                    onChange={(e) => setLlmForm({ ...llmForm, apiKey: e.target.value })}
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      className={inputCls}
                      placeholder="模型名（如 deepseek-chat）"
                      value={llmForm.model}
                      onChange={(e) => setLlmForm({ ...llmForm, model: e.target.value })}
                    />
                    <input
                      className={inputCls}
                      type="number"
                      step="0.05"
                      min="0"
                      max="1"
                      value={llmForm.temperature}
                      onChange={(e) => setLlmForm({ ...llmForm, temperature: Number(e.target.value) })}
                    />
                  </div>
                </>
              )}
              <p className="text-[11px] text-slate-500">
                优先级：API → IDE 本地 LLM → Ollama → 免费接口兜底。英文翻译质量校验失败会自动重试一次。
              </p>
            </div>
          </section>

          {/* Bright Data 兜底抓取 */}
          <section>
            <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-slate-300">
              <Globe2 size={13} className="text-emerald-400" /> Bright Data 兜底抓取
            </h3>
            <div className="space-y-2 rounded-lg border border-slate-700/50 bg-slate-800/40 p-3">
              <label className="flex items-center gap-1.5 text-xs text-slate-400">
                <input
                  type="checkbox"
                  checked={!!bdForm?.enabled}
                  onChange={(e) => setBdForm((f) => (f ? { ...f, enabled: e.target.checked } : f))}
                  className="cursor-pointer"
                />
                启用（普通抓取失败时自动改用 Bright Data 重试）
              </label>
              <input
                className={inputCls}
                type="password"
                placeholder={bdForm?.apiKey ? '已配置（留空保持不变）' : 'API Key（留空自动读取 CLI 登录凭证）'}
                value={bdForm?.apiKey ?? ''}
                onChange={(e) => setBdForm((f) => (f ? { ...f, apiKey: e.target.value } : f))}
              />
              <input
                className={inputCls}
                placeholder="区域 Zone（默认 cli_unlocker）"
                value={bdForm?.zone ?? ''}
                onChange={(e) => setBdForm((f) => (f ? { ...f, zone: e.target.value } : f))}
              />
              <p className="text-[11px] text-slate-500">
                抓取失败的页面会记录在本地，可在每日精选顶部用「BD 重试失败页」批量重爬。
              </p>
            </div>
          </section>

          {/* 每日目标与调度 */}
          <section>
            <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-slate-300">
              <Clock size={13} className="text-blue-400" /> 每日目标与调度
            </h3>
            <div className="space-y-2 rounded-lg border border-slate-700/50 bg-slate-800/40 p-3">
              <div className="grid grid-cols-3 gap-2">
                <label className="text-[11px] text-slate-400">
                  每日目标（30-50）
                  <input
                    className={`${inputCls} mt-1`}
                    type="number"
                    min={30}
                    max={50}
                    value={settingsForm.top_n}
                    onChange={(e) => setSettingsForm({ ...settingsForm, top_n: Number(e.target.value) })}
                  />
                </label>
                <label className="text-[11px] text-slate-400">
                  审计占比 %（20-30）
                  <input
                    className={`${inputCls} mt-1`}
                    type="number"
                    min={0.2}
                    max={0.3}
                    step={0.01}
                    value={settingsForm.audit_ratio}
                    onChange={(e) => setSettingsForm({ ...settingsForm, audit_ratio: Number(e.target.value) })}
                  />
                </label>
                <label className="text-[11px] text-slate-400">
                  英文占比（固定 40%）
                  <input className={`${inputCls} mt-1`} value="40%" disabled />
                </label>
              </div>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-1.5 text-xs text-slate-400">
                  <input
                    type="checkbox"
                    checked={settingsForm.schedule.enabled}
                    onChange={(e) => setSettingsForm({
                      ...settingsForm,
                      schedule: { ...settingsForm.schedule, enabled: e.target.checked },
                    })}
                    className="cursor-pointer"
                  />
                  启用每日定时
                </label>
                <label className="text-[11px] text-slate-400">
                  时
                  <input
                    className={`${inputCls} ml-1 inline-block w-16`}
                    type="number"
                    min={0}
                    max={23}
                    value={settingsForm.schedule.hour}
                    onChange={(e) => setSettingsForm({
                      ...settingsForm,
                      schedule: { ...settingsForm.schedule, hour: Number(e.target.value) },
                    })}
                  />
                </label>
                <label className="text-[11px] text-slate-400">
                  分
                  <input
                    className={`${inputCls} ml-1 inline-block w-16`}
                    type="number"
                    min={0}
                    max={59}
                    value={settingsForm.schedule.minute}
                    onChange={(e) => setSettingsForm({
                      ...settingsForm,
                      schedule: { ...settingsForm.schedule, minute: Number(e.target.value) },
                    })}
                  />
                </label>
              </div>
            </div>
          </section>

          {/* 来源启停 */}
          <section>
            <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-slate-300">
              <Globe2 size={13} className="text-violet-400" /> 来源启停（{sources.filter((s) => s.enabled).length}/{sources.length}）
            </h3>
            <div className="max-h-56 space-y-1 overflow-y-auto rounded-lg border border-slate-700/50 bg-slate-800/40 p-2">
              {sources.map((s) => (
                <div key={s.name} className="flex items-center gap-2 rounded px-2 py-1.5 hover:bg-slate-700/40">
                  <input
                    type="checkbox"
                    checked={s.enabled}
                    onChange={() => void toggle(s)}
                    className="cursor-pointer"
                  />
                  <span className="flex-1 text-xs text-slate-200">
                    {s.name}
                    {s.audit && <span className="ml-1.5 text-[10px] text-amber-400">审计×AI</span>}
                    {s.lang === 'en' && <span className="ml-1.5 text-[10px] text-violet-400">EN</span>}
                  </span>
                  <span className="text-[10px] text-slate-500">{s.kind === 'rss' ? 'RSS' : s.kind}</span>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* 底部 */}
        <div className="flex items-center justify-end gap-2 border-t border-slate-700/50 px-4 py-3">
          <button
            onClick={onClose}
            className="rounded-md bg-slate-700/60 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-700 transition cursor-pointer"
          >
            取消
          </button>
          <button
            onClick={() => void saveAll()}
            disabled={saving}
            className="flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-50 transition cursor-pointer"
          >
            {saving ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
            保存设置
          </button>
        </div>
      </div>
    </div>
  )
}
