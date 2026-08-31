import { useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  IconPackage,
  IconPencil,
  IconPlus,
  IconReceipt,
  IconTool,
} from '@tabler/icons-react'
import type { AiDraft } from '../api/ai'
import {
  listCategories,
  listPriceItems,
  type PriceItem,
} from '../api/catalog'
import type { CreateEntryBody, EntryKind, PayMethod } from '../api/entries'
import { AiInputBar } from '../components/AiInputBar'
import { Chips } from '../components/Chips'
import { EntryFormSheet } from '../components/EntryFormSheet'
import { MoneyInput } from '../components/MoneyInput'
import { NewServiceSheet } from '../components/NewServiceSheet'
import { QuantityInput } from '../components/QuantityInput'
import { Screen } from '../components/Screen'
import { Segment } from '../components/Segment'
import { useActiveProject } from '../hooks/activeProjectContext'
import { useCreateEntry, useSummary } from '../hooks/useEntries'
import { useMainButton } from '../hooks/useMainButton'
import { KIND_LABEL } from '../lib/entryVisual'
import { fmtMoney, fmtQty } from '../lib/format'
import { hapticSuccess } from '../lib/telegram'

const EXPENSE_NAMES = ['Tushlik', 'Taksi', 'Asbob', 'Boshqa']
const INPUT =
  'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

export function Add() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const { active } = useActiveProject()

  const initialType = params.get('type') as EntryKind | null
  const [type, setType] = useState<EntryKind | null>(
    initialType && ['work', 'material', 'expense'].includes(initialType)
      ? initialType
      : null,
  )
  const [draft, setDraft] = useState<AiDraft | null>(null)
  const [formOpen, setFormOpen] = useState(false)

  if (!active) {
    return (
      <Screen title="Qo‘shish">
        <p className="text-body text-text-muted">Obyekt topilmadi.</p>
      </Screen>
    )
  }

  if (!type) {
    return (
      <Screen title="Qo‘shish">
        <AiInputBar
          projectId={active.id}
          onDraft={(d) => {
            setDraft(d)
            setFormOpen(true)
          }}
          onManual={() => {
            setDraft(null)
            setFormOpen(true)
          }}
        />

        <div className="my-3 flex items-center gap-3">
          <span className="h-px flex-1 bg-border" />
          <span className="text-label text-text-faint">yoki</span>
          <span className="h-px flex-1 bg-border" />
        </div>

        <div className="space-y-3">
          <TypeButton
            icon={<IconTool size={22} />}
            label="Ish"
            onClick={() => setType('work')}
          />
          <TypeButton
            icon={<IconPackage size={22} />}
            label="Material"
            onClick={() => setType('material')}
          />
          <TypeButton
            icon={<IconReceipt size={22} />}
            label="Xarajat"
            onClick={() => setType('expense')}
          />
        </div>

        <EntryFormSheet
          open={formOpen}
          onClose={() => setFormOpen(false)}
          projectId={active.id}
          draft={draft}
          initialKind={draft?.kind ?? 'material'}
          onSaved={() =>
            navigate(`/history?kind=${draft?.kind ?? 'material'}`)
          }
        />
      </Screen>
    )
  }

  return type === 'expense' ? (
    <ExpenseFlow
      projectId={active.id}
      onDone={() => navigate('/history?kind=expense')}
    />
  ) : (
    <ServiceFlow
      key={type}
      kind={type}
      projectId={active.id}
      onDone={() => navigate(`/history?kind=${type}`)}
    />
  )
}

function TypeButton({
  icon,
  label,
  onClick,
}: {
  icon: ReactNode
  label: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex min-h-[56px] w-full items-center gap-3 rounded-card border border-border bg-surface px-4 text-title text-text active:scale-[0.99]"
    >
      <span className="text-primary">{icon}</span>
      {label}
    </button>
  )
}

