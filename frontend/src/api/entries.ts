import { api } from './client'

export type EntryKind = 'work' | 'material' | 'expense'
export type PaidBy = 'master' | 'client'
export type PayMethod = 'cash' | 'card' | 'transfer'

export interface Entry {
  id: number
  project_id: number
  project_price_id: number | null
  created_by_user_id: number | null
  kind: EntryKind
  name: string
  unit: string
  quantity: string
  unit_price: string
  amount: string
  paid_by: PaidBy
  is_billable: boolean
  is_rework: boolean
  payment_method: PayMethod | null
  vendor: string | null
  entry_date: string
  note: string | null
  receipt_file_id: string | null
  source: string
  created_at: string
  updated_at: string | null
  deleted_at: string | null
  category_name: string | null
  unit_label: string | null
  has_receipt: boolean
}

export interface EntryPage {
  items: Entry[]
  page: number
  pages: number
  total: number
}

export interface ListEntriesParams {
  projectId: number
  kind?: EntryKind
  paidBy?: PaidBy
  dateFrom?: string
  dateTo?: string
  page?: number
}

export function listEntries({
  projectId,
  kind,
  paidBy,
  dateFrom,
  dateTo,
  page = 1,
}: ListEntriesParams) {
  const qs = new URLSearchParams({ page: String(page) })
  if (kind) qs.set('kind', kind)
  if (paidBy) qs.set('paid_by', paidBy)
  if (dateFrom) qs.set('date_from', dateFrom)
  if (dateTo) qs.set('date_to', dateTo)
  return api<EntryPage>(`/api/projects/${projectId}/entries?${qs}`)
}

export interface CreateEntryBody {
  price_item_id?: number
  project_price_id?: number
  kind?: EntryKind
  name?: string
  unit?: string
  unit_price?: number | string
  quantity?: number | string
  paid_by?: PaidBy
  is_rework?: boolean
  payment_method?: PayMethod | null
  vendor?: string
}

export const createEntry = (projectId: number, body: CreateEntryBody) =>
  api<Entry>(`/api/projects/${projectId}/entries`, {
    method: 'POST',
    body: JSON.stringify(body),
  })

export interface UpdateEntryBody {
  quantity?: number | string
  unit_price?: number | string
  note?: string
  vendor?: string
  is_rework?: boolean
}

export const updateEntry = (id: number, body: UpdateEntryBody) =>
  api<Entry>(`/api/entries/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })

export const deleteEntry = (id: number) =>
  api<void>(`/api/entries/${id}`, { method: 'DELETE' })

export const deleteLastEntry = (projectId: number) =>
  api<Entry>(`/api/projects/${projectId}/entries/last`, { method: 'DELETE' })
