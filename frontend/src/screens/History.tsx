import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import type { Entry, EntryKind } from '../api/entries'
import { EntryCard } from '../components/EntryCard'
import { EntryDetailSheet } from '../components/EntryDetailSheet'
import { ProjectPicker } from '../components/ProjectPicker'
import { EmptyState, Screen } from '../components/Screen'
import { Segment } from '../components/Segment'
import { SplashSkeleton } from '../components/states'
import { useActiveProject } from '../hooks/activeProjectContext'
import { useDeleteEntry, useEntries } from '../hooks/useEntries'
import { fmtDateGroup } from '../lib/format'
import { confirmDialog, hapticSuccess } from '../lib/telegram'
import { IconSelector } from '@tabler/icons-react'

type FilterKind = 'all' | EntryKind

const FILTERS: { value: FilterKind; label: string }[] = [
  { value: 'all', label: 'Barchasi' },
  { value: 'work', label: 'Ishlar' },
  { value: 'material', label: 'Material' },
  { value: 'expense', label: 'Xarajat' },
]

export function History() {
  const { active, projects, isLoading, setActive } = useActiveProject()
  const [params, setParams] = useSearchParams()
  const [pickerOpen, setPickerOpen] = useState(false)
  const [selected, setSelected] = useState<Entry | null>(null)

  const kindParam = params.get('kind') as FilterKind | null
  const filter: FilterKind =
    kindParam && FILTERS.some((f) => f.value === kindParam) ? kindParam : 'all'

  const q = useEntries({
    projectId: active?.id ?? 0,
    kind: filter === 'all' ? undefined : filter,
  })
  const del = useDeleteEntry(active?.id ?? 0)

  const entries = useMemo(
    () => q.data?.pages.flatMap((p) => p.items) ?? [],
    [q.data],
  )
  const groups = useMemo(() => groupByDay(entries), [entries])

  const sentinel = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = sentinel.current
    if (!el) return
    const io = new IntersectionObserver((e) => {
      if (e[0].isIntersecting && q.hasNextPage && !q.isFetchingNextPage) {
        void q.fetchNextPage()
      }
    })
    io.observe(el)
    return () => io.disconnect()
  }, [q])

  if (isLoading) return <SplashSkeleton />
  if (!active) {
    return (
      <Screen title="Tarix">
        <EmptyState text="Obyekt topilmadi." />
      </Screen>
    )
  }

  async function quickDelete(e: Entry) {
    const ok = await confirmDialog('Bu yozuv o‘chirilsinmi?')
    if (!ok) return
    await del.mutateAsync(e.id)
    hapticSuccess()
  }

  return (
    <Screen
      title="Tarix"
      action={
        projects.length > 1 && (
          <button
            type="button"
            onClick={() => setPickerOpen(true)}
            className="flex items-center gap-1 rounded-chip bg-surface-2 px-3 py-1 text-label text-text-muted"
          >
            <span className="max-w-[9rem] truncate">{active.title}</span>
            <IconSelector size={14} />
          </button>
        )
      }
    >
      <div className="sticky top-0 z-10 -mx-4 bg-bg px-4 pb-2">
        <Segment
          options={FILTERS}
          value={filter}
          onChange={(v) => {
            const next = new URLSearchParams(params)
            if (v === 'all') next.delete('kind')
            else next.set('kind', v)
            setParams(next, { replace: true })
          }}
        />
      </div>

      {q.isPending ? (
        <SkeletonList />
      ) : entries.length === 0 ? (
        <EmptyState text="Bu bo‘limda hali yozuv yo‘q." />
      ) : (
        <div className="space-y-4">
          {groups.map((g) => (
            <div key={g.key}>
              <h3 className="mb-1.5 text-label uppercase text-text-muted">
                {fmtDateGroup(g.date)}
              </h3>
              <div className="space-y-2">
                {g.items.map((e) => (
                  <EntryCard
                    key={e.id}
                    entry={e}
                    onOpen={setSelected}
                    onDelete={quickDelete}
                  />
                ))}
              </div>
            </div>
          ))}
          <div ref={sentinel} className="h-8" />
          {q.isFetchingNextPage && (
            <p className="text-center text-label text-text-faint">
              Yuklanmoqda…
            </p>
          )}
        </div>
      )}

      <ProjectPicker
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        projects={projects}
        activeId={active.id}
        onPick={setActive}
      />
      <EntryDetailSheet
        projectId={active.id}
        entry={selected}
        onClose={() => setSelected(null)}
      />
    </Screen>
  )
}

interface DayGroup {
  key: string
  date: string
  items: Entry[]
}

function groupByDay(items: Entry[]): DayGroup[] {
  const map = new Map<string, DayGroup>()
  for (const e of items) {
    const key = e.entry_date.slice(0, 10)
    if (!map.has(key)) map.set(key, { key, date: e.entry_date, items: [] })
    map.get(key)!.items.push(e)
  }
  return [...map.values()]
}

function SkeletonList() {
  return (
    <div className="space-y-2">
      {[0, 1, 2, 3].map((i) => (
        <div
          key={i}
          className="h-20 animate-pulse rounded-card border border-border bg-surface"
        />
      ))}
    </div>
  )
}
