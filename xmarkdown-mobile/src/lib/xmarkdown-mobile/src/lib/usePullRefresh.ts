import { useRef, useState, useCallback, useEffect } from 'react'

interface PullResult {
  pullRef: React.RefObject<HTMLDivElement>
  pulling: boolean
  distance: number
}

/** 下拉刷新：在顶部容器上监听触摸，向下拉动超过阈值触发 onRefresh */
export function usePullRefresh(onRefresh: () => Promise<void> | void): PullResult {
  const pullRef = useRef<HTMLDivElement>(null)
  const [pulling, setPulling] = useState(false)
  const [distance, setDistance] = useState(0)
  const startY = useRef(0)
  const pullingRef = useRef(false)

  const handleTouchStart = useCallback((e: TouchEvent) => {
    const el = pullRef.current
    if (!el) return
    if (el.scrollTop <= 0) {
      startY.current = e.touches[0].clientY
      pullingRef.current = true
    }
  }, [])

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (!pullingRef.current) return
    const dy = e.touches[0].clientY - startY.current
    if (dy > 0 && dy < 140) {
      setPulling(true)
      setDistance(dy)
    }
  }, [])

  const handleTouchEnd = useCallback(() => {
    if (!pullingRef.current) return
    pullingRef.current = false
    if (distance >= 70) {
      setPulling(true)
      setDistance(60) // 保持指示器可见
      Promise.resolve(onRefresh()).finally(() => {
        setPulling(false)
        setDistance(0)
      })
    } else {
      setPulling(false)
      setDistance(0)
    }
  }, [distance, onRefresh])

  useEffect(() => {
    const el = pullRef.current
    if (!el) return
    el.addEventListener('touchstart', handleTouchStart, { passive: true })
    el.addEventListener('touchmove', handleTouchMove, { passive: true })
    el.addEventListener('touchend', handleTouchEnd)
    return () => {
      el.removeEventListener('touchstart', handleTouchStart)
      el.removeEventListener('touchmove', handleTouchMove)
      el.removeEventListener('touchend', handleTouchEnd)
    }
  }, [handleTouchStart, handleTouchMove, handleTouchEnd])

  return { pullRef, pulling, distance }
}
