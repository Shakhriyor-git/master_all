import { useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { IconPencil, IconPlus, IconSearch } from '@tabler/icons-react'
import type { AiDraft } from '../api/ai'
import { listCategories, listPriceItems, type PriceItem } from '../api/catalog'
import type { CreateEntryBody, EntryKind, PayMethod } from '../api/entries'
import { AiInputBar } from '../components/AiInputBar'
import { EntryFormSheet } from '../components/EntryFormSheet'
import { MoneyInput } from '../components/MoneyInput'
import { NewServiceSheet } from '../components/NewServiceSheet'
import { QuantityInput } from '../components/QuantityInput'
import { Screen } from '../components/Screen'
import { Segment } from '../components/Segment'
import { useActiveProject } from '../hooks/activeProjectContext'
import { useCreateEntry } from '../hooks/useEntries'
import { useMainButton } from '../hooks/useMainButton'
import { KIND_LABEL, ROW_ICON, ROW_ICON_BG } from '../lib/entryVisual'
import { fmtMoney, fmtQty } from '../lib/format'
import { hapticSuccess } from '../lib/telegram'

const EXPENSE_NAMES = ['Tushlik', 'Taksi', 'Asbob', 'Boshqa']
const FI =
  'w-full rounded-btn border border-border bg-surface px-3 py-[13px] text-body text-text outline-none focus:border-primary'
const METHODS = [
  { value: 'cash', label: 'Naqd' },
  { value: 'card', label: 'Karta' },
  { value: 'transfer', label: 'O‘tkazma' },
]

export function Add() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const { active } = useActiveProject()

  const initial = params.get('type') as EntryKind | null
  const [kind, setKind] = useState<EntryKind>(
    initial && ['work', 'material', 'expense'].includes(initial)
      ? initial
      : 'work',
  )

  if (!active) {
    return (
      <Screen title="Qo‘shish">
        <p className="text-body text-text-muted">Obyekt topilmadi.</p>
      </Screen>
    )
  }

  return (
    <AddFlow
      key={kind}
      kind={kind}
      onKindChange={setKind}
      projectId={active.id}
      onDone={() => navigate(`/history?kind=${kind}`)}
    />
  )
}

function AddFlow({
  kind,
  onKindChange,
  projectId,
  onDone,
}: {
  kind: EntryKind
  onKindChange: (k: EntryKind) => void
  projectId: number
  onDone: () => void
}) {
  const [draft, setDraft] = useState<AiDraft | null>(null)
  const [formOpen, setFormOpen] = useState(false)

  return (
    <Screen title={`${KIND_LABEL[kind]} qo‘shish`}>
      <Segment
        options={[
          { value: 'work', label: 'Ish' },
          { value: 'material', label: 'Material' },
          { value: 'expense', label: 'Xarajat' },
        ]}
        value={kind}
        onChange={(v) => onKindChange(v as EntryKind)}
      />

      <AiInputBar
        projectId={projectId}
        onDraft={(d) => {
          setDraft(d)
          setFormOpen(true)
        }}
        onManual={() => {
          setDraft(null)
          setFormOpen(true)
        }}
      />
      <div className="mt-1 text-center text-[10px] text-text-faint">
        {kind === 'work'
          ? 'Yozing yoki ayting'
          : 'Yozing yoki chekni suratga oling'}
      </div>

      <div className="my-3 flex items-center gap-2">
        <span className="h-px flex-1 bg-border" />
        <span className="text-[10px] text-text-faint">yoki tanlang</span>
        <span className="h-px flex-1 bg-border" />
      </div>

      {kind === 'expense' ? (
        <ExpenseBody projectId={projectId} onDone={onDone} />
      ) : (
        <CatalogBody kind={kind} projectId={projectId} onDone={onDone} />
      )}

      <EntryFormSheet
        open={formOpen}
        onClose={() => setFormOpen(false)}
        projectId={projectId}
        draft={draft}
        initialKind={draft?.kind ?? kind}
        onSaved={onDone}
      />
    </Screen>
  )
}

