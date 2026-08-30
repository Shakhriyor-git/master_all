import { createContext, useContext } from 'react'
import type { Project } from '../api/projects'

export interface ActiveProjectValue {
  projects: Project[]
  isLoading: boolean
  active: Project | null
  setActive: (id: number) => void
}

export const ActiveCtx = createContext<ActiveProjectValue | null>(null)

export function useActiveProject(): ActiveProjectValue {
  const c = useContext(ActiveCtx)
  if (!c) throw new Error('useActiveProject: provider yo‘q')
  return c
}
