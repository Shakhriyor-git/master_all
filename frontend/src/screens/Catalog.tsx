import { forwardRef, useCallback, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  IconDotsVertical,
  IconPlus,
  IconSearch,
  IconWand,
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
import {
  CATEGORY_ICONS,
  catIcon,
  catIconStyle,
} from '../lib/categoryIcons'
import { confirmDialog, hapticSuccess } from '../lib/telegram'

type Kind = 'work' | 'material'

const INPUT =
  'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

interface Group {
  id: number | null
  name: string
  icon: string | null
  items: PriceItem[]
}

function priceStats(items: PriceItem[]) {
  const total = items.length
  const priced = items.filter((i) => Number(i.default_price) > 0).length
  const pct = total ? Math.round((priced / total) * 100) : 0
  const good = pct === 100 || pct > 50
  return { total, priced, pct, good }
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
      list.push({ id: null, name: 'Kategoriyasiz', icon: null, items: orphan })
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

  const unit = kind === 'work' ? 'xizmat' : 'pozitsiya'

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
        <div className="rounded-card border border-border bg-surface px-5 py-8 text-center">
          <p className="text-body text-text">Katalogingiz bo‘sh</p>
          <p className="mt-2 text-label text-text-muted">
            Avval kategoriya yarating (masalan: Shift, Elektrika), keyin
            ichiga xizmatlaringizni qo‘shing.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-2.5">
          {groups.map((g) => {
            const { total, priced, pct, good } = priceStats(g.items)
            const ci = catIcon(g.icon)
            const barColor = good ? 'var(--success)' : 'var(--danger)'
            return (
              <button
                key={g.id ?? 'orphan'}
                type="button"
                onClick={() => setOpenId(g.id)}
                className="rounded-card border border-border bg-surface p-3.5 text-left active:scale-[0.98]"
              >
                <span
                  className="mb-2.5 flex h-[38px] w-[38px] items-center justify-center rounded-[11px]"
                  style={catIconStyle(ci.color)}
                >
                  <ci.Icon size={20} />
                </span>
                <div className="text-[14px] font-medium text-text">{g.name}</div>
                <div className="mb-2 text-[11px] text-text-faint">
                  {total} {unit}
                </div>
                <div className="h-[3px] overflow-hidden rounded-chip bg-surface-2">
                  <span
                    className="block h-full"
                    style={{ width: `${pct}%`, background: barColor }}
                  />
                </div>
                <div
                  className={`mt-1.5 text-[10px] ${
                    pct === 100
                      ? 'text-success'
                      : good
                        ? 'text-text-faint'
                        : 'text-danger'
                  }`}
                >
                  {pct === 100
                    ? 'Narx to‘liq'
                    : `${priced} / ${total} narxlangan`}
                </div>
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
// Yangi kategoriya — ikonka to'ri + qidiruv
// ---------------------------------------------------------------------------
function NewCategoryCard({ kind }: { kind: Kind }) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [icon, setIcon] = useState<string>(CATEGORY_ICONS[0].name)
  const [q, setQ] = useState('')
  const { createCategory } = useCatalogMutations()

  const filtered = q.trim()
    ? CATEGORY_ICONS.filter((c) =>
        c.label.toLowerCase().includes(q.trim().toLowerCase()),
      )
    : CATEGORY_ICONS

  async function save() {
    if (!name.trim()) return
    await createCategory.mutateAsync({ name: name.trim(), kind, icon })
    hapticSuccess()
    setName('')
    setQ('')
    setOpen(false)
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-card border-[1.5px] border-dashed border-border py-3.5 text-body font-medium text-primary active:bg-surface-2"
      >
        <IconPlus size={18} /> Yangi kategoriya
      </button>

      <BottomSheet
        open={open}
        onClose={() => setOpen(false)}
        title="Yangi kategoriya"
      >
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

          <div className="flex items-center gap-2 rounded-btn border border-border bg-surface-2 px-3 py-2">
            <IconSearch size={15} className="shrink-0 text-text-faint" />
            <input
              className="min-w-0 flex-1 bg-transparent text-body text-text outline-none placeholder:text-text-faint"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Ikonka qidirish…"
            />
          </div>

          <div className="grid max-h-56 grid-cols-[repeat(auto-fill,minmax(64px,1fr))] gap-2 overflow-y-auto">
            {filtered.map((c) => (
              <button
                key={c.name}
                type="button"
                onClick={() => setIcon(c.name)}
                className={`flex flex-col items-center gap-1 rounded-btn border p-2 ${
                  icon === c.name ? 'border-primary' : 'border-border'
                }`}
              >
                <span
                  className="flex h-[34px] w-[34px] items-center justify-center rounded-[10px]"
                  style={catIconStyle(c.color)}
                >
                  <c.Icon size={18} />
                </span>
                <span className="text-[10px] text-text-faint">{c.label}</span>
              </button>
            ))}
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
// Kategoriya ichi
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
  const noun = kind === 'work' ? 'xizmat' : 'material'
  const ci = catIcon(group.icon)

  return (
    <Screen
      title={group.name}
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
      <div className="mb-3.5 flex items-center gap-2.5">
        <span
          className="flex h-9 w-9 items-center justify-center rounded-[11px]"
          style={catIconStyle(ci.color)}
        >
          <ci.Icon size={19} />
        </span>
        <div>
          <div className="text-[17px] font-medium text-text">{group.name}</div>
          <div className="text-[11px] text-text-faint">
            {group.items.length} {noun}
            {priceless.length > 0 && ` · ${priceless.length} narxsiz`}
          </div>
        </div>
      </div>

      {priceless.length > 0 && (
        <button
          type="button"
          onClick={() => setFillOpen(true)}
          className="mb-3 flex w-full items-center justify-center gap-2 rounded-btn border border-primary py-2.5 text-[13px] font-medium text-primary active:scale-[0.99]"
        >
          <IconWand size={16} /> Barcha narxlarni to‘ldirish
        </button>
      )}

      {group.items.length === 0 ? (
        <EmptyState text={`Bu kategoriyada hali ${noun} yo‘q.`} />
      ) : (
        <div className="overflow-hidden rounded-card border border-border bg-surface">
          {group.items.map((it, idx) => (
            <PriceRow
              key={it.id}
              item={it}
              ref={(el) => {
                priceRefs.current[idx] = el
              }}
              onCommit={(v) => {
                if ((Number(it.default_price) || 0) !== (v ?? 0)) {
                  updateItem.mutate({ id: it.id, default_price: v ?? 0 })
                }
              }}
              onEnter={() => {
                // keyingi narxsiz qatorga o'tadi
                for (let j = idx + 1; j < group.items.length; j++) {
                  if (Number(group.items[j].default_price) <= 0) {
                    priceRefs.current[j]?.focus()
                    return
                  }
                }
                priceRefs.current[idx]?.blur()
              }}
              onMenu={() => setMenuItem(it)}
            />
          ))}
        </div>
      )}

      <button
        type="button"
        onClick={() => setNewOpen(true)}
        className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-card border border-dashed border-border py-3 text-label text-primary active:bg-surface-2"
      >
        <IconPlus size={16} /> Yangi {noun}
      </button>

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
                className="flex min-h-[44px] w-full items-center gap-2 rounded-btn px-3 text-left text-body text-text active:bg-surface-2"
              >
                <span
                  className="flex h-6 w-6 items-center justify-center rounded-[7px]"
                  style={catIconStyle(catIcon(c.icon).color)}
                >
                  {(() => {
                    const I = catIcon(c.icon).Icon
                    return <I size={13} />
                  })()}
                </span>
                {c.name}
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

// Qatorda tahrirlanadigan narx
interface PriceRowProps {
  item: PriceItem
  onCommit: (v: number | null) => void
  onEnter: () => void
  onMenu: () => void
}

const PriceRow = forwardRef<HTMLInputElement, PriceRowProps>(function PriceRow(
  { item, onCommit, onEnter, onMenu },
  ref,
) {
  const [v, setV] = useState<number | null>(Number(item.default_price) || null)
  const [focused, setFocused] = useState(false)
  const last = useRef<number | null>(Number(item.default_price) || null)
  const cur = Number(item.default_price) || null
  if (last.current !== cur) {
    last.current = cur
    setV(cur)
  }
  const missing = (v ?? 0) <= 0

  return (
    <div
      className={`flex items-center gap-2 border-b border-border px-3 py-2.5 last:border-b-0 ${
        focused ? 'bg-primary-soft' : ''
      }`}
    >
      <div className="min-w-0 flex-1">
        <div className="truncate text-[13px] text-text">{item.name}</div>
        <div className="text-[11px] text-text-faint">
          {item.unit_label ?? item.unit}
        </div>
      </div>
      <MoneyInput
        ref={ref}
        value={v}
        onChange={setV}
        placeholder={missing ? 'narx yo‘q' : 'narx'}
        aria-label="narx"
        className={`w-24 shrink-0 bg-transparent py-1 text-right text-[14px] font-medium outline-none ${
          focused
            ? 'border-b-2 border-primary text-primary'
            : missing
              ? 'text-danger'
              : 'text-text'
        }`}
        onFocus={() => setFocused(true)}
        onBlur={() => {
          setFocused(false)
          onCommit(v)
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault()
            onCommit(v)
            onEnter()
          }
        }}
      />
      <button
        type="button"
        onClick={onMenu}
        aria-label="Amallar"
        className="shrink-0 text-text-faint active:text-text"
      >
        <IconDotsVertical size={18} />
      </button>
    </div>
  )
})

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
