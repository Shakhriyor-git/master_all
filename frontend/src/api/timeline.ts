import { api } from './client'
import type { EntryKind, PaidBy, PayMethod } from './entries'
import type { PayPurpose } from './payments'

export interface TimelineEntry {
  type: 'entry'
  id: number
  kind: EntryKind
  name: string
  quantity: string
  unit: string
  unit_label: string | null
  unit_price: string
  amount: string
  paid_by: PaidBy
  payment_method: PayMethod | null
  is_rework: boolean
  has_receipt: boolean
  note: string | null
  entry_date: string
  created_at: string
}

export interface TimelinePayment {
  type: 'payment'
  id: number
  kind: 'payment'
  purpose: PayPurpose
  amount: string
  method: PayMethod
  note: string | null
  paid_at: string
  created_at: string
}

export type TimelineItem = TimelineEntry | TimelinePayment

export interface TimelinePage {
  items: TimelineItem[]
  page: number
  pages: number
  total: number
}

export type TimelineKind = EntryKind | 'payment'

export function listTimeline(params: {
  projectId: number
  kind?: TimelineKind
  dateFrom?: string
  dateTo?: string
  page?: number
}) {
  const qs = new URLSearchParams({ page: String(params.page ?? 1) })
  if (params.kind) qs.set('kind', params.kind)
  if (params.dateFrom) qs.set('date_from', params.dateFrom)
  if (params.dateTo) qs.set('date_to', params.dateTo)
  return api<TimelinePage>(
    `/api/projects/${params.projectId}/timeline?${qs}`,
  )
}
