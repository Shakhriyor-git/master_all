import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createPayment,
  deletePayment,
  listPayments,
  updatePayment,
  type CreatePaymentBody,
  type PayPurpose,
  type UpdatePaymentBody,
} from '../api/payments'

export function usePayments(projectId: number, purpose?: PayPurpose) {
  return useQuery({
    queryKey: ['payments', projectId, purpose ?? 'all'],
    queryFn: () => listPayments(projectId, purpose),
    enabled: projectId > 0,
  })
}

function invalidate(
  qc: ReturnType<typeof useQueryClient>,
  projectId: number,
) {
  qc.invalidateQueries({ queryKey: ['payments', projectId] })
  qc.invalidateQueries({ queryKey: ['summary', projectId] })
  qc.invalidateQueries({ queryKey: ['timeline', projectId] })
}

export function useCreatePayment(projectId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: CreatePaymentBody) => createPayment(projectId, body),
    onSuccess: () => invalidate(qc, projectId),
  })
}

export function useUpdatePayment(projectId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: UpdatePaymentBody }) =>
      updatePayment(id, body),
    onSuccess: () => invalidate(qc, projectId),
  })
}

export function useDeletePayment(projectId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deletePayment(id),
    onSuccess: () => invalidate(qc, projectId),
  })
}
