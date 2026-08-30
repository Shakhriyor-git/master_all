import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { Reorder } from 'framer-motion'
import {
  IconGripVertical,
  IconPin,
  IconPinFilled,
  IconPlus,
  IconTrash,
} from '@tabler/icons-react'
import type { NoteItem } from '../api/notes'
import { BottomSheet } from '../components/BottomSheet'
import { EmptyState, Screen } from '../components/Screen'
import { SplashSkeleton } from '../components/states'
import { useActiveProject } from '../hooks/activeProjectContext'
import { useBackButton } from '../hooks/useBackButton'
import { useNote, useNoteMutations, useNotes } from '../hooks/useNotes'
import { fmtDateGroup } from '../lib/format'
import { confirmDialog, hapticSuccess } from '../lib/telegram'

const INPUT =
  'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

export function Notes() {
  const navigate = useNavigate()
  const [openId, setOpenId] = useState<number | null>(null)
  const [newOpen, setNewOpen] = useState(false)
  const list = useNotes()
  const { create } = useNoteMutations()
  const { projects } = useActiveProject()

  useBackButton(() => {
    if (openId != null) setOpenId(null)
    else navigate(-1)
  })

  if (openId != null) {
    return <NoteDetail id={openId} onBack={() => setOpenId(null)} />
  }

  if (list.isPending) return <SplashSkeleton />

  const notes = list.data ?? []

  return (
    <Screen title="Qaydlarim">
      {notes.length === 0 ? (
        <EmptyState text="Hali qayd yo‘q. Kerakli narsalarni shu yerda yozib boring." />
      ) : (
        <div className="space-y-2">
          {notes.map((n) => (
            <button
              key={n.id}
              type="button"
              onClick={() => setOpenId(n.id)}
              className="block w-full rounded-card border border-border bg-surface p-3 text-left active:scale-[0.99]"
            >
              <div className="flex items-center gap-1.5">
                {n.is_pinned && (
                  <IconPinFilled size={14} className="shrink-0 text-primary" />
                )}
                <span className="truncate text-body text-text">{n.title}</span>
                {n.items_total > 0 && (
                  <span className="ml-auto shrink-0 rounded-chip bg-surface-2 px-2 py-0.5 text-label text-text-muted">
                    {n.items_done}/{n.items_total}
                  </span>
                )}
              </div>
              {n.body && (
                <p className="mt-0.5 line-clamp-1 text-label text-text-muted">
                  {n.body.split('\n')[0]}
                </p>
              )}
              <p className="mt-1 text-label text-text-faint">
                {fmtDateGroup(n.updated_at ?? n.created_at)}
              </p>
            </button>
          ))}
        </div>
      )}

      <button
        type="button"
        onClick={() => setNewOpen(true)}
        className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-card border border-dashed border-border py-3 text-label text-primary active:bg-surface-2"
      >
        <IconPlus size={16} /> Yangi qayd
      </button>

      <NewNoteSheet
        open={newOpen}
        onClose={() => setNewOpen(false)}
        projects={projects}
        pending={create.isPending}
        onCreate={async (title, projectId) => {
          const note = await create.mutateAsync({
            title,
            project_id: projectId,
          })
          hapticSuccess()
          setNewOpen(false)
          setOpenId(note.id)
        }}
      />
    </Screen>
  )
}

