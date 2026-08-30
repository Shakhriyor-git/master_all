import { createContext, useContext } from 'react'
import type { Scheme } from '../lib/telegram'
import type { ThemePref } from '../api/me'

export interface ThemeCtxValue {
  pref: ThemePref
  resolved: Scheme
  setPref: (p: ThemePref) => void
}

export const ThemeCtx = createContext<ThemeCtxValue | null>(null)

export function useTheme(): ThemeCtxValue {
  const c = useContext(ThemeCtx)
  if (!c) throw new Error('useTheme: ThemeProvider ichida ishlatilsin')
  return c
}
