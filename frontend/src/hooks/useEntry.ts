import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Entry } from '../api/entries'

/** Bitta yozuv — batafsil oyna uchun (tarix lentasidan ochilganda). */
export function useEntry(id: number | null) {
  return useQuery({
    queryKey: ['entry', id],
    queryFn: () => api<Entry>(`/api/entries/${id as number}`),
    enabled: id != null,
  })
}
