import { api } from './client'

export interface NoteItem {
  id: number
  note_id: number
  text: string
  is_done: boolean
  sort_order: number
}

export interface Note {
  id: number
  user_id: number
  project_id: number | null
  title: string
  body: string | null
  is_pinned: boolean
  created_at: string
  updated_at: string | null
}

/** Ro'yxat kartasi — belgilangan/jami ro'yxat elementi sanog'i bilan. */
export interface NoteListItem extends Note {
  items_done: number
  items_total: number
}

export interface NoteDetail extends Note {
  items: NoteItem[]
}

export const listNotes = (projectId?: number) =>
  api<NoteListItem[]>(
    `/api/notes${projectId != null ? `?project_id=${projectId}` : ''}`,
  )

export const getNote = (id: number) => api<NoteDetail>(`/api/notes/${id}`)

export const createNote = (body: {
  project_id?: number | null
  title: string
  body?: string
  items?: string[]
}) =>
  api<NoteDetail>('/api/notes', {
    method: 'POST',
    body: JSON.stringify(body),
  })

export const updateNote = (
  id: number,
  body: { title?: string; body?: string | null; is_pinned?: boolean },
) =>
  api<Note>(`/api/notes/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })

export const deleteNote = (id: number) =>
  api<void>(`/api/notes/${id}`, { method: 'DELETE' })

export const addNoteItem = (noteId: number, text: string) =>
  api<NoteItem>(`/api/notes/${noteId}/items`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  })

export const updateNoteItem = (
  noteId: number,
  itemId: number,
  body: { text?: string; is_done?: boolean; sort_order?: number },
) =>
  api<NoteItem>(`/api/notes/${noteId}/items/${itemId}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })

export const deleteNoteItem = (noteId: number, itemId: number) =>
  api<void>(`/api/notes/${noteId}/items/${itemId}`, { method: 'DELETE' })