function NewNoteSheet({
  open,
  onClose,
  projects,
  pending,
  onCreate,
}: {
  open: boolean
  onClose: () => void
  projects: { id: number; title: string }[]
  pending: boolean
  onCreate: (title: string, projectId: number | null) => Promise<void>
}) {
  const [title, setTitle] = useState('')
  const [projectId, setProjectId] = useState<number | null>(null)

  const wasOpen = useRef(false)
  if (open && !wasOpen.current) {
    wasOpen.current = true
    setTitle('')
    setProjectId(null)
  }
  if (!open && wasOpen.current) wasOpen.current = false

  return (
    <BottomSheet open={open} onClose={onClose} title="Yangi qayd">
      <div className="space-y-3">
        <label className="block text-label text-text-muted">
          Sarlavha
          <input
            className={INPUT}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="masalan: Xarid ro‘yxati"
            autoFocus
          />
        </label>
        {projects.length > 0 && (
          <div>
            <div className="mb-1 text-label text-text-muted">
              Obyekt (ixtiyoriy)
            </div>
            <div className="flex flex-wrap gap-1">
              <ChipBtn
                active={projectId == null}
                onClick={() => setProjectId(null)}
              >
                Umumiy
              </ChipBtn>
              {projects.map((p) => (
                <ChipBtn
                  key={p.id}
                  active={projectId === p.id}
                  onClick={() => setProjectId(p.id)}
                >
                  {p.title}
                </ChipBtn>
              ))}
            </div>
          </div>
        )}
        <button
          type="button"
          disabled={!title.trim() || pending}
          onClick={() => void onCreate(title.trim(), projectId)}
          className="min-h-[44px] w-full rounded-btn bg-primary text-body text-on-primary active:scale-[0.98] disabled:opacity-60"
        >
          Yaratish
        </button>
      </div>
    </BottomSheet>
  )
}

function ChipBtn({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        active
          ? 'min-h-[36px] max-w-[12rem] truncate rounded-chip bg-primary px-3 text-body text-on-primary'
          : 'min-h-[36px] max-w-[12rem] truncate rounded-chip border border-border bg-surface px-3 text-body text-text-muted'
      }
    >
      {children}
    </button>
  )
}

