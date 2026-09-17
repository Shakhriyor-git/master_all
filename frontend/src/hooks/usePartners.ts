import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from '@tanstack/react-query'
import {
  createPartner,
  createPartnerPayment,
  deletePartner,
  deletePartnerPayment,
  listPartnerPayments,
  listPartners,
  updatePartner,
  updatePartnerPayment,
  type PartnerBody,
  type PartnerList,
  type PartnerListItem,
  type PartnerPayment,
  type PartnerPaymentBody,
} from '../api/partners'

const LIST_KEY = ['partners'] as const
const paymentsKey = (partnerId: number) =>
  ['partner-payments', partnerId] as const

export function usePartners() {
  return useQuery({ queryKey: LIST_KEY, queryFn: listPartners })
}

export function usePartnerPayments(partnerId: number) {
  return useQuery({
    queryKey: paymentsKey(partnerId),
    queryFn: () => listPartnerPayments(partnerId),
    enabled: partnerId > 0,
  })
}

// ---------------------------------------------------------------------------
// Optimistik kesh yordamchilari
// ---------------------------------------------------------------------------
interface Ctx {
  list?: PartnerList
  payments?: PartnerPayment[]
}

function num(v: string | number): number {
  return Number(v) || 0
}

/** Ro'yxatdagi bitta sherik agregatini va grand_total ni o'zgartiradi. */
function patchList(
  qc: QueryClient,
  partnerId: number,
  fn: (p: PartnerListItem) => PartnerListItem | null,
): PartnerList | undefined {
  const prev = qc.getQueryData<PartnerList>(LIST_KEY)
  if (!prev) return undefined
  const partners: PartnerListItem[] = []
  for (const p of prev.partners) {
    const r = p.id === partnerId ? fn(p) : p
    if (r) partners.push(r)
  }
  const grand = partners.reduce((s, p) => s + num(p.total_paid), 0)
  qc.setQueryData<PartnerList>(LIST_KEY, {
    partners,
    grand_total: String(grand),
  })
  return prev
}

function patchPayments(
  qc: QueryClient,
  partnerId: number,
  fn: (items: PartnerPayment[]) => PartnerPayment[],
): PartnerPayment[] | undefined {
  const key = paymentsKey(partnerId)
  const prev = qc.getQueryData<PartnerPayment[]>(key)
  if (prev) qc.setQueryData(key, fn(prev))
  return prev
}

/** To'lovlar massividan sherik agregatini qayta hisoblaydi. */
function withTotals(
  p: PartnerListItem,
  items: PartnerPayment[],
): PartnerListItem {
  const total = items.reduce((s, it) => s + num(it.amount), 0)
  const last = items.reduce<string | null>(
    (m, it) => (m == null || it.paid_at > m ? it.paid_at : m),
    null,
  )
  return {
    ...p,
    total_paid: String(total),
    payments_count: items.length,
    last_payment_at: last,
  }
}

function restore(qc: QueryClient, partnerId: number, ctx?: Ctx) {
  if (ctx?.list) qc.setQueryData(LIST_KEY, ctx.list)
  if (ctx?.payments) qc.setQueryData(paymentsKey(partnerId), ctx.payments)
}