// ---------------------------------------------------------------------------
// Ish / Material
// ---------------------------------------------------------------------------
function ServiceFlow({
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
  const [paidBy, setPaidBy] = useState<'master' | 'client'>('master')
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

  // Katalog bo'sh bo'lsa — to'g'ridan-to'g'ri "Yangi qo'shish" formasi
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

  const ready =
    !!item &&
    (qty ?? 0) > 0 &&
    (!needsPrice || (priceOverride ?? 0) > 0)

  const save = useCallback(async () => {
    if (!item || !ready) return
    const body: CreateEntryBody = {
      price_item_id: item.id,
      quantity: qty ?? undefined,
      paid_by: kind === 'material' ? paidBy : undefined,
      payment_method: kind === 'material' ? method : undefined,
    }
    if (needsPrice) body.unit_price = priceOverride ?? undefined
    await create.mutateAsync(body)
    hapticSuccess()
    onDone()
  }, [
    item,
    ready,
    qty,
    kind,
    paidBy,
    method,
    needsPrice,
    priceOverride,
    create,
    onDone,
  ])

  useMainButton({
    text: 'Saqlash',
    onClick: save,
    visible: true,
    enabled: ready && !create.isPending,
    loading: create.isPending,
  })

  return (
    <Screen title={`${KIND_LABEL[kind]} qo‘shish`}>
      {showCategoryStep && (
        <div className="mb-3">
          <Chips
            options={categories.map((c) => ({
              value: String(c.id),
              label: `${c.icon ?? ''} ${c.name}`.trim(),
            }))}
            value={categoryId != null ? String(categoryId) : null}
            onChange={(v) => {
              setCategoryId(Number(v))
              setItem(null)
            }}
          />
        </div>
      )}

      {catalogEmpty ? (
        <button
          type="button"
          onClick={() => setNewOpen(true)}
          className="flex w-full items-center justify-center gap-1.5 rounded-card border border-dashed border-border py-4 text-label text-primary active:bg-surface-2"
        >
          <IconPlus size={16} />{' '}
          Yangi {kind === 'material' ? 'material' : 'xizmat'} qo‘shish
        </button>
      ) : (!showCategoryStep || categoryId != null) && (
        <>
          <input
            className={INPUT}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={
              kind === 'material'
                ? 'Materialni qidiring…'
                : 'Xizmatni qidiring…'
            }
          />
          <button
            type="button"
            onClick={() => setManualOpen(true)}
            className="mt-2 flex w-full items-center gap-1.5 rounded-btn border border-dashed border-border px-3 py-2.5 text-label text-primary active:bg-surface-2"
          >
            <IconPencil size={15} /> Qo‘lda kiritish
          </button>
          <div className="mt-2 max-h-64 overflow-y-auto rounded-card border border-border bg-surface">
            {(items.data ?? []).map((it) => (
              <button
                key={it.id}
                type="button"
                onClick={() => {
                  setItem(it)
                  setPriceOverride(null)
                }}
                className={`flex w-full items-center justify-between gap-2 border-b border-border px-3 py-2.5 text-left last:border-b-0 ${
                  item?.id === it.id ? 'bg-primary-soft' : ''
                }`}
              >
                <span className="truncate text-body text-text">{it.name}</span>
                <span className="shrink-0 text-label text-text-muted">
                  {Number(it.default_price) > 0
                    ? `${fmtMoney(it.default_price)} / ${it.unit_label ?? it.unit}`
                    : `narxsiz · ${it.unit_label ?? it.unit}`}
                </span>
              </button>
            ))}
            <button
              type="button"
              onClick={() => setNewOpen(true)}
              className="flex w-full items-center gap-1.5 px-3 py-2.5 text-label text-primary"
            >
              <IconPlus size={16} /> Yangi qo‘shish
            </button>
          </div>
        </>
      )}

      {item && (
        <div className="mt-4 space-y-3">
          {needsPrice && (
            <label className="block text-label text-text-muted">
              Bir birlik narxi ({item.unit_label ?? item.unit})
              <MoneyInput
                value={priceOverride}
                onChange={setPriceOverride}
                className={INPUT}
                autoFocus
              />
            </label>
          )}

          <div>
            <div className="mb-1 text-label text-text-muted">
              Miqdor · {item.unit_label ?? item.unit}
            </div>
            <QuantityInput
              value={qty}
              onChange={setQty}
              className={`${INPUT} text-title`}
            />
            <div className="mt-2 flex gap-1.5">
              {[1, 5, 10].map((n) => (
                <QuickBtn key={n} onClick={() => setQty(n)}>
                  {n}
                </QuickBtn>
              ))}
              <QuickBtn onClick={() => setQty((v) => (v ?? 0) + 1)}>
                +1
              </QuickBtn>
              <QuickBtn
                onClick={() => setQty((v) => Math.max(0, (v ?? 0) - 1))}
              >
                −1
              </QuickBtn>
            </div>
          </div>

          {kind === 'material' && (
            <div className="space-y-2">
              <Segment
                options={[
                  { value: 'master', label: 'Men' },
                  { value: 'client', label: 'Mijoz' },
                ]}
                value={paidBy}
                onChange={(v) => setPaidBy(v as 'master' | 'client')}
              />
              <Segment
                options={[
                  { value: 'cash', label: 'Naqd' },
                  { value: 'card', label: 'Karta' },
                  { value: 'transfer', label: 'O‘tkazma' },
                ]}
                value={method}
                onChange={(v) => setMethod(v as PayMethod)}
              />
              {paidBy === 'client' && (
                <BudgetHint projectId={projectId} spend={total} />
              )}
            </div>
          )}

          <div className="rounded-card border border-border bg-surface p-3 text-center">
            <span className="text-body text-text-muted">
              {fmtQty(qty ?? 0)} × {fmtMoney(price)} ={' '}
            </span>
            <span className="text-title text-text">{fmtMoney(total)}</span>
          </div>
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
        }}
      />

      <EntryFormSheet
        open={manualOpen}
        onClose={() => setManualOpen(false)}
        projectId={projectId}
        initialKind={kind}
        onSaved={onDone}
      />
    </Screen>
  )
}

// ---------------------------------------------------------------------------
// Xarajat
// ---------------------------------------------------------------------------
function ExpenseFlow({
  projectId,
  onDone,
}: {
  projectId: number
  onDone: () => void
}) {
  const create = useCreateEntry(projectId)
  const [name, setName] = useState('')
  const [amount, setAmount] = useState<number | null>(null)
  const [paidBy, setPaidBy] = useState<'master' | 'client'>('master')
  const [method, setMethod] = useState<PayMethod>('cash')

  const ready = name.trim().length > 0 && (amount ?? 0) > 0

  const save = useCallback(async () => {
    if (!ready) return
    await create.mutateAsync({
      kind: 'expense',
      name: name.trim(),
      unit_price: amount ?? undefined,
      paid_by: paidBy,
      payment_method: method,
    })
    hapticSuccess()
    onDone()
  }, [ready, create, name, amount, paidBy, method, onDone])

  useMainButton({
    text: 'Saqlash',
    onClick: save,
    visible: true,
    enabled: ready && !create.isPending,
    loading: create.isPending,
  })

  return (
    <Screen title="Xarajat qo‘shish">
      <div className="space-y-3">
        <div>
          <div className="mb-1 text-label text-text-muted">Nomi</div>
          <input
            className={INPUT}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="masalan: Tushlik"
          />
          <div className="mt-2 flex gap-1.5">
            {EXPENSE_NAMES.map((n) => (
              <QuickBtn key={n} onClick={() => setName(n)}>
                {n}
              </QuickBtn>
            ))}
          </div>
        </div>

        <label className="block text-label text-text-muted">
          Summa
          <MoneyInput
            value={amount}
            onChange={setAmount}
            className={`${INPUT} text-title`}
          />
        </label>

        <Segment
          options={[
            { value: 'master', label: 'Men' },
            { value: 'client', label: 'Mijoz' },
          ]}
          value={paidBy}
          onChange={(v) => setPaidBy(v as 'master' | 'client')}
        />
        <Segment
          options={[
            { value: 'cash', label: 'Naqd' },
            { value: 'card', label: 'Karta' },
            { value: 'transfer', label: 'O‘tkazma' },
          ]}
          value={method}
          onChange={(v) => setMethod(v as PayMethod)}
        />
        {paidBy === 'client' && (
          <BudgetHint projectId={projectId} spend={amount ?? 0} />
        )}
      </div>
    </Screen>
  )
}

// ---------------------------------------------------------------------------
// Mijoz budjeti — yozuv qo'shishda jonli qoldiq
// ---------------------------------------------------------------------------
function BudgetHint({
  projectId,
  spend,
}: {
  projectId: number
  spend: number
}) {
  const summary = useSummary(projectId)
  const b = summary.data?.budget
  const given = Number(b?.given ?? 0)
  const balance = Number(b?.balance ?? 0)

  if (given <= 0) {
    return (
      <div className="rounded-btn bg-surface-2 px-3 py-2 text-label text-text-muted">
        Mijoz hali pul bermagan.{' '}
        <Link to="/budget" className="text-primary">
          Qo‘shish
        </Link>
      </div>
    )
  }

  const after = balance - spend
  return (
    <div className="rounded-btn bg-surface-2 px-3 py-2 text-label">
      <div className="text-text-muted">
        Mijoz budjeti: {fmtMoney(balance)} → {fmtMoney(after)} qoladi
      </div>
      {after < 0 && (
        <div className="mt-0.5 text-danger">
          ⚠️ Budjetdan {fmtMoney(-after)} oshib ketadi
        </div>
      )}
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
      className="min-h-[40px] flex-1 rounded-btn bg-surface-2 text-body text-text active:scale-95"
    >
      {children}
    </button>
  )
}
