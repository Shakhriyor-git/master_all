import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from '@tanstack/react-query'
import {
  addNoteItem,
  createNote,
  deleteNote,
  deleteNoteItem,
  getNote,
  listNotes,
  updateNote,
  updateNoteItem,
  type NoteDetail,
  type NoteListItem,
} from '../api/notes'

export function useNotes(projectId?: number) {
  return useQuery({
    queryKey: ['notes', projectId ?? 'all'],
    queryFn: () => listNotes(projectId),
  })
}

export function useNote(id: number | null) {
  return useQuery({
    queryKey: ['note', id],
    queryFn: () => getNote(id as number),
    enabled: id != null,
  })
}

// ---------------------------------------------------------------------------
// Optimistik kesh yordamchilari
// ---------------------------------------------------------------------------
type ListSnapshot = [readonly unknown[], NoteListItem[] | undefined][]

function patchLists(
  qc: QueryClient,
  fn: (n: NoteListItem) => NoteListItem | null,
): ListSnapshot {
  const snaps = qc.getQueriesData<NoteListItem[]>({ queryKey: ['notes'] })
  for (const [key, data] of snaps) {
    if (!data) continue
    const next: NoteListItem[] = []
    for (const n of data) {
      const r = fn(n)
      if (r) next.push(r)
    }
    qc.setQueryData(key, next)
  }
  return snaps
}

function restoreLists(qc: QueryClient, snaps: ListSnapshot | undefined) {
  snaps?.forEach(([key, data]) => qc.setQueryData(key, data))
}

function patchDetail(
  qc: QueryClient,
  id: number,
  fn: (d: NoteDetail) => NoteDetail,
): NoteDetail | undefined {
  const prev = qc.getQueryData<NoteDetail>(['note', id])
  if (prev) qc.setQueryData(['note', id], fn(prev))
  return prev
}

interface Ctx {
  detail?: NoteDetail
  lists?: ListSnapshot
}

export function useNoteMutations() {
  const qc = useQueryClient()

  const settleList = () => qc.invalidateQueries({ queryKey: ['notes'] })
  const settleOne = (id: number) => {
    qc.invalidateQueries({ queryKey: ['note', id] })
    settleList()
  }

  async function cancel(id: number) {
    await Promise.all([
      qc.cancelQueries({ queryKey: ['note', id] }),
      qc.cancelQueries({ queryKey: ['notes'] }),
    ])
  }

  return {
    create: useMutation({
      mutationFn: createNote,
      onSuccess: (data) => {
        qc.setQueryData(['note', data.id], data)
        settleList()
      },
    }),

    // sarlavha / matn / qadash
    update: useMutation({
      mutationFn: ({
        id,
        ...body
      }: {
        id: number
        title?: string
        body?: string | null
        is_pinned?: boolean
      }) => updateNote(id, body),
      onMutate: async (v): Promise<Ctx> => {
        await cancel(v.id)
        const patch: Partial<NoteListItem> = {}
        if (v.title !== undefined) patch.title = v.title
        if (v.body !== undefined) patch.body = v.body
        if (v.is_pinned !== undefined) patch.is_pinned = v.is_pinned
        const detail = patchDetail(qc, v.id, (d) => ({ ...d, ...patch }))
        const lists = patchLists(qc, (n) =>
          n.id === v.id
            ? { ...n, ...patch, updated_at: new Date().toISOString() }
            : n,
        )
        return { detail, lists }
      },
      onError: (_e, v, ctx) => {
        if (ctx?.detail) qc.setQueryData(['note', v.id], ctx.detail)
        restoreLists(qc, ctx?.lists)
      },
      onSettled: (_d, _e, v) => settleOne(v.id),
    }),

    remove: useMutation({
      mutationFn: (id: number) => deleteNote(id),
      onMutate: async (id): Promise<Ctx> => {
        await cancel(id)
        const lists = patchLists(qc, (n) => (n.id === id ? null : n))
        return { lists }
      },
      onError: (_e, _id, ctx) => restoreLists(qc, ctx?.lists),
      onSettled: () => settleList(),
    }),

    addItem: useMutation({
      mutationFn: ({ id, text }: { id: number; text: string }) =>
        addNoteItem(id, text),
      onMutate: async ({ id, text }): Promise<Ctx> => {
        await cancel(id)
        const detail = patchDetail(qc, id, (d) => ({
          ...d,
          items: [
            ...d.items,
            {
              id: -Date.now(),
              note_id: id,
              text,
              is_done: false,
              sort_order: d.items.length,
            },
          ],
        }))
        const lists = patchLists(qc, (n) =>
          n.id === id ? { ...n, items_total: n.items_total + 1 } : n,
        )
        return { detail, lists }
      },
      onError: (_e, { id }, ctx) => {
        if (ctx?.detail) qc.setQueryData(['note', id], ctx.detail)
        restoreLists(qc, ctx?.lists)
      },
      onSettled: (_d, _e, { id }) => settleOne(id),
    }),

    updateItem: useMutation({
      mutationFn: ({
        id,
        itemId,
        ...body
      }: {
        id: number
        itemId: number
        text?: string
        is_done?: boolean
        sort_order?: number
      }) => updateNoteItem(id, itemId, body),
      onMutate: async ({ id, itemId, ...body }): Promise<Ctx> => {
        await cancel(id)
        const detail = patchDetail(qc, id, (d) => ({
          ...d,
          items: d.items.map((it) =>
            it.id === itemId ? { ...it, ...body } : it,
          ),
        }))
        let lists: ListSnapshot | undefined
        if (body.is_done !== undefined) {
          const delta = body.is_done ? 1 : -1
          lists = patchLists(qc, (n) =>
            n.id === id
              ? {
                  ...n,
                  items_done: Math.min(
                    n.items_total,
                    Math.max(0, n.items_done + delta),
                  ),
                }
              : n,
          )
        }
        return { detail, lists }
      },
      onError: (_e, { id }, ctx) => {
        if (ctx?.detail) qc.setQueryData(['note', id], ctx.detail)
        restoreLists(qc, ctx?.lists)
      },
      onSettled: (_d, _e, { id }) => settleOne(id),
    }),

    removeItem: useMutation({
      mutationFn: ({ id, itemId }: { id: number; itemId: number }) =>
        deleteNoteItem(id, itemId),
      onMutate: async ({ id, itemId }): Promise<Ctx> => {
        await cancel(id)
        const removed = qc
          .getQueryData<NoteDetail>(['note', id])
          ?.items.find((it) => it.id === itemId)
        const detail = patchDetail(qc, id, (d) => ({
          ...d,
          items: d.items.filter((it) => it.id !== itemId),
        }))
        const lists = patchLists(qc, (n) =>
          n.id === id
            ? {
                ...n,
                items_total: Math.max(0, n.items_total - 1),
                items_done: removed?.is_done
                  ? Math.max(0, n.items_done - 1)
                  : n.items_done,
              }
            : n,
        )
        return { detail, lists }
      },
      onError: (_e, { id }, ctx) => {
        if (ctx?.detail) qc.setQueryData(['note', id], ctx.detail)
        restoreLists(qc, ctx?.lists)
      },
      onSettled: (_d, _e, { id }) => settleOne(id),
    }),
  }
}
