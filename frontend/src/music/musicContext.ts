import { createContext, useContext } from 'react'
import type { Track } from '../api/tracks'

export interface MusicState {
  /** music_enabled && kamida bitta trek */
  available: boolean
  tracks: Track[]
  index: number
  playing: boolean
  loading: boolean
  toggle: () => void
  restart: () => void
  playIndex: (i: number) => void
}

export const MusicCtx = createContext<MusicState | null>(null)

export function useMusic(): MusicState {
  const v = useContext(MusicCtx)
  if (!v) throw new Error('useMusic MusicProvider ichida ishlatilsin')
  return v
}
