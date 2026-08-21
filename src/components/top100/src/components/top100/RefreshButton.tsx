import { RefreshCw } from 'lucide-react'
import { useTop100 } from '@/hooks/useTop100'

export function RefreshButton() {
  const { refresh, loading } = useTop100()
  return (
    <button
      onClick={refresh}
      disabled={loading}
      className="card-hover flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white shadow-soft hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 transition cursor-pointer"
    >
      <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
      <span>{loading ? '刷新中...' : '手动刷新'}</span>
    </button>
  )
}