// ---------------------------------------------------------------------------
// Qayd batafsil
// ---------------------------------------------------------------------------
function NoteDetail({ id, onBack }: { id: number; onBack: () => void }) {
  const q = useNote(id)
  const { update, remove, addItem, updateItem, removeItem } =
    useNoteMutations(id)
  const { projects } = useActiveProject()

  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [items, setItems] = useState<NoteItem[]>([])
  const [newItem, setNewItem] = useState('')

  const savedTitle = useRef('')
  const savedBody = useRef('')
  const seededFor = useRef<number | null>(null)

  useEffect(() => {
    if (q.data && seededFor.current !== q.data.id) {
      seededFor.current = q.data.id
      setTitle(q.data.title)
      setBody(q.data.body ?? '')
      setItems([...q.data.items].sort((a, b) => a.sort_order - b.sort_order))
      savedTitle.current = q.data.title
      savedBody.current = q.data.body ?? ''
    }
  }, [q.data])

  // avtomatik saqlash — 1 soniya kechikish bilan
  const { mutate: saveNote } = update
  useEffect(() => {
    if (seededFor.current !== id) return
    const t = setTimeout(() => {
      const patch: { id: number; title?: string; body?: string } = {
        id,
      }
      if (title.trim() && title !== savedTitle.current)
        patch.title = title.trim()
      if (body !== savedBody.current) patch.body = body
      if (patch.title !== undefined || patch.body !== undefined) {
        saveNote(patch)
        if (patch.title !== undefined) savedTitle.current = patch.title
        if (patch.body !== undefined) savedBody.current = patch.body
      }
    }, 1000)
    return () => clearTimeout(t)
  }, [title, body, id, saveNote])

  if (q.isPending || !q.data) return <SplashSkeleton />
  const note = q.data

  const doneCount = items.filter((i) => i.is_done).length
  const linkedProject = projects.find((p) => p.id === note.project_id)

  async function persistOrder(next: NoteItem[]) {
    setItems(next)
    await Promise.all(
      next.flatMap((it, idx) =>
        it.sort_order === idx
          ? []
          : [updateItem.mutateAsync({ id, itemId: it.id, sort_order: idx })],
      ),
    )
  }

  return (
    <Screen
      title="Qayd"
      action={
        <div className="flex items-center gap-1">
          <button
            type="button"
            aria-label={note.is_pinned ? 'Qadashni olib tashlash' : 'Qadash'}
            onClick={() => update.mutate({ id, is_pinned: !note.is_pinned })}
            className="p-1.5"
          >
            {note.is_pinned ? (
              <IconPinFilled size={18} className="text-primary" />
            ) : (
              <IconPin size={18} className="text-text-muted" />
            )}
          </button>
          <button
            type="button"
            onClick={onBack}
            className="rounded-chip bg-surface-2 px-3 py-1 text-label text-text-muted"
          >
            Orqaga
          </button>
        </div>
      }
    >
      <input
        className={`${INPUT} text-title`}
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Sarlavha"
      />

      <textarea
        className={`${INPUT} mt-2 min-h-[96px] resize-y`}
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Matn — erkin yozing"
      />

      {linkedProject && (
        <p className="mt-2 text-label text-text-muted">
          Obyekt: <span className="text-text">{linkedProject.title}</span>
        </p>
      )}

      <section className="mt-4">
        <div className="mb-1.5 flex items-center justify-between">
          <h2 className="text-label uppercase text-text-muted">Ro‘yxat</h2>
          {items.length > 0 && (
            <span className="text-label text-text-faint">
              {doneCount}/{items.length}
            </span>
          )}
        </div>

        {items.length > 0 && (
          <Reorder.Group
            axis="y"
            values={items}
            onReorder={setItems}
            className="space-y-1.5"
          >
            {items.map((it) => (
              <Reorder.Item
                key={it.id}
                value={it}
                onDragEnd={() => void persistOrder(items)}
                className="flex items-center gap-2 rounded-btn border border-border bg-surface px-2 py-2"
              >
                <IconGripVertical
                  size={16}
                  className="shrink-0 cursor-grab text-text-faint"
                />
                <button
                  type="button"
                  aria-label="Belgilash"
                  onClick={() =>
                    updateItem.mutate({
                      id,
                      itemId: it.id,
                      is_done: !it.is_done,
                    })
                  }
                  className={
                    it.is_done
                      ? 'flex h-5 w-5 shrink-0 items-center justify-center rounded border border-primary bg-primary text-[10px] text-on-primary'
                      : 'h-5 w-5 shrink-0 rounded border border-border'
                  }
                >
                  {it.is_done ? '✓' : ''}
                </button>
                <span
                  className={`flex-1 text-body ${
                    it.is_done ? 'text-text-faint line-through' : 'text-text'
                  }`}
                >
                  {it.text}
                </span>
                <button
                  type="button"
                  aria-label="O‘chirish"
                  onClick={() => removeItem.mutate({ id, itemId: it.id })}
                  className="shrink-0 text-text-faint active:text-danger"
                >
                  <IconTrash size={16} />
                </button>
              </Reorder.Item>
            ))}
          </Reorder.Group>
        )}

        <form
          className="mt-2 flex gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            const t = newItem.trim()
            if (!t) return
            addItem.mutate({ id, text: t })
            setNewItem('')
          }}
        >
          <input
            className={INPUT}
            value={newItem}
            onChange={(e) => setNewItem(e.target.value)}
            placeholder="Element qo‘shish"
          />
          <button
            type="submit"
            aria-label="Qo‘shish"
            className="shrink-0 rounded-btn bg-surface-2 px-4 text-body text-primary active:scale-95"
          >
            <IconPlus size={18} />
          </button>
        </form>
      </section>

      <button
        type="button"
        onClick={async () => {
          if (!(await confirmDialog('Bu qayd o‘chirilsinmi?'))) return
          await remove.mutateAsync(id)
          hapticSuccess()
          onBack()
        }}
        className="mt-6 w-full rounded-btn bg-danger-soft py-2.5 text-body text-danger active:scale-[0.99]"
      >
        Qaydni o‘chirish
      </button>
    </Screen>
  )
}
