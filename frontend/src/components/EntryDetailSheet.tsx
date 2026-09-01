import { useState } from 'react'
import type { Entry } from '../api/entries'
import { useDeleteEntry, useUpdateEntry } from '../hooks/useEntries'
import { confirmDialog, hapticSuccess } from '../lib/telegram'
import { KIND_LABEL, METHOD_LABEL } from '../lib/entryVisual'
import { fmtDate, fmtMoney, fmtQty } from '../lib/format'
import { BottomSheet } from './BottomSheet'
import { MoneyInput } from './MoneyInput'
import { QuantityInput } from './QuantityInput'

interface Props {
  projectId: number
  entry: Entry | null
  onClose: () => void
}

export function EntryDetailSheet({ projectId, entry, onClose }: Props) {
  const del = useDeleteEntry(projectId)
  const upd = useUpdateEntry(projectId)
  const [editing, setEditing] = useState(false)
  const [qty, setQty] = useState<number | null>(null)
  const [price, setPrice] = useState<number | null>(null)

  if (!entry) return null

  function startEdit() {
    if (!entry) return
    setQty(Number(entry.quantity))
    setPrice(Number(entry.unit_price))
    setEditing(true)
  }

  async function save() {
    if (!entry) return
    await upd.mutateAsync({
      id: entry.id,
      body: {
        quantity: qty ?? entry.quantity,
        unit_price: price ?? entry.unit_price,
      },
    })
    hapticSuccess()
    setEditing(false)
    onClose()
  }

  async function remove() {
    if (!entry) return
    const ok = await confirmDialog('Bu yozuv o‘chirilsinmi?')
    if (!ok) return
    await del.mutateAsync(entry.id)
    hapticSuccess()
    onClose()
  }

  const inputClass =
    'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

  return (
    <BottomSheet open={!!entry} onClose={onClose} title={entry.name}>
      <div className="space-y-1.5 text-body">
        <Row k="Turi" v={KIND_LABEL[entry.kind]} />
        {entry.category_name && <Row k="Kategoriya" v={entry.category_name} />}
        <Row k="Sana" v={fmtDate(entry.entry_date)} />
        {entry.kind !== 'expense' && (
          <Row
            k="Miqdor"
            v={`${fmtQty(entry.quantity, entry.unit_label ?? entry.unit)} × ${fmtMoney(entry.unit_price)}`}
          />
        )}
        <Row k="Summa" v={fmtMoney(entry.amount)} strong />
        {entry.payment_method && (
          <Row k="Usul" v={METHOD_LABEL[entry.payment_method]} />
        )}
        {entry.vendor && <Row k="Sotuvchi" v={entry.vendor} />}
        {entry.note && <Row k="Izoh" v={entry.note} />}
        {entry.is_rework && (
          <p className="text-label text-danger">
            ⚠️ Brak — mijozga yozilmadi
          </p>
        )}
      </div>

      {editing ? (
        <div className="mt-4 space-y-2">
          {entry.kind !== 'expense' && (
            <label className="block text-label text-text-muted">
              Miqdor
              <QuantityInput
                value={qty}
                onChange={setQty}
                className={inputClass}
              />
            </label>
          )}
          <label className="block text-label text-text-muted">
            {entry.kind === 'expense' ? 'Summa' : 'Bir birlik narxi'}
            <MoneyInput
              value={price}
              onChange={setPrice}
              className={inputClass}
            />
          </label>
          <div className="text-label text-text-muted">
            Natija:{' '}
            <span className="text-text">
              {fmtMoney((qty ?? 1) * (price ?? 0))}
            </span>
          </div>
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={save}
              disabled={upd.isPending}
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
      <span className={strong ? 'text-text' : 'text-text'}>
        {strong ? <strong>{v}</strong> : v}
      </span>
    </div>
  )
}
