import { api } from './client'
import type { EntryKind, PaidBy, PayMethod } from './entries'

export interface AiDraft {
  kind: EntryKind
  name: string
  quantity: string | null
  unit: string | null
  /** JAMI summa */
  amount: string | null
  unit_price: string | null
  paid_by: PaidBy | null
  payment_method: PayMethod | null
  matched_price_item_id: number | null
  vendor: string | null
  entry_date: string | null
  note: string | null
  confidence: 'high' | 'low'
}

export const aiParse = (projectId: number, text: string) =>
  api<AiDraft>(`/api/projects/${projectId}/ai-parse`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  })

export function receiptScan(projectId: number, image: Blob) {
  const fd = new FormData()
  fd.append('file', image, 'receipt.jpg')
  return api<AiDraft>(`/api/projects/${projectId}/receipt-scan`, {
    method: 'POST',
    body: fd,
  })
}
