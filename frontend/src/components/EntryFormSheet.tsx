import { useRef, useState } from 'react'
import { IconAlertTriangle } from '@tabler/icons-react'
import type { AiDraft } from '../api/ai'
import { createPriceItem } from '../api/catalog'
import type {
  CreateEntryBody,
  EntryKind,
  PaidBy,
  PayMethod,
} from '../api/entries'
import { useCreateEntry } from '../hooks/useEntries'
import { KIND_LABEL } from '../lib/entryVisual'
import { fmtMoney } from '../lib/format'
import { hapticSuccess } from '../lib/telegram'
import { BottomSheet } from './BottomSheet'
import { MoneyInput } from './MoneyInput'
import { QuantityInput } from './QuantityInput'
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
  /** boshlang'ich tur — AI kelmasa */
  initialKind?: EntryKind
  /** AI matn yoki chekdan kelgan qoralama */
  draft?: AiDraft | null
  onSaved: () => void
}

/**
 * Qo'lda kiritish / AI tasdiqlash formasi. Yozuv katalogga bog'lanmaydi
 * (`project_price_id` bo'sh), faqat «Katalogga ham qo'shilsin» belgilansa
 * alohida `price_item` yaratiladi.
 */
export function EntryFormSheet({
  open,
  onClose,
  projectId,
  initialKind = 'material',
  draft,
  onSaved,
}: Props) {
  const create = useCreateEntry(projectId)

  const [kind, setKind] = useState<EntryKind>(initialKind)
  const [name, setName] = useState('')
  const [qty, setQty] = useState<number | null>(null)
  const [unit, setUnit] = useState('')
  const [amount, setAmount] = useState<number | null>(null)
  const [paidBy, setPaidBy] = useState<PaidBy>('master')
  const [method, setMethod] = useState<PayMethod>('cash')
  const [entryDate, setEntryDate] = useState(today())
  const [note, setNote] = useState('')
  const [vendor, setVendor] = useState('')
  const [addToCatalog, setAddToCatalog] = useState(false)

  // open/draft o'zgarganda formani moslash
  const seed = useRef<string>('')
  const key = `${open ? 1 : 0}:${draft?.name ?? ''}:${draft?.amount ?? ''}:${initialKind}`
  if (seed.current !== key) {
    seed.current = key
    setKind(draft?.kind ?? initialKind)
    setName(draft?.name ?? '')
    setQty(draft?.quantity ? Number(draft.quantity) : null)
    setUnit(draft?.unit ?? '')
    setAmount(draft?.amount ? Number(draft.amount) : null)
    setPaidBy(draft?.paid_by ?? 'master')
    setMethod(draft?.payment_method ?? 'cash')
    setEntryDate(draft?.entry_date ?? today())
    setNote(draft?.note ?? '')
    setVendor(draft?.vendor ?? '')
    setAddToCatalog(false)
  }

  const isExpense = kind === 'expense'
  const isWork = kind === 'work'
  const total = amount ?? 0
  const unitPrice =
    !isExpense && (qty ?? 0) > 0 ? total / (qty as number) : total
  const ready = name.trim().length > 0 && total > 0

  async function save() {
    if (!ready) return
    const body: CreateEntryBody = {
      kind,
      name: name.trim(),
      unit: isExpense ? 'summa' : unit.trim() || 'summa',
      unit_price: unitPrice,
      // usta kiritgan aniq jami — backend shuni saqlaydi (yaxlatishsiz)
      amount: total,
      quantity: isExpense ? 1 : (qty ?? 0) > 0 ? (qty as number) : 1,
      entry_date: entryDate,
      note: note.trim() || undefined,
      vendor: vendor.trim() || undefined,
    }
    if (!isWork) {
      body.paid_by = paidBy
      body.payment_method = method
    }
    await create.mutateAsync(body)

    if (addToCatalog && !isExpense) {
      try {
        await createPriceItem({
          name: name.trim(),
          kind,
          unit: unit.trim() || 'summa',
          default_price: unitPrice,
        })
      } catch {
        /* dublikat bo'lishi mumkin — e'tibor bermaymiz */
      }
    }
    hapticSuccess()
    onSaved()
    onClose()
  }

  return (
    <BottomSheet
      open={open}
      onClose={onClose}
      title={draft ? 'Tekshiring va saqlang' : 'Qo‘lda kiritish'}
    >
      {draft?.confidence === 'low' && (
        <div className="mb-3 flex items-center gap-1.5 rounded-btn bg-accent-soft px-3 py-2 text-label text-accent">
          <IconAlertTriangle size={14} /> Tekshirib chiqing
        </div>
      )}

      <div className="space-y-3">
        <Segment
          options={[
            { value: 'work', label: KIND_LABEL.work },
            { value: 'material', label: KIND_LABEL.material },
            { value: 'expense', label: KIND_LABEL.expense },
          ]}
          value={kind}
          onChange={(v) => setKind(v as EntryKind)}
        />

        <label className="block text-label text-text-muted">
          Nomi
          <input
            className={INPUT}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="masalan: Oboy kley"
            autoFocus={!draft}
          />
        </label>

        {!isExpense && (
          <div className="grid grid-cols-2 gap-2">
            <label className="block text-label text-text-muted">
              Miqdor
              <QuantityInput
                value={qty}
                onChange={setQty}
                className={INPUT}
                placeholder="1"
              />
            </label>
            <label className="block text-label text-text-muted">
              Birlik
              <input
                className={INPUT}
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                placeholder="summa"
              />
            </label>
          </div>
        )}

        <label className="block text-label text-text-muted">
          Summa (jami)
          <MoneyInput
            value={amount}
            onChange={setAmount}
            className={`${INPUT} text-title`}
            placeholder="0"
          />
        </label>

        {!isExpense && (qty ?? 0) > 0 && total > 0 && (
          <p className="text-label text-text-faint">
            {fmtMoney(unitPrice)} / {unit.trim() || 'birlik'} · jami{' '}
            {fmtMoney(total)}
          </p>
        )}

        {!isWork && (
          <Segment
            options={[
              { value: 'cash', label: 'Naqd' },
              { value: 'card', label: 'Karta' },
              { value: 'transfer', label: 'O‘tkazma' },
            ]}
            value={method}
            onChange={(v) => setMethod(v as PayMethod)}
          />
        )}

        {!isWork && (
          <label className="block text-label text-text-muted">
            Sotuvchi (ixtiyoriy)
            <input
              className={INPUT}
              value={vendor}
              onChange={(e) => setVendor(e.target.value)}
              placeholder="masalan: Qurilish bozori"
            />
          </label>
        )}

        <label className="block text-label text-text-muted">
          Sana
          <input
            type="date"
            className={INPUT}
            value={entryDate}
            onChange={(e) => setEntryDate(e.target.value)}
          />
        </label>

        <label className="block text-label text-text-muted">
          Izoh (ixtiyoriy)
          <textarea
            className={`${INPUT} min-h-[60px] resize-y`}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </label>

        {!isWork && (
          <label className="flex items-center gap-2 text-label text-text-muted">
            <input
              type="checkbox"
              checked={paidBy === 'client'}
              onChange={(e) =>
                setPaidBy(e.target.checked ? 'client' : 'master')
              }
              className="h-4 w-4 accent-[var(--primary)]"
            />
            Mijoz o‘zi sotib oldi
          </label>
        )}

        {!isExpense && (
          <label className="flex items-center gap-2 text-label text-text-muted">
            <input
              type="checkbox"
              checked={addToCatalog}
              onChange={(e) => setAddToCatalog(e.target.checked)}
              className="h-4 w-4 accent-[var(--primary)]"
            />
            Katalogga ham qo‘shilsin
          </label>
        )}

        <button
          type="button"
          disabled={!ready || create.isPending}
          onClick={save}
          className="min-h-[44px] w-full rounded-btn bg-primary text-body text-on-primary active:scale-[0.98] disabled:opacity-60"
        >
          Saqlash
        </button>
      </div>
    </BottomSheet>
  )
}
