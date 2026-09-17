import { useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { IconMusic, IconRefresh, IconTrash } from '@tabler/icons-react'
import { patchMe, type Me } from '../api/me'
import {
  deleteTrack,
  listTracks,
  uploadTrack,
  type TracksInfo,
} from '../api/tracks'
import { Screen } from '../components/Screen'
import { Segment } from '../components/Segment'
import { useMe } from '../hooks/useMe'
import { useTheme } from '../theme/themeContext'
import type { ThemePref } from '../api/me'
import { confirmDialog } from '../lib/telegram'
import { BUILD_SHORT, forceReload, readVersionDebug } from '../lib/version'

const THEME_OPTIONS: { value: ThemePref; label: string }[] = [
  { value: 'light', label: 'Kunduzgi' },
  { value: 'dark', label: 'Tungi' },
  { value: 'auto', label: 'Avtomatik' },
]

function mb(n: number): string {
  return (n / 1024 / 1024).toFixed(1)
}

export function Settings() {
  const { pref, setPref } = useTheme()

  return (
    <Screen title="Sozlamalar">
      <Row label="Mavzu">
        <Segment options={THEME_OPTIONS} value={pref} onChange={setPref} />
      </Row>

      <MusicSettings />

      <Row label="Til">
        <Segment
          options={[{ value: 'uz', label: "O'zbekcha" }]}
          value="uz"
          onChange={() => {}}
        />
        <p className="mt-1 text-label text-text-faint">
          Rus tili keyin qo‘shiladi.
        </p>
      </Row>

      <p className="mt-6 flex items-center justify-center gap-1.5 text-label text-text-faint">
        Versiya {BUILD_SHORT}
        <button
          type="button"
          aria-label="Yangilash"
          title="Yangilash"
          onClick={forceReload}
          className="rounded-full p-1 active:bg-surface-2"
        >
          <IconRefresh size={14} />
        </button>
      </p>
      <p className="mt-1 text-center text-label text-text-faint">
        {readVersionDebug()}
      </p>
    </Screen>
  )
}

function MusicSettings() {
  const { data: me } = useMe()
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [progress, setProgress] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const tracksQ = useQuery({ queryKey: ['tracks'], queryFn: listTracks })

  const setEnabled = useMutation({
    mutationFn: (on: boolean) => patchMe({ music_enabled: on }),
    onSuccess: (data: Me) => qc.setQueryData(['me'], data),
  })

  const del = useMutation({
    mutationFn: (id: number) => deleteTrack(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tracks'] }),
  })

  async function onFile(file: File) {
    setError(null)
    setProgress(0)
    try {
      const info = await uploadTrack(file, setProgress)
      qc.setQueryData(['tracks'], info)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Yuklab bo‘lmadi')
    } finally {
      setProgress(null)
    }
  }

  const info: TracksInfo | undefined = tracksQ.data
  const total = info?.total_bytes ?? 0
  const limit = info?.limit_bytes ?? 15 * 1024 * 1024
  const remaining = info?.remaining_bytes ?? limit
  const pct = Math.min(100, Math.round((total / limit) * 100))
  const full = remaining < 100 * 1024 // ~0.1 MB dan kam

  return (
    <Row label="Musiqa">
      <label className="flex items-center justify-between">
        <span className="text-body text-text">Ko‘rsatilsin</span>
        <Toggle
          on={!!me?.music_enabled}
          onChange={(v) => setEnabled.mutate(v)}
        />
      </label>

      <div className="mt-3 text-label text-text-muted">
        Yuklangan: {mb(total)} MB / {mb(limit)} MB
      </div>
      <div className="mt-1 h-1.5 overflow-hidden rounded-chip bg-surface-2">
        <span
          className="block h-full bg-primary"
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="mt-3 space-y-1.5">
        {(info?.tracks ?? []).map((t) => (
          <div
            key={t.id}
            className="flex items-center gap-2 rounded-btn bg-surface-2 px-3 py-2"
          >
            <IconMusic size={15} className="shrink-0 text-primary" />
            <span className="min-w-0 flex-1 truncate text-body text-text">
              {t.original_name}
            </span>
            <span className="shrink-0 text-label text-text-faint">
              {mb(t.size_bytes)} MB
            </span>
            <button
              type="button"
              aria-label="O‘chirish"
              disabled={del.isPending}
              onClick={async () => {
                if (await confirmDialog(`"${t.original_name}" o‘chirilsinmi?`)) {
                  del.mutate(t.id)
                }
              }}
              className="shrink-0 text-text-faint active:text-danger"
            >
              <IconTrash size={16} />
            </button>
          </div>
        ))}
      </div>

      {progress !== null ? (
        <div className="mt-3">
          <div className="h-1.5 overflow-hidden rounded-chip bg-surface-2">
            <span
              className="block h-full bg-primary transition-[width]"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="mt-1 text-label text-text-muted">
            Yuklanmoqda… {progress}%
          </div>
        </div>
      ) : (
        <button
          type="button"
          disabled={full}
          onClick={() => fileRef.current?.click()}
          className="mt-3 w-full rounded-btn border border-dashed border-border py-2.5 text-label text-primary active:bg-surface-2 disabled:opacity-50"
        >
          + Musiqa yuklash
        </button>
      )}
      {full && progress === null && (
        <p className="mt-1 text-label text-text-faint">
          Joy tugadi — avval bir nechta trekni o‘chiring
        </p>
      )}
      {error && <p className="mt-1 text-label text-danger">{error}</p>}

      <input
        ref={fileRef}
        type="file"
        accept="audio/*"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0]
          e.target.value = ''
          if (f) void onFile(f)
        }}
      />
    </Row>
  )
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="mt-3 rounded-card border border-border bg-surface p-4">
      <div className="mb-2 text-label text-text-muted">{label}</div>
      {children}
    </div>
  )
}

function Toggle({
  on,
  onChange,
}: {
  on: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className={`h-7 w-12 rounded-chip p-1 transition-colors ${
        on ? 'bg-primary' : 'bg-surface-2'
      }`}
    >
      <span
        className={`block h-5 w-5 rounded-full transition-transform ${
          on ? 'translate-x-5 bg-on-primary' : 'bg-text-faint'
        }`}
      />
    </button>
  )
}
