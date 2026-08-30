import { forwardRef, useCallback, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  IconDotsVertical,
  IconPlus,
} from '@tabler/icons-react'
import type { Category, PriceItem } from '../api/catalog'
import { BottomSheet } from '../components/BottomSheet'
import { MoneyInput } from '../components/MoneyInput'
import { NewServiceSheet } from '../components/NewServiceSheet'
import { EmptyState, Screen } from '../components/Screen'
import { Segment } from '../components/Segment'
import { SplashSkeleton } from '../components/states'
import { useBackButton } from '../hooks/useBackButton'
import {
  useCatalogMutations,
  useCategories,
  usePriceItems,
} from '../hooks/useCatalog'
import { confirmDialog, hapticSuccess } from '../lib/telegram'

type Kind = 'work' | 'material'
const EMOJIS = ['🏠', '🧱', '⬜', '◻️', '⚡', '🚿', '🔨', '📋', '🪣', '🎨', '📦']

const INPUT =
  'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

interface Group {
  id: number | null
  name: string
  icon: string | null
  items: PriceItem[]
}

export function Catalog() {
  const navigate = useNavigate()
  const [kind, setKind] = useState<Kind>('work')
  const [openId, setOpenId] = useState<number | null | 'none'>('none')

  const cats = useCategories(kind)
  const items = usePriceItems(kind)

  const groups = useMemo<Group[]>(() => {
    const all = items.data ?? []
    const list: Group[] = (cats.data ?? []).map((c: Category) => ({
      id: c.id,
      name: c.name,
      icon: c.icon,
      items: all.filter((i) => i.category_id === c.id),
    }))
    const orphan = all.filter((i) => i.category_id == null)
    if (orphan.length) {
      list.push({ id: null, name: 'Kategoriyasiz', icon: '📦', items: orphan })
    }
    return list
  }, [cats.data, items.data])

  const openGroup =
    openId === 'none' ? null : groups.find((g) => g.id === openId) ?? null

  const back = useCallback(() => {
    if (openId !== 'none') setOpenId('none')
    else navigate(-1)
  }, [openId, navigate])
  useBackButton(back)

  if (cats.isPending || items.isPending) return <SplashSkeleton />

  if (openGroup) {
    return (
      <CategoryDetail
        key={openGroup.id ?? 'orphan'}
        group={openGroup}
        kind={kind}
        categories={cats.data ?? []}
        onBack={() => setOpenId('none')}
      />
    )
  }

  return (
    <Screen title="Xizmatlarim">
      <div className="mb-3">
        <Segment
          options={[
            { value: 'work', label: 'Ishlar' },
            { value: 'material', label: 'Materiallar' },
          ]}
          value={kind}
          onChange={(v) => {
            setKind(v as Kind)
            setOpenId('none')
          }}
        />
      </div>

      {groups.length === 0 ? (
        <EmptyState text="Hali kategoriya yo‘q." />
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {groups.map((g) => {
            const priceless = g.items.filter(
              (i) => Number(i.default_price) <= 0,
            ).length
            return (
              <button
                key={g.id ?? 'orphan'}
                type="button"
                onClick={() => setOpenId(g.id)}
                className="flex flex-col items-center gap-1 rounded-card border border-border bg-surface p-4 text-center active:scale-[0.98]"
              >
                <span className="text-title">{g.icon ?? '📦'}</span>
                <span className="text-body text-text">{g.name}</span>
                <span className="text-label text-text-muted">
                  {g.items.length} xizmat
                </span>
                <span
                  className={
                    priceless > 0
                      ? 'text-label text-danger'
                      : 'text-label text-success'
                  }
                >
                  {priceless > 0 ? `${priceless} narxsiz` : 'narx to‘liq'}
                </span>
              </button>
            )
          })}
        </div>
      )}

      <NewCategoryCard kind={kind} />
    </Screen>
  )
}

// ---------------------------------------------------------------------------
// Yangi kategoriya
// ---------------------------------------------------------------------------
function NewCategoryCard({ kind }: { kind: Kind }) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [icon, setIcon] = useState<string>(EMOJIS[0])
  const { createCategory } = useCatalogMutations()

  async function save() {
    if (!name.trim()) return
    await createCategory.mutateAsync({ name: name.trim(), kind, icon })
    hapticSuccess()
    setName('')
    setOpen(false)
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-card border border-dashed border-border py-3 text-label text-primary active:bg-surface-2"
      >
        <IconPlus size={16} /> Yangi kategoriya
      </button>

      <BottomSheet open={open} onClose={() => setOpen(false)} title="Yangi kategoriya">
        <div className="space-y-3">
          <label className="block text-label text-text-muted">
            Nomi
            <input
              className={INPUT}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="masalan: Elektrika"
              autoFocus
            />
          </label>
          <div>
            <div className="mb-1 text-label text-text-muted">Belgi</div>
            <div className="flex flex-wrap gap-1">
              {EMOJIS.map((e) => (
                <button
                  key={e}
                  type="button"
                  onClick={() => setIcon(e)}
                  className={
                    icon === e
                      ? 'h-10 w-10 rounded-btn bg-primary-soft text-title'
                      : 'h-10 w-10 rounded-btn border border-border text-title'
                  }
                >
                  {e}
                </button>
              ))}
            </div>
          </div>
          <button
            type="button"
            onClick={save}
            disabled={!name.trim() || createCategory.isPending}
            className="min-h-[44px] w-full rounded-btn bg-primary text-body text-on-primary active:scale-[0.98] disabled:opacity-60"
          >
            Qo‘shish
          </button>
        </div>
      </BottomSheet>
    </>
  )
}

