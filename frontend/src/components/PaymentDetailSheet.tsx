import { useState } from 'react'
import type { TimelinePayment } from '../api/timeline'
import type { PayMethod } from '../api/payments'
import { useDeletePayment, useUpdatePayment } from '../hooks/usePayments'
import { METHOD_LABEL, PURPOSE_LABEL } from '../lib/entryVisual'
import { fmtDate, fmtMoney } from '../lib/format'
import { confirmDialog, hapticSuccess } from '../lib/telegram'
import { BottomSheet } from './BottomSheet'
import { MoneyInput } from './MoneyInput'
import { Segment } from './Segment'

const INPUT =
  'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

interface Props {
  projectId: number
  payment: TimelinePayment | null
  onClose: () => void
}

export function PaymentDetailSheet({ projectId, payment, onClose }: Props) {
  const upd = useUpdatePayment(projectId)
  const del = useDeletePayment(projectId)
  const [editing, setEditing] = useState(false)
  const [amount, setAmount] = useState<number | null>(null)
  const [method, setMethod] = useState<PayMethod>('cash')
  const [paidAt, setPaidAt] = useState('')
  const [note, setNote] = useState('')

  if (!payment) return null

  function startEdit() {
    if (!payment) return
    setAmount(Number(payment.amount))
    setMethod(payment.method)
    setPaidAt(payment.paid_at.slice(0, 10))
    setNote(payment.note ?? '')
    setEditing(true)
  }

  async function save() {
    if (!payment || (amount ?? 0) <= 0) return
    await upd.mutateAsync({
      id: payment.id,
      body: {
        amount: amount ?? 0,
        method,
        paid_at: paidAt,
        note: note.trim() || null,
      },
    })
    hapticSuccess()
    setEditing(false)
    onClose()
  }

  async function remove() {
    if (!payment) return
    if (!(await confirmDialog('Bu to‘lov o‘chirilsinmi?'))) return
    await del.mutateAsync(payment.id)
    hapticSuccess()
    onClose()
  }

  return (
    <BottomSheet open={!!payment} onClose={onClose} title="Mijoz to‘lovi">
      <div className="space-y-1.5 text-body">
        <Row k="Summa" v={`+ ${fmtMoney(payment.amount)}`} strong />
        <Row k="Maqsad" v={PURPOSE_LABEL[payment.purpose]} />
        <Row k="Usul" v={METHOD_LABEL[payment.method]} />
        <Row k="Sana" v={fmtDate(payment.paid_at)} />
        {payment.note && <Row k="Izoh" v={payment.note} />}
      </div>

      {editing ? (
        <div className="mt-4 space-y-2">
          <label className="block text-label text-text-muted">
            Summa
            <MoneyInput
              value={amount}
              onChange={setAmount}
              className={INPUT}
            />
          </label>
          <Segment
            options={[
              { value: 'cash', label: 'Naqd' },
              { value: 'card', label: 'Karta' },
              { value: 'transfer', label: 'O‘tkazma' },
            ]}
            value={method}
            onChange={(v) => setMethod(v as PayMethod)}
          />
          <label className="block text-label text-text-muted">
            Sana
            <input
              type="date"
              className={INPUT}
              value={paidAt}
              onChange={(e) => setPaidAt(e.target.value)}
            />
          </label>
          <label className="block text-label text-text-muted">
            Izoh
            <input
              className={INPUT}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={save}
              disabled={upd.isPending || (amount ?? 0) <= 0}
              className="min-h-[44px] flex-1 rounded-btn bg-primary text-body text-on-primary active:scale-[0.98] disabled:opacity-60"
            >
              Saqlash
            </button>
            <button
              type="button"
              onClick={() => setEditing(false)}
              className="min-h-[44px] rounded-btn bg-surface-2 px-4 text-body text-text"
            >
              Bekor
            </button>
          </div>
        </div>
      ) : (
        <div className="mt-4 flex gap-2">
          <button
            type="button"
            onClick={startEdit}
            className="min-h-[44px] flex-1 rounded-btn bg-surface-2 text-body text-text active:scale-[0.98]"
          >
            Tahrirlash
          </button>
          <button
            type="button"
            onClick={remove}
            disabled={del.isPending}
            className="min-h-[44px] flex-1 rounded-btn bg-danger-soft text-body text-danger active:scale-[0.98] disabled:opacity-60"
          >
            O‘chirish
          </button>
        </div>
      )}
    </BottomSheet>
  )
}

function Row({ k, v, strong }: { k: string; v: string; strong?: boolean }) {
  return (
    <div className="flex justify-between gap-3">
      <span className="text-text-muted">{k}</span>
      <span className="text-text">{strong ? <strong>{v}</strong> : v}</span>
    </div>
  )
}
