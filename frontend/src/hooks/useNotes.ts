import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  addNoteItem,
  createNote,
  deleteNote,
  deleteNoteItem,
  getNote,
  listNotes,
  updateNote,
  updateNoteItem,
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

export function useNoteMutations(noteId?: number) {
  const qc = useQueryClient()
  const refreshList = () => qc.invalidateQueries({ queryKey: ['notes'] })
  const refreshOne = () => {
    if (noteId != null) qc.invalidateQueries({ queryKey: ['note', noteId] })
    refreshList()
  }

  return {
    create: useMutation({ mutationFn: createNote, onSuccess: refreshList }),
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
      onSuccess: (_d, v) => {
        qc.invalidateQueries({ queryKey: ['note', v.id] })
        refreshList()
      },
    }),
    remove: useMutation({
      mutationFn: (id: number) => deleteNote(id),
      onSuccess: refreshList,
    }),
    addItem: useMutation({
      mutationFn: ({ id, text }: { id: number; text: string }) =>
        addNoteItem(id, text),
      onSuccess: refreshOne,
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
      onSuccess: refreshOne,
    }),
    removeItem: useMutation({
      mutationFn: ({ id, itemId }: { id: number; itemId: number }) =>
        deleteNoteItem(id, itemId),
      onSuccess: refreshOne,
    }),
  }
}
