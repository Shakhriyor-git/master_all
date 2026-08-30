import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import {
  applyTelegramChrome,
  getColorScheme,
  onSchemeChange,
  type Scheme,
} from '../lib/telegram'
import type { ThemePref } from '../api/me'
import { ThemeCtx } from './themeContext'

interface Props {
  children: ReactNode
  pref: ThemePref
  onPrefChange?: (p: ThemePref) => void
}

export function ThemeProvider({ children, pref, onPrefChange }: Props) {
  const [scheme, setScheme] = useState<Scheme>(getColorScheme)
  const [localPref, setLocalPref] = useState<ThemePref>(pref)
  const lastPref = useRef(pref)

  if (pref !== lastPref.current) {
    lastPref.current = pref
    setLocalPref(pref)
  }

  useEffect(() => onSchemeChange(() => setScheme(getColorScheme())), [])

  const resolved: Scheme = localPref === 'auto' ? scheme : localPref

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', resolved)
    applyTelegramChrome(resolved)
  }, [resolved])

  function setPref(p: ThemePref) {
    setLocalPref(p)
    onPrefChange?.(p)
  }

  return (
    <ThemeCtx.Provider value={{ pref: localPref, resolved, setPref }}>
      {children}
    </ThemeCtx.Provider>
  )
}
