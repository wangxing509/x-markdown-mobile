import { Sidebar } from '@/components/layout/Sidebar'
import { Workspace } from '@/components/layout/Workspace'
import { ChatPanel } from '@/components/layout/ChatPanel'

export default function App() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950">
      <Sidebar />
      <Workspace />
      <ChatPanel />
    </div>
  )
}
