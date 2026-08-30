import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  createPriceItem,
  listUnits,
  type PriceItem,
} from '../api/catalog'
import { BottomSheet } from './BottomSheet'
import { MoneyInput } from './MoneyInput'
import { hapticSuccess } from '../lib/telegram'

interface Props {
  open: boolean
  onClose: () => void
  kind: 'work' | 'material'
  categoryId: number | null
  onCreated: (item: PriceItem) => void
}

export function NewServiceSheet({
  open,
  onClose,
  kind,
  categoryId,
  onCreated,
}: Props) {
  const units = useQuery({ queryKey: ['units'], queryFn: listUnits })
  const [name, setName] = useState('')
  const [unit, setUnit] = useState('')
  const [price, setPrice] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)

  const unitOptions = useMemo(
    () =>
      (units.data ?? [])
        .filter((u) => u.code !== 'summa')
        .map((u) => ({ value: u.code, label: u.label })),
    [units.data],
  )

  const inputClass =
    'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

  async function save() {
    if (!name.trim() || !unit) return
    setBusy(true)
    try {
      const item = await createPriceItem({
        category_id: categoryId ?? undefined,
        name: name.trim(),
        kind,
        unit,
        default_price: price ?? 0,
      })
      hapticSuccess()
      onCreated(item)
      setName('')
      setUnit('')
      setPrice(null)
      onClose()
    } finally {
      setBusy(false)
    }
  }

  return (
    <BottomSheet open={open} onClose={onClose} title="Yangi xizmat">
      <div className="space-y-3">
        <label className="block text-label text-text-muted">
          Nomi
          <input
            className={inputClass}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="masalan: Shpatlyovka"
            autoFocus
          />
        </label>

        <div>
          <div className="mb-1 text-label text-text-muted">Birlik</div>
          {unitOptions.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {unitOptions.map((o) => (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => setUnit(o.value)}
                  className={
                    unit === o.value
                      ? 'min-h-[40px] rounded-chip bg-primary px-3 text-body text-on-primary'
                      : 'min-h-[40px] rounded-chip border border-border bg-surface px-3 text-body text-text-muted'
                  }
                >
                  {o.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <label className="block text-label text-text-muted">
          Narx (ixtiyoriy, keyin kiritsa bo‘ladi)
          <MoneyInput
            value={price}
            onChange={setPrice}
            className={inputClass}
            placeholder="0"
          />
        </label>

        <button
          type="button"
          onClick={save}
          disabled={busy || !name.trim() || !unit}
          className="min-h-[44px] w-full rounded-btn bg-primary text-body text-on-primary active:scale-[0.98] disabled:opacity-60"
        >
          Qo‘shish
        </button>
      </div>
    </BottomSheet>
  )
}