// ---------------------------------------------------------------------------
// Ish / Material — katalogdan tanlab, keyin to'ldirish
// ---------------------------------------------------------------------------
function CatalogBody({
  kind,
  projectId,
  onDone,
}: {
  kind: 'work' | 'material'
  projectId: number
  onDone: () => void
}) {
  const create = useCreateEntry(projectId)
  const cats = useQuery({
    queryKey: ['categories', kind],
    queryFn: () => listCategories(kind),
  })
  const [categoryId, setCategoryId] = useState<number | null>(null)
  const [q, setQ] = useState('')
  const [item, setItem] = useState<PriceItem | null>(null)
  const [priceOverride, setPriceOverride] = useState<number | null>(null)
  const [qty, setQty] = useState<number | null>(null)
  const [method, setMethod] = useState<PayMethod>('cash')
  const [newOpen, setNewOpen] = useState(false)
  const [manualOpen, setManualOpen] = useState(false)

  const categories = cats.data ?? []
  const showCategoryStep = categories.length > 1
  const effectiveCategoryId = showCategoryStep ? categoryId : null

  const items = useQuery({
    queryKey: ['price-items', kind, effectiveCategoryId ?? 'all', q],
    queryFn: () =>
      listPriceItems({
        kind,
        categoryId: effectiveCategoryId ?? undefined,
        q: q || undefined,
      }),
    enabled: !showCategoryStep || categoryId != null,
  })

  const catalogEmpty =
    !cats.isPending &&
    categories.length === 0 &&
    !items.isPending &&
    (items.data?.length ?? 0) === 0 &&
    !q
  useEffect(() => {
    if (catalogEmpty) setNewOpen(true)
  }, [catalogEmpty])

  const price = item
    ? Number(item.default_price) > 0
      ? Number(item.default_price)
      : (priceOverride ?? 0)
    : 0
  const needsPrice = !!item && Number(item.default_price) <= 0
  const total = (qty ?? 0) * price
  const unit = item ? (item.unit_label ?? item.unit) : ''

  const ready =
    !!item && (qty ?? 0) > 0 && (!needsPrice || (priceOverride ?? 0) > 0)

  const save = useCallback(async () => {
    if (!item || !ready) return
    const body: CreateEntryBody = {
      price_item_id: item.id,
      quantity: qty ?? undefined,
      payment_method: kind === 'material' ? method : undefined,
    }
    if (needsPrice) body.unit_price = priceOverride ?? undefined
    await create.mutateAsync(body)
    hapticSuccess()
    onDone()
  }, [item, ready, qty, kind, method, needsPrice, priceOverride, create, onDone])

  useMainButton({
    text: 'Saqlash',
    onClick: save,
    visible: !!item,
    enabled: ready && !create.isPending,
    loading: create.isPending,
  })

  return (
    <>
      {showCategoryStep && (
        <div className="-mx-4 mb-3 flex gap-1.5 overflow-x-auto px-4">
          {categories.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => {
                setCategoryId(c.id)
                setItem(null)
              }}
              className={`shrink-0 rounded-chip border px-3 py-[7px] text-[12px] ${
                categoryId === c.id
                  ? 'border-primary bg-primary text-on-primary'
                  : 'border-border bg-surface text-text-muted'
              }`}
            >
              {c.name}
            </button>
          ))}
        </div>
      )}

      {catalogEmpty ? (
        <button
          type="button"
          onClick={() => setNewOpen(true)}
          className="flex w-full items-center justify-center gap-1.5 rounded-btn border border-dashed border-border py-4 text-label text-primary active:bg-surface-2"
        >
          <IconPlus size={16} /> Yangi{' '}
          {kind === 'material' ? 'material' : 'xizmat'} qo‘shish
        </button>
      ) : (
        (!showCategoryStep || categoryId != null) && (
          <>
            <div className="flex items-center gap-2 rounded-btn border border-border bg-surface px-3 py-2.5">
              <IconSearch size={15} className="shrink-0 text-text-faint" />
              <input
                className="min-w-0 flex-1 bg-transparent text-body text-text outline-none placeholder:text-text-faint"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Qidirish…"
              />
            </div>

            <div className="mt-2 max-h-72 overflow-y-auto overflow-hidden rounded-btn border border-border bg-surface">
              <button
                type="button"
                onClick={() => setManualOpen(true)}
                className="flex w-full items-center gap-2.5 bg-primary-soft px-3 py-[11px] text-left"
              >
                <IconPencil size={17} className="text-primary" />
                <span className="text-[13px] font-medium text-primary">
                  Qo‘lda kiritish
                </span>
              </button>
              {(items.data ?? []).map((it) => {
                const priced = Number(it.default_price) > 0
                return (
                  <button
                    key={it.id}
                    type="button"
                    onClick={() => {
                      setItem(it)
                      setPriceOverride(null)
                      setQty(null)
                    }}
                    className={`flex w-full items-center justify-between gap-2 border-t border-border px-3 py-3 text-left ${
                      item?.id === it.id ? 'bg-primary-soft' : ''
                    }`}
                  >
                    <span className="truncate text-[13px] text-text">
                      {it.name}
                    </span>
                    <span
                      className={`shrink-0 text-[12px] ${
                        priced ? 'text-text-muted' : 'text-danger'
                      }`}
                    >
                      {priced
                        ? `${fmtMoney(it.default_price)} · ${it.unit_label ?? it.unit}`
                        : `narxsiz · ${it.unit_label ?? it.unit}`}
                    </span>
                  </button>
                )
              })}
              <button
                type="button"
                onClick={() => setNewOpen(true)}
                className="flex w-full items-center gap-2.5 border-t border-border px-3 py-3 text-left"
              >
                <IconPlus size={16} className="text-text-muted" />
                <span className="text-[13px] text-text-muted">
                  Yangi {kind === 'material' ? 'material' : 'xizmat'}
                </span>
              </button>
            </div>
          </>
        )
      )}

      {item && (
        <div className="mt-4 space-y-2">
          <div className="mb-3 flex items-center gap-2.5">
            <span
              className={`flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-[11px] ${ROW_ICON_BG[kind]}`}
            >
              {(() => {
                const Icon = ROW_ICON[kind]
                return <Icon size={20} />
              })()}
            </span>
            <div className="min-w-0">
              <div className="truncate text-[16px] font-medium text-text">
                {item.name}
              </div>
              <div className="text-[11px] text-text-faint">
                {item.category_name ?? 'Kategoriyasiz'} · {unit}
              </div>
            </div>
          </div>

          {needsPrice && (
            <>
              <div className="text-[11px] text-text-muted">
                Bir {unit} narxi
              </div>
              <MoneyInput
                value={priceOverride}
                onChange={setPriceOverride}
                className={`${FI} text-[18px]`}
                autoFocus
              />
            </>
          )}

          <div className="text-[11px] text-text-muted">Miqdor</div>
          <QuantityInput
            value={qty}
            onChange={setQty}
            className={`${FI} text-[22px] font-medium`}
          />
          <div className="flex gap-1.5 pt-1">
            {[1, 5, 10].map((n) => (
              <QuickBtn key={n} onClick={() => setQty(n)}>
                {n}
              </QuickBtn>
            ))}
            <QuickBtn onClick={() => setQty((v) => (v ?? 0) + 1)}>+1</QuickBtn>
            <QuickBtn onClick={() => setQty((v) => Math.max(0, (v ?? 0) - 1))}>
              −1
            </QuickBtn>
          </div>

          {kind === 'material' && (
            <div className="pt-2">
              <div className="mb-1 text-[11px] text-text-muted">
                Qanday to‘landi
              </div>
              <Segment
                options={METHODS}
                value={method}
                onChange={(v) => setMethod(v as PayMethod)}
              />
            </div>
          )}

          {total > 0 && (
            <div className="rounded-btn bg-primary-soft p-3.5 text-center">
              <div className="text-[11px] text-primary">
                {fmtQty(qty ?? 0, unit)} × {fmtMoney(price)}
              </div>
              <div className="text-[24px] font-semibold text-primary">
                {fmtMoney(total)}
              </div>
            </div>
          )}
        </div>
      )}

      <NewServiceSheet
        open={newOpen}
        onClose={() => setNewOpen(false)}
        kind={kind}
        categoryId={effectiveCategoryId}
        onCreated={(it) => {
          setItem(it)
          setPriceOverride(null)
          setQty(null)
        }}
      />
      <EntryFormSheet
        open={manualOpen}
        onClose={() => setManualOpen(false)}
        projectId={projectId}
        initialKind={kind}
        onSaved={onDone}
      />
    </>
  )
}