export function usePartnerMutations() {
  const qc = useQueryClient()

  const settleList = () => qc.invalidateQueries({ queryKey: LIST_KEY })
  const settle = (partnerId: number) => {
    qc.invalidateQueries({ queryKey: paymentsKey(partnerId) })
    settleList()
  }
  async function cancel(partnerId?: number) {
    await Promise.all([
      qc.cancelQueries({ queryKey: LIST_KEY }),
      partnerId != null
        ? qc.cancelQueries({ queryKey: paymentsKey(partnerId) })
        : Promise.resolve(),
    ])
  }

  /** Keshdagi to'lovlar bo'yicha ro'yxat agregatini yangilaydi. */
  function syncListFromPayments(partnerId: number): PartnerList | undefined {
    const items = qc.getQueryData<PartnerPayment[]>(paymentsKey(partnerId))
    if (!items) return undefined
    return patchList(qc, partnerId, (p) => withTotals(p, items))
  }

  return {
    createPartner: useMutation({
      mutationFn: (body: PartnerBody) => createPartner(body),
      onSuccess: () => settleList(),
    }),

    updatePartner: useMutation({
      mutationFn: ({ id, ...body }: PartnerBody & { id: number }) =>
        updatePartner(id, body),
      onMutate: async ({ id, ...body }): Promise<Ctx> => {
        await cancel()
        const list = patchList(qc, id, (p) => ({ ...p, ...body }))
        return { list }
      },
      onError: (_e, v, ctx) => restore(qc, v.id, ctx),
      onSettled: () => settleList(),
    }),

    removePartner: useMutation({
      mutationFn: (id: number) => deletePartner(id),
      onMutate: async (id): Promise<Ctx> => {
        await cancel(id)
        const list = patchList(qc, id, () => null)
        return { list }
      },
      onError: (_e, id, ctx) => restore(qc, id, ctx),
      onSettled: (_d, _e, id) => {
        qc.removeQueries({ queryKey: paymentsKey(id) })
        settleList()
      },
    }),

    createPayment: useMutation({
      mutationFn: ({
        partnerId,
        ...body
      }: PartnerPaymentBody & { partnerId: number }) =>
        createPartnerPayment(partnerId, body),
      onMutate: async ({ partnerId, ...body }): Promise<Ctx> => {
        await cancel(partnerId)
        const payments = patchPayments(qc, partnerId, (items) =>
          [
            {
              id: -Date.now(),
              partner_id: partnerId,
              amount: String(body.amount ?? 0),
              method: body.method ?? 'cash',
              paid_at: body.paid_at ?? new Date().toISOString().slice(0, 10),
              note: body.note ?? null,
              created_at: new Date().toISOString(),
            },
            ...items,
          ].sort((a, b) => (a.paid_at < b.paid_at ? 1 : -1)),
        )
        const list = payments
          ? syncListFromPayments(partnerId)
          : patchList(qc, partnerId, (p) => ({
              ...p,
              total_paid: String(num(p.total_paid) + num(body.amount ?? 0)),
              payments_count: p.payments_count + 1,
              last_payment_at:
                body.paid_at &&
                (!p.last_payment_at || body.paid_at > p.last_payment_at)
                  ? body.paid_at
                  : p.last_payment_at,
            }))
        return { list, payments }
      },
      onError: (_e, v, ctx) => restore(qc, v.partnerId, ctx),
      onSettled: (_d, _e, v) => settle(v.partnerId),
    }),

    updatePayment: useMutation({
      mutationFn: (
        v: PartnerPaymentBody & { id: number; partnerId: number },
      ) =>
        updatePartnerPayment(v.id, {
          amount: v.amount,
          method: v.method,
          paid_at: v.paid_at,
          note: v.note,
        }),
      onMutate: async ({ id, partnerId, ...body }): Promise<Ctx> => {
        await cancel(partnerId)
        const payments = patchPayments(qc, partnerId, (items) =>
          items
            .map((it) =>
              it.id === id
                ? {
                    ...it,
                    ...body,
                    amount:
                      body.amount !== undefined
                        ? String(body.amount)
                        : it.amount,
                  }
                : it,
            )
            .sort((a, b) => (a.paid_at < b.paid_at ? 1 : -1)),
        )
        const list = payments ? syncListFromPayments(partnerId) : undefined
        return { list, payments }
      },
      onError: (_e, v, ctx) => restore(qc, v.partnerId, ctx),
      onSettled: (_d, _e, v) => settle(v.partnerId),
    }),

    removePayment: useMutation({
      mutationFn: ({ id }: { id: number; partnerId: number }) =>
        deletePartnerPayment(id),
      onMutate: async ({ id, partnerId }): Promise<Ctx> => {
        await cancel(partnerId)
        const payments = patchPayments(qc, partnerId, (items) =>
          items.filter((it) => it.id !== id),
        )
        const list = payments ? syncListFromPayments(partnerId) : undefined
        return { list, payments }
      },
      onError: (_e, v, ctx) => restore(qc, v.partnerId, ctx),
      onSettled: (_d, _e, v) => settle(v.partnerId),
    }),
  }
}
