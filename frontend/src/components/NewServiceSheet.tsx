import { useMemo, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { IconPlus } from '@tabler/icons-react'
import {
  createPriceItem,
  createUnit,
  listUnits,
  updatePriceItem,
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
  /** berilsa — tahrirlash rejimi */
  item?: PriceItem | null
  onCreated: (item: PriceItem) => void
}

const inputClass =
  'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

export function NewServiceSheet({
  open,
  onClose,
  kind,
  categoryId,
  item,
  onCreated,
}: Props) {
  const qc = useQueryClient()
  const units = useQuery({ queryKey: ['units'], queryFn: listUnits })
  const editing = !!item

  const [name, setName] = useState('')
  const [unit, setUnit] = useState('')
  const [price, setPrice] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const [newUnitOpen, setNewUnitOpen] = useState(false)
  const [newCode, setNewCode] = useState('')
  const [newLabel, setNewLabel] = useState('')

  // item / open o'zgarganda formani moslash
  const seed = useRef<string>('')
  const key = `${open ? 1 : 0}:${item?.id ?? 0}`
  if (seed.current !== key) {
    seed.current = key
    setName(item?.name ?? '')
    setUnit(item?.unit ?? '')
    setPrice(item ? Number(item.default_price) || null : null)
    setNewUnitOpen(false)
    setNewCode('')
    setNewLabel('')
  }

  const unitOptions = useMemo(
    () =>
      (units.data ?? [])
        .filter((u) => u.code !== 'summa')
        .map((u) => ({ value: u.code, label: u.label })),
    [units.data],
  )

  async function addUnit() {
    const code = newCode.trim()
    const label = newLabel.trim() || code
    if (!code) return
    setBusy(true)
    try {
      const u = await createUnit({ code, label })
      await qc.invalidateQueries({ queryKey: ['units'] })
      setUnit(u.code)
      setNewUnitOpen(false)
      setNewCode('')
      setNewLabel('')
    } finally {
      setBusy(false)
    }
  }

  async function save() {
    if (!name.trim() || !unit) return
    setBusy(true)
    try {
      const result = editing
        ? await updatePriceItem(item!.id, {
            name: name.trim(),
            unit,
            default_price: price ?? 0,
          })
        : await createPriceItem({
            category_id: categoryId ?? undefined,
            name: name.trim(),
            kind,
            unit,
            default_price: price ?? 0,
          })
      await Promise.all([
        qc.invalidateQueries({ queryKey: ['price-items'] }),
        qc.invalidateQueries({ queryKey: ['categories'] }),
      ])
      hapticSuccess()
      onCreated(result)
      onClose()
    } finally {
      setBusy(false)
    }
  }

  return (
    <BottomSheet
      open={open}
      onClose={onClose}
      title={editing ? 'Xizmatni tahrirlash' : 'Yangi xizmat'}
    >
      <div className="space-y-3">
        <label className="block text-label text-text-muted">
          Nomi
          <input
            className={inputClass}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="masalan: Shpatlyovka"
            autoFocus={!editing}
          />
        </label>

        <div>
          <div className="mb-1 text-label text-text-muted">Birlik</div>
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
            <button
              type="button"
              onClick={() => setNewUnitOpen((v) => !v)}
              className="flex min-h-[40px] items-center gap-1 rounded-chip border border-dashed border-border px-3 text-body text-primary"
            >
              <IconPlus size={14} /> Yangi birlik
            </button>
          </div>

          {newUnitOpen && (
            <div className="mt-2 space-y-2 rounded-btn border border-border bg-surface-2 p-2">
              <input
                className={inputClass}
                value={newLabel}
                onChange={(e) => setNewLabel(e.target.value)}
                placeholder="Ko‘rinishi, masalan: m²"
              />
              <input
                className={inputClass}
                value={newCode}
                onChange={(e) => setNewCode(e.target.value)}
                placeholder="Kod, masalan: m2"
              />
              <button
                type="button"
                onClick={addUnit}
                disabled={busy || !newCode.trim()}
                className="min-h-[40px] w-full rounded-btn bg-primary text-body text-on-primary active:scale-[0.98] disabled:opacity-60"
              >
                Birlik qo‘shish
              </button>
            </div>
          )}
        </div>

        <label className="block text-label text-text-muted">
          Narx {editing ? '' : '(ixtiyoriy, keyin kiritsa bo‘ladi)'}
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
          {editing ? 'Saqlash' : 'Qo‘shish'}
        </button>
      </div>
    </BottomSheet>
  )
}
