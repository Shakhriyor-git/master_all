import { api } from './client'

export type PayMethod = 'cash' | 'card' | 'transfer'
export type PayPurpose = 'labor' | 'material'

export interface Payment {
  id: number
  project_id: number
  created_by_user_id: number | null
  amount: string
  method: PayMethod
  purpose: PayPurpose
  paid_at: string
  note: string | null
  created_at: string
  updated_at: string | null
  deleted_at: string | null
}

export const listPayments = (projectId: number, purpose?: PayPurpose) =>
  api<Payment[]>(
    `/api/projects/${projectId}/payments${
      purpose ? `?purpose=${purpose}` : ''
    }`,
  )

export interface CreatePaymentBody {
  amount: number | string
  method?: PayMethod
  purpose?: PayPurpose
  paid_at?: string
  note?: string
}

export const createPayment = (projectId: number, body: CreatePaymentBody) =>
  api<Payment>(`/api/projects/${projectId}/payments`, {
    method: 'POST',
    body: JSON.stringify(body),
  })

export interface UpdatePaymentBody {
  amount?: number | string
  method?: PayMethod
  purpose?: PayPurpose
  paid_at?: string
  note?: string | null
}

export const updatePayment = (id: number, body: UpdatePaymentBody) =>
  api<Payment>(`/api/payments/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })

export const deletePayment = (id: number) =>
  api<void>(`/api/payments/${id}`, { method: 'DELETE' })
