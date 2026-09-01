import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listTracks, trackAudioUrl } from '../api/tracks'
import { useMe } from '../hooks/useMe'
import { MusicCtx, type MusicState } from './musicContext'

export function MusicProvider({ children }: { children: ReactNode }) {
  const { data: me } = useMe()
  const enabled = !!me?.music_enabled

  const tracksQ = useQuery({
    queryKey: ['tracks'],
    queryFn: listTracks,
    enabled,
    staleTime: 60_000,
  })
  const tracks = useMemo(() => tracksQ.data?.tracks ?? [], [tracksQ.data])

  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [index, setIndex] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [loading, setLoading] = useState(false)

  const available = enabled && tracks.length > 0

  const playIndex = useCallback(
    (i: number) => {
      const el = audioRef.current
      const list = tracks
      if (!el || list.length === 0) return
      const next = ((i % list.length) + list.length) % list.length
      setIndex(next)
      el.src = trackAudioUrl(list[next])
      setLoading(true)
      el.play().catch(() => {
        // fayl topilmadi / format qo'llab-quvvatlanmaydi — jimgina to'xtaydi
        setPlaying(false)
        setLoading(false)
      })
    },
    [tracks],
  )

  const toggle = useCallback(() => {
    const el = audioRef.current
    if (!el || tracks.length === 0) return
    if (playing) {
      el.pause()
      return
    }
    if (!el.src) {
      playIndex(index)
    } else {
      setLoading(true)
      el.play().catch(() => {
        setPlaying(false)
        setLoading(false)
      })
    }
  }, [playing, tracks.length, index, playIndex])

  const restart = useCallback(() => {
    const el = audioRef.current
    if (!el || tracks.length === 0) return
    if (!el.src) {
      playIndex(index)
      return
    }
    el.currentTime = 0
    setLoading(true)
    el.play().catch(() => {
      setPlaying(false)
      setLoading(false)
    })
  }, [tracks.length, index, playIndex])

  // Musiqa o'chirilsa yoki treklar yo'qolsa — to'xtatamiz
  useEffect(() => {
    if (!available && audioRef.current) {
      audioRef.current.pause()
      audioRef.current.removeAttribute('src')
      setPlaying(false)
      setLoading(false)
    }
  }, [available])

  const value = useMemo<MusicState>(
    () => ({
      available,
      tracks,
      index,
      playing,
      loading,
      toggle,
      restart,
      playIndex,
    }),
    [available, tracks, index, playing, loading, toggle, restart, playIndex],
  )

  return (
    <MusicCtx.Provider value={value}>
      <audio
        ref={audioRef}
        preload="none"
        onPlaying={() => {
          setPlaying(true)
          setLoading(false)
        }}
        onPause={() => setPlaying(false)}
        onWaiting={() => setLoading(true)}
        onEnded={() => playIndex(index + 1)}
        onError={() => {
          setPlaying(false)
          setLoading(false)
        }}
      />
      {children}
    </MusicCtx.Provider>
  )
}
