import type { ReactNode } from 'react'
import { BottomNav } from './BottomNav'

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto flex min-h-full max-w-md flex-col bg-bg">
      <main className="flex-1 pb-24">{children}</main>
      <BottomNav />
    </div>
  )
}
