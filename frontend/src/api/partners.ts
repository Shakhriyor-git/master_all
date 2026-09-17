import { api } from './client'
import type { PayMethod } from './payments'

/** Brigada — ustaning sheriklari. Obyektga bog'lanmaydi, hisobotga kirmaydi. */

export interface Partner {
  id: number
  name: string
  phone: string | null
  note: string | null
  created_at: string
}

export interface PartnerListItem extends Partner {
  total_paid: string
  payments_count: number
  last_payment_at: string | null
}

export interface PartnerList {
  partners: PartnerListItem[]
  grand_total: string
}

export interface PartnerPayment {
  id: number
  partner_id: number
  amount: string
  method: PayMethod
  paid_at: string
  note: string | null
  created_at: string
}

export interface PartnerBody {
  name?: string
  phone?: string | null
  note?: string | null
}

export interface PartnerPaymentBody {
  amount?: number | string
  method?: PayMethod
  paid_at?: string
  note?: string | null
}

export const listPartners = () => api<PartnerList>('/api/partners')

export const createPartner = (body: PartnerBody) =>
  api<Partner>('/api/partners', {
    method: 'POST',
    body: JSON.stringify(body),
  })

export const updatePartner = (id: number, body: PartnerBody) =>
  api<Partner>(`/api/partners/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })

export const deletePartner = (id: number) =>
  api<void>(`/api/partners/${id}`, { method: 'DELETE' })

export const listPartnerPayments = (partnerId: number) =>
  api<PartnerPayment[]>(`/api/partners/${partnerId}/payments`)

export const createPartnerPayment = (
  partnerId: number,
  body: PartnerPaymentBody,
) =>
  api<PartnerPayment>(`/api/partners/${partnerId}/payments`, {
    method: 'POST',
    body: JSON.stringify(body),
  })

export const updatePartnerPayment = (id: number, body: PartnerPaymentBody) =>
  api<PartnerPayment>(`/api/partner-payments/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })

export const deletePartnerPayment = (id: number) =>
  api<void>(`/api/partner-payments/${id}`, { method: 'DELETE' })
