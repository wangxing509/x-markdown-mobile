import { useCallback, useEffect } from 'react'
import { useStore } from '@/stores/useStore'
import { api } from '@/api/client'

export function useKnowledgeBase() {
  const {
    kbItems,
    kbLoading,
    kbTree,
    kbTreeLoading,
    setKbItems,
    setKbLoading,
    setKbTree,
    setKbTreeLoading,
  } = useStore()

  const loadKb = useCallback(async () => {
    setKbLoading(true)
    try {
      const items = await api.listKnowledgeBase()
      setKbItems(items)
    } catch (e) {
      console.error('加载知识库失败:', e)
    } finally {
      setKbLoading(false)
    }
  }, [setKbItems, setKbLoading])

  const loadKbTree = useCallback(async () => {
    setKbTreeLoading(true)
    try {
      const tree = await api.getKbTree()
      setKbTree(tree)
    } catch (e) {
      console.error('加载知识库目录树失败:', e)
      setKbTree(null)
    } finally {
      setKbTreeLoading(false)
    }
  }, [setKbTree, setKbTreeLoading])

  const readArticle = useCallback(async (filepath: string) => {
    try {
      if (window.xmarkdown?.readMarkdown) {
        return await window.xmarkdown.readMarkdown(filepath)
      }
      return null
    } catch (e) {
      console.error('读取文章失败:', e)
      return null
    }
  }, [])

  const searchKb = useCallback(async (query: string, filters?: { domain?: string; lang?: string; category?: string }) => {
    try {
      return await api.searchKnowledgeBase(query, filters)
    } catch (e) {
      console.error('检索知识库失败:', e)
      return { results: [] }
    }
  }, [])

  useEffect(() => {
    loadKb()
    loadKbTree()
    const onUpdated = () => {
      void loadKb()
      void loadKbTree()
    }
    window.addEventListener('xmarkdown:kb-updated', onUpdated)
    return () => window.removeEventListener('xmarkdown:kb-updated', onUpdated)
  }, [loadKb, loadKbTree])

  return { kbItems, kbLoading, kbTree, kbTreeLoading, loadKb, loadKbTree, readArticle, searchKb }
}
