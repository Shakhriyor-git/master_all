import { useRef, useState } from 'react'
import { IconArrowLeft } from '@tabler/icons-react'
import type { PayMethod, PayPurpose } from '../api/payments'
import { useCreatePayment } from '../hooks/usePayments'
import { hapticSuccess } from '../lib/telegram'
import { BottomSheet } from './BottomSheet'
import { MoneyInput } from './MoneyInput'
import { Segment } from './Segment'

const INPUT =
  'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

interface Props {
  open: boolean
  onClose: () => void
  projectId: number
  /** berilsa — maqsad tanlash yashiriladi */
  lockPurpose?: PayPurpose
  onSaved?: () => void
}

export function AddPaymentSheet({
  open,
  onClose,
  projectId,
  lockPurpose,
  onSaved,
}: Props) {
  const create = useCreatePayment(projectId)
  // Standart qiymat YO'Q — usta ataylab tanlasin (10-vazifa 1-bo'lim)
  const [purpose, setPurpose] = useState<PayPurpose | null>(
    lockPurpose ?? null,
  )
  const [amount, setAmount] = useState<number | null>(null)
  const [method, setMethod] = useState<PayMethod>('cash')
  const [paidAt, setPaidAt] = useState(today())
  const [note, setNote] = useState('')

  const wasOpen = useRef(false)
  if (open && !wasOpen.current) {
    wasOpen.current = true
    setPurpose(lockPurpose ?? null)
    setAmount(null)
    setMethod('cash')
    setPaidAt(today())
    setNote('')
  }
  if (!open && wasOpen.current) wasOpen.current = false

  async function save() {
    if (!purpose || (amount ?? 0) <= 0) return
    await create.mutateAsync({
      amount: amount ?? 0,
      method,
      purpose,
      paid_at: paidAt,
      note: note.trim() || undefined,
    })
    hapticSuccess()
    onSaved?.()
    onClose()
  }

  return (
    <BottomSheet open={open} onClose={onClose} title="Mijoz to‘lovi">
      {!purpose ? (
        <div className="space-y-2">
          <p className="text-label text-text-muted">Pul nima uchun?</p>
          <button
            type="button"
            onClick={() => setPurpose('labor')}
            className="min-h-[52px] w-full rounded-btn bg-surface-2 text-body text-text active:scale-[0.98]"
          >
            💵 Ish haqi uchun
          </button>
          <button
            type="button"
            onClick={() => setPurpose('material')}
            className="min-h-[52px] w-full rounded-btn bg-surface-2 text-body text-text active:scale-[0.98]"
          >
            📦 Material uchun
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {!lockPurpose && (
            <button
              type="button"
              onClick={() => setPurpose(null)}
              className="flex items-center gap-1 text-label text-primary"
            >
              <IconArrowLeft size={14} />
              {purpose === 'labor' ? 'Ish haqi uchun' : 'Material uchun'}
            </button>
          )}
          <label className="block text-label text-text-muted">
            Summa
            <MoneyInput
              value={amount}
              onChange={setAmount}
              autoFocus
              className={`${INPUT} text-title`}
              placeholder="0"
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
            Izoh (ixtiyoriy)
            <input
              className={INPUT}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
          <button
            type="button"
            disabled={(amount ?? 0) <= 0 || create.isPending}
            onClick={save}
            className="min-h-[44px] w-full rounded-btn bg-primary text-body text-on-primary active:scale-[0.98] disabled:opacity-60"
          >
            Saqlash
          </button>
        </div>
      )}
    </BottomSheet>
  )
}
