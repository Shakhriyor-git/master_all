import { useCallback, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listProjects } from '../api/projects'
import { ActiveCtx } from './activeProjectContext'

const KEY = 'activeProjectId'

function readStored(): number | null {
  try {
    const v = localStorage.getItem(KEY)
    return v ? Number(v) : null
  } catch {
    return null
  }
}

export function ActiveProjectProvider({ children }: { children: ReactNode }) {
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects', 'active-list'],
    queryFn: () => listProjects(),
  })
  const [storedId, setStoredId] = useState<number | null>(readStored)

  const setActive = useCallback((id: number) => {
    setStoredId(id)
    try {
      localStorage.setItem(KEY, String(id))
    } catch {
      /* noop */
    }
  }, [])

  const active = useMemo(() => {
    if (!projects.length) return null
    return (
      projects.find((p) => p.id === storedId) ??
      projects.find((p) => p.status === 'active') ??
      projects[0]
    )
  }, [projects, storedId])

  return (
    <ActiveCtx.Provider value={{ projects, isLoading, active, setActive }}>
      {children}
    </ActiveCtx.Provider>
  )
}
