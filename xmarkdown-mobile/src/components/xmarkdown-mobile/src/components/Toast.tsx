import { useEffect } from 'react'
import { CheckCircle2, AlertCircle, Info } from 'lucide-react'

export function Toast({ toast, onDone }: { toast: { type: string; msg: string }; onDone: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDone, 2600)
    return () => clearTimeout(t)
  }, [toast, onDone])

  const Icon = toast.type === 'success' ? CheckCircle2 : toast.type === 'error' ? AlertCircle : Info
  const color = toast.type === 'success' ? 'text-emerald-400' : toast.type === 'error' ? 'text-red-400' : 'text-blue-400'

  return (
    <div className="fade-in pointer-events-none fixed inset-x-0 top-4 z-50 flex justify-center px-4">
      <div className="flex items-center gap-2 rounded-full bg-slate-800/95 px-4 py-2 text-sm text-slate-100 shadow-lg ring-1 ring-white/10 backdrop-blur">
        <Icon size={16} className={color} />
        <span>{toast.msg}</span>
      </div>
    </div>
  )
}