// ---------------------------------------------------------------------------
// Kategoriya ichi — xizmatlar ro'yxati
// ---------------------------------------------------------------------------
function CategoryDetail({
  group,
  kind,
  categories,
  onBack,
}: {
  group: Group
  kind: Kind
  categories: Category[]
  onBack: () => void
}) {
  const { updateItem, deleteItem, bulkPrices } = useCatalogMutations()
  const [menuItem, setMenuItem] = useState<PriceItem | null>(null)
  const [editItem, setEditItem] = useState<PriceItem | null>(null)
  const [moveItem, setMoveItem] = useState<PriceItem | null>(null)
  const [newOpen, setNewOpen] = useState(false)
  const [fillOpen, setFillOpen] = useState(false)

  const priceRefs = useRef<(HTMLInputElement | null)[]>([])
  const priceless = group.items.filter((i) => Number(i.default_price) <= 0)

  return (
    <Screen
      title={`${group.icon ?? '📦'} ${group.name}`}
      action={
        <button
          type="button"
          onClick={onBack}
          className="rounded-chip bg-surface-2 px-3 py-1 text-label text-text-muted"
        >
          Orqaga
        </button>
      }
    >
      {priceless.length > 0 && (
        <button
          type="button"
          onClick={() => setFillOpen(true)}
          className="mb-3 w-full rounded-btn bg-primary-soft py-2.5 text-body text-primary active:scale-[0.99]"
        >
          Barcha narxlarni to‘ldirish ({priceless.length})
        </button>
      )}

      {group.items.length === 0 ? (
        <EmptyState text="Bu kategoriyada hali xizmat yo‘q." />
      ) : (
        <div className="overflow-hidden rounded-card border border-border bg-surface">
          {group.items.map((it, idx) => (
            <div
              key={it.id}
              className="flex items-center gap-2 border-b border-border px-3 py-2 last:border-b-0"
            >
              <div className="min-w-0 flex-1">
                <div className="truncate text-body text-text">{it.name}</div>
                <div className="text-label text-text-muted">
                  {it.unit_label ?? it.unit}
                </div>
              </div>
              <PriceCell
                ref={(el) => {
                  priceRefs.current[idx] = el
                }}
                value={Number(it.default_price) || null}
                onCommit={(v) => {
                  if ((Number(it.default_price) || 0) !== (v ?? 0)) {
                    updateItem.mutate({ id: it.id, default_price: v ?? 0 })
                  }
                }}
                onEnter={() => priceRefs.current[idx + 1]?.focus()}
              />
              <button
                type="button"
                onClick={() => setMenuItem(it)}
                aria-label="Amallar"
                className="shrink-0 text-text-faint active:text-text"
              >
                <IconDotsVertical size={18} />
              </button>
            </div>
          ))}
        </div>
      )}

      <button
        type="button"
        onClick={() => setNewOpen(true)}
        className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-card border border-dashed border-border py-3 text-label text-primary active:bg-surface-2"
      >
        <IconPlus size={16} /> Yangi xizmat
      </button>

      {/* qator menyusi */}
      <BottomSheet
        open={!!menuItem}
        onClose={() => setMenuItem(null)}
        title={menuItem?.name}
      >
        <div className="space-y-2">
          <SheetBtn
            onClick={() => {
              setEditItem(menuItem)
              setMenuItem(null)
            }}
          >
            Tahrirlash
          </SheetBtn>
          <SheetBtn
            onClick={() => {
              setMoveItem(menuItem)
              setMenuItem(null)
            }}
          >
            Boshqa kategoriyaga
          </SheetBtn>
          <SheetBtn
            danger
            onClick={async () => {
              const it = menuItem
              setMenuItem(null)
              if (!it) return
              if (await confirmDialog(`"${it.name}" o‘chirilsinmi?`)) {
                await deleteItem.mutateAsync(it.id)
                hapticSuccess()
              }
            }}
          >
            O‘chirish
          </SheetBtn>
        </div>
      </BottomSheet>

      {/* boshqa kategoriyaga ko'chirish */}
      <BottomSheet
        open={!!moveItem}
        onClose={() => setMoveItem(null)}
        title="Kategoriyani tanlang"
      >
        <div className="space-y-1">
          {categories
            .filter((c) => c.id !== group.id)
            .map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={async () => {
                  const it = moveItem
                  setMoveItem(null)
                  if (!it) return
                  await updateItem.mutateAsync({
                    id: it.id,
                    category_id: c.id,
                  })
                  hapticSuccess()
                }}
                className="min-h-[44px] w-full rounded-btn px-3 text-left text-body text-text active:bg-surface-2"
              >
                {c.icon ?? '📦'} {c.name}
              </button>
            ))}
        </div>
      </BottomSheet>

      <NewServiceSheet
        open={newOpen}
        onClose={() => setNewOpen(false)}
        kind={kind}
        categoryId={group.id}
        onCreated={() => setNewOpen(false)}
      />
      <NewServiceSheet
        open={!!editItem}
        onClose={() => setEditItem(null)}
        kind={kind}
        categoryId={group.id}
        item={editItem}
        onCreated={() => setEditItem(null)}
      />

      <FillPricesWizard
        open={fillOpen}
        onClose={() => setFillOpen(false)}
        items={priceless}
        onDone={async (rows) => {
          if (rows.length) {
            await bulkPrices.mutateAsync(rows)
            hapticSuccess()
          }
          setFillOpen(false)
        }}
      />
    </Screen>
  )
}

