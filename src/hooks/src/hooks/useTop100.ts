import { useCallback } from 'react'
import { useStore } from '@/stores/useStore'
import { api } from '@/api/client'
import type { Category, Domain, Lang } from '@/types'

export function useTop100() {
  const {
    top100,
    top100Loading,
    top100Category,
    top100Domain,
    top100Lang,
    top100UpdateTime,
    nextRefresh,
    top100Stats,
    refreshLogs,
    setTop100,
    setTop100Loading,
    setTop100Category,
    setTop100Domain,
    setTop100Lang,
    setTop100Meta,
    setRefreshLogs,
  } = useStore()

  const fetchTop100 = useCallback(async (category?: Category, domain?: Domain, lang?: Lang) => {
    setTop100Loading(true)
    try {
      const data = await api.getTop100(category, domain, lang)
      setTop100(data.items)
      setTop100Meta(data.updateTime, data.nextRefresh, data.stats ?? null)
      if (category !== undefined) setTop100Category(category ?? null)
      if (domain !== undefined) setTop100Domain(domain ?? null)
      if (lang !== undefined) setTop100Lang(lang ?? null)
    } catch (e) {
      console.error('获取每日精选失败:', e)
    } finally {
      setTop100Loading(false)
    }
  }, [setTop100, setTop100Loading, setTop100Category, setTop100Domain, setTop100Lang, setTop100Meta])

  const loadLogs = useCallback(async () => {
    try {
      const res = await api.refreshLogs(5)
      setRefreshLogs(res.logs)
    } catch (e) {
      console.error('加载刷新日志失败:', e)
    }
  }, [setRefreshLogs])

  const refresh = useCallback(async () => {
    setTop100Loading(true)
    try {
      const res = await api.refresh()
      if (res.success) {
        await fetchTop100(
          top100Category ?? undefined,
          top100Domain ?? undefined,
          top100Lang ?? undefined,
        )
        loadLogs()
      }
      return res
    } catch (e) {
      console.error('刷新失败:', e)
      return null
    } finally {
      setTop100Loading(false)
    }
  }, [fetchTop100, top100Category, top100Domain, top100Lang, setTop100Loading, loadLogs])

  const setCategory = useCallback((c: Category | null) => {
    fetchTop100(c ?? undefined)
  }, [fetchTop100])

  const setDomain = useCallback((d: Domain | null) => {
    fetchTop100(top100Category ?? undefined, d ?? undefined, top100Lang ?? undefined)
  }, [fetchTop100, top100Category, top100Lang])

  const setLang = useCallback((l: Lang | null) => {
    fetchTop100(top100Category ?? undefined, top100Domain ?? undefined, l ?? undefined)
  }, [fetchTop100, top100Category, top100Domain])

  return {
    top100,
    loading: top100Loading,
    category: top100Category,
    domain: top100Domain,
    lang: top100Lang,
    updateTime: top100UpdateTime,
    nextRefresh,
    stats: top100Stats,
    refreshLogs,
    fetchTop100,
    refresh,
    setCategory,
    setDomain,
    setLang,
    loadLogs,
  }
}
