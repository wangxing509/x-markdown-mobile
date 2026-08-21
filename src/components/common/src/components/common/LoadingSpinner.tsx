import { Loader2 } from 'lucide-react'

export function LoadingSpinner({ size = 20, text = '加载中...' }: { size?: number; text?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-8 text-slate-500">
      <Loader2 className="animate-spin" size={size} />
      <span className="text-sm">{text}</span>
    </div>
  )
}