function SheetBtn({
  children,
  onClick,
  danger,
}: {
  children: ReactNode
  onClick: () => void
  danger?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        danger
          ? 'min-h-[44px] w-full rounded-btn bg-danger-soft text-body text-danger active:scale-[0.98]'
          : 'min-h-[44px] w-full rounded-btn bg-surface-2 text-body text-text active:scale-[0.98]'
      }
    >
      {children}
    </button>
  )
}

// inline narx katakchasi
interface PriceCellProps {
  value: number | null
  onCommit: (v: number | null) => void
  onEnter: () => void
}

const PriceCell = forwardRef<HTMLInputElement, PriceCellProps>(
  function PriceCell({ value, onCommit, onEnter }, ref) {
    const [v, setV] = useState<number | null>(value)
    const last = useRef(value)
    if (last.current !== value) {
      last.current = value
      setV(value)
    }
    return (
      <MoneyInput
        ref={ref}
        value={v}
        onChange={setV}
        placeholder="narx"
        aria-label="narx"
        className={
          'w-24 shrink-0 rounded-btn border px-2 py-1.5 text-right text-body outline-none focus:border-primary ' +
          ((v ?? 0) <= 0
            ? 'border-danger bg-danger-soft text-danger'
            : 'border-border bg-surface-2 text-text')
        }
        onBlur={() => onCommit(v)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault()
            onCommit(v)
            onEnter()
          }
        }}
      />
    )
  },
)

// ---------------------------------------------------------------------------
// Narxlarni ketma-ket to'ldirish
// ---------------------------------------------------------------------------
function FillPricesWizard({
  open,
  onClose,
  items,
  onDone,
}: {
  open: boolean
  onClose: () => void
  items: PriceItem[]
  onDone: (rows: { id: number; default_price: number }[]) => void
}) {
  const [idx, setIdx] = useState(0)
  const [rows, setRows] = useState<{ id: number; default_price: number }[]>([])
  const [price, setPrice] = useState<number | null>(null)

  const seed = useRef(false)
  if (open && !seed.current) {
    seed.current = true
    setIdx(0)
    setRows([])
    setPrice(null)
  }
  if (!open && seed.current) seed.current = false

  const cur = items[idx]

  function next(save: boolean) {
    const acc =
      save && cur && (price ?? 0) > 0
        ? [...rows, { id: cur.id, default_price: price ?? 0 }]
        : rows
    if (idx + 1 >= items.length) {
      onDone(acc)
      return
    }
    setRows(acc)
    setIdx(idx + 1)
    setPrice(null)
  }

  if (!cur) return null

  return (
    <BottomSheet open={open} onClose={onClose} title="Narxlarni to‘ldirish">
      <div className="space-y-3">
        <div className="text-label text-text-muted">
          {idx + 1} / {items.length}
        </div>
        <div className="text-title text-text">{cur.name}</div>
        <div className="text-label text-text-muted">
          bir {cur.unit_label ?? cur.unit} narxi
        </div>
        <MoneyInput
          value={price}
          onChange={setPrice}
          autoFocus
          className={`${INPUT} text-title`}
          placeholder="0"
        />
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => next(false)}
            className="min-h-[44px] flex-1 rounded-btn bg-surface-2 text-body text-text active:scale-[0.98]"
          >
            O‘tkazish
          </button>
          <button
            type="button"
            onClick={() => next(true)}
            disabled={(price ?? 0) <= 0}
            className="min-h-[44px] flex-1 rounded-btn bg-primary text-body text-on-primary active:scale-[0.98] disabled:opacity-60"
          >
            {idx + 1 >= items.length ? 'Saqlash' : 'Keyingi'}
          </button>
        </div>
      </div>
    </BottomSheet>
  )
}