// ---------------------------------------------------------------------------
// Xarajat — nom + bitta Summa maydoni
// ---------------------------------------------------------------------------
function ExpenseBody({
  projectId,
  onDone,
}: {
  projectId: number
  onDone: () => void
}) {
  const create = useCreateEntry(projectId)
  const [name, setName] = useState('')
  const [amount, setAmount] = useState<number | null>(null)
  const [method, setMethod] = useState<PayMethod>('cash')

  const ready = name.trim().length > 0 && (amount ?? 0) > 0

  const save = useCallback(async () => {
    if (!ready) return
    await create.mutateAsync({
      kind: 'expense',
      name: name.trim(),
      unit_price: amount ?? undefined,
      payment_method: method,
    })
    hapticSuccess()
    onDone()
  }, [ready, create, name, amount, method, onDone])

  useMainButton({
    text: 'Saqlash',
    onClick: save,
    visible: true,
    enabled: ready && !create.isPending,
    loading: create.isPending,
  })

  return (
    <div className="space-y-2">
      <div className="text-[11px] text-text-muted">Nomi</div>
      <input
        className={FI}
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="masalan: Tushlik"
      />
      <div className="flex gap-1.5 pt-1">
        {EXPENSE_NAMES.map((n) => (
          <QuickBtn key={n} onClick={() => setName(n)}>
            {n}
          </QuickBtn>
        ))}
      </div>

      <div className="pt-2 text-[11px] text-text-muted">Summa</div>
      <MoneyInput
        value={amount}
        onChange={setAmount}
        className={`${FI} text-[22px] font-medium`}
      />

      <div className="pt-2">
        <div className="mb-1 text-[11px] text-text-muted">Qanday to‘landi</div>
        <Segment
          options={METHODS}
          value={method}
          onChange={(v) => setMethod(v as PayMethod)}
        />
      </div>
    </div>
  )
}

function QuickBtn({
  children,
  onClick,
}: {
  children: ReactNode
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="min-h-[38px] flex-1 rounded-[10px] border border-border bg-surface text-[13px] text-text-muted active:scale-95"
    >
      {children}
    </button>
  )
}
