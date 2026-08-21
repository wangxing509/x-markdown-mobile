import { useCallback, useEffect } from 'react'
import { useStore } from '@/stores/useStore'
import { api } from '@/api/client'
import type { Settings, LlmConfig, AgentConfig } from '@/types'

export function useSettings() {
  const { agents, settings, llmConfig, sources, setAgents, setSettings, setLlmConfig, setSources } = useStore()

  const loadAll = useCallback(async () => {
    try {
      const [a, s, l, src] = await Promise.all([
        api.getAgents(),
        api.getSettings(),
        api.getLlmConfig(),
        api.getSources(),
      ])
      setAgents(a)
      setSettings(s)
      setLlmConfig(l)
      setSources(src)
    } catch (e) {
      console.error('加载设置失败:', e)
    }
  }, [setAgents, setSettings, setLlmConfig, setSources])

  useEffect(() => {
    void loadAll()
  }, [loadAll])

  const saveSettings = useCallback(async (patch: Partial<Settings>) => {
    const s = await api.saveSettings(patch)
    setSettings(s)
    return s
  }, [setSettings])

  const saveLlmConfig = useCallback(async (patch: Partial<LlmConfig>) => {
    const l = await api.saveLlmConfig(patch)
    setLlmConfig(l)
    return l
  }, [setLlmConfig])

  const toggleSource = useCallback(async (name: string, enabled: boolean) => {
    const res = await api.toggleSource(name, enabled)
    setSources(res.sources)
    return res
  }, [setSources])

  const saveAgents = useCallback(async (list: AgentConfig[]) => {
    const a = await api.saveAgents(list)
    setAgents(a)
    return a
  }, [setAgents])

  return { agents, settings, llmConfig, sources, loadAll, saveSettings, saveLlmConfig, toggleSource, saveAgents }
}
