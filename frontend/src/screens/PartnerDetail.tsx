import { useCallback, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { IconDotsVertical, IconPlus } from '@tabler/icons-react'
import type { PartnerPayment } from '../api/partners'
import type { PayMethod } from '../api/payments'
import { BottomSheet } from '../components/BottomSheet'
import { MoneyInput } from '../components/MoneyInput'
import { EmptyState, Screen } from '../components/Screen'
import { Segment } from '../components/Segment'
import { SplashSkeleton } from '../components/states'
import { useBackButton } from '../hooks/useBackButton'
import {
  usePartnerMutations,
  usePartnerPayments,
  usePartners,
} from '../hooks/usePartners'
import { METHOD_LABEL } from '../lib/entryVisual'
import { fmtDate, fmtDateGroup, fmtMoney, fmtPhone } from '../lib/format'
import { confirmDialog, hapticSuccess } from '../lib/telegram'
import { PartnerFormSheet } from './Partners'

const INPUT =
  'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

const METHOD_OPTIONS: { value: PayMethod; label: string }[] = [
  { value: 'cash', label: 'Naqd' },
  { value: 'card', label: 'Karta' },
  { value: 'transfer', label: 'O‘tkazma' },
]

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

/** Sherik sahifasi: jami berilgan + to'lovlar tarixi. */
export function PartnerDetail() {
  const navigate = useNavigate()
  const { id } = useParams()
  const partnerId = Number(id) || 0

  const list = usePartners()
  const payments = usePartnerPayments(partnerId)
  const { updatePartner, removePartner, createPayment } =
    usePartnerMutations()

  const [menuOpen, setMenuOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [addOpen, setAddOpen] = useState(false)
  const [selected, setSelected] = useState<PartnerPayment | null>(null)

  const back = useCallback(() => navigate('/partners'), [navigate])
  useBackButton(back)

  const partner = list.data?.partners.find((p) => p.id === partnerId)

  const groups = useMemo(() => {
    const map = new Map<string, PartnerPayment[]>()
    for (const p of payments.data ?? []) {
      const key = p.paid_at.slice(0, 10)
      const arr = map.get(key)
      if (arr) arr.push(p)
      else map.set(key, [p])
    }
    return [...map.entries()]
  }, [payments.data])

  if (list.isPending || payments.isPending) return <SplashSkeleton />
  if (!partner) {
    return (
      <Screen title="Brigada">
        <EmptyState text="Sherik topilmadi." />
      </Screen>
    )
  }

  async function remove() {
    if (!partner) return
    const count = partner.payments_count
    const msg =
      count > 0
        ? `${partner.name} va uning ${count} ta to‘lovi o‘chiriladi`
        : `${partner.name} o‘chiriladi`
    if (!(await confirmDialog(msg))) return
    setMenuOpen(false)
    await removePartner.mutateAsync(partner.id)
    hapticSuccess()
    navigate('/partners', { replace: true })
  }

  return (
    <Screen
      title={partner.name}
      action={
        <button
          type="button"
          aria-label="Amallar"
          onClick={() => setMenuOpen(true)}
          className="p-1.5 text-text-muted"
        >
          <IconDotsVertical size={20} />
        </button>
      }
    >
      <div className="rounded-card border border-border bg-surface p-4">
        <div className="text-label text-text-muted">Jami berilgan</div>
        <div className="text-title text-text">
          {fmtMoney(partner.total_paid)}
        </div>
        <div className="my-2 h-px w-1/2 bg-border" />
        <div className="text-label text-text-faint">
          {partner.payments_count} ta to‘lov
          {partner.last_payment_at &&
            ` · oxirgi: ${fmtDateGroup(partner.last_payment_at)}`}
        </div>
        {(partner.phone || partner.note) && (
          <div className="mt-2 text-label text-text-muted">
            {partner.phone && <div>{fmtPhone(partner.phone)}</div>}
            {partner.note && <div>{partner.note}</div>}
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={() => setAddOpen(true)}
        className="mt-3 flex min-h-[44px] w-full items-center justify-center gap-1.5 rounded-btn bg-primary text-body text-on-primary active:scale-[0.98]"
      >
        <IconPlus size={16} /> To‘lov qo‘shish
      </button>

      <section className="mt-5">
        <h2 className="mb-1.5 text-[11px] uppercase tracking-[0.06em] text-text-faint">
          To‘lovlar
        </h2>
        {groups.length === 0 ? (
          <EmptyState text="Hali to‘lov yo‘q." />
        ) : (
          <div className="space-y-3">
            {groups.map(([day, items]) => (
              <div key={day}>
                <div className="mb-1 text-label text-text-muted">
                  {fmtDateGroup(day)}
                </div>
                <div className="space-y-1.5">
                  {items.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => setSelected(p)}
                      className="block w-full rounded-card border border-border bg-surface p-3 text-left active:scale-[0.99]"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-body text-text">
                          {fmtMoney(p.amount)}
                        </span>
                        <span className="rounded-chip bg-surface-2 px-2 py-0.5 text-label text-text-muted">
                          {METHOD_LABEL[p.method]}
                        </span>
                      </div>
                      {p.note && (
                        <p className="mt-0.5 line-clamp-1 text-label text-text-muted">
                          {p.note}
                        </p>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Uch nuqta menyusi */}
      <BottomSheet
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
        title={partner.name}
      >
        <div className="space-y-2">
          <button
            type="button"
            onClick={() => {
              setMenuOpen(false)
              setEditOpen(true)
            }}
            className="min-h-[44px] w-full rounded-btn bg-surface-2 text-body text-text active:scale-[0.98]"
          >
            Tahrirlash
          </button>
          <button
            type="button"
            onClick={remove}
            disabled={removePartner.isPending}
            className="min-h-[44px] w-full rounded-btn bg-danger-soft text-body text-danger active:scale-[0.98] disabled:opacity-60"
          >
            O‘chirish
          </button>
        </div>
      </BottomSheet>

      <PartnerFormSheet
        open={editOpen}
        onClose={() => setEditOpen(false)}
        title="Sherikni tahrirlash"
        initial={partner}
        pending={updatePartner.isPending}
        onSave={async (body) => {
          await updatePartner.mutateAsync({ id: partner.id, ...body })
          hapticSuccess()
          setEditOpen(false)
        }}
      />

      <AddPartnerPaymentSheet
        open={addOpen}
        onClose={() => setAddOpen(false)}
        partnerName={partner.name}
        pending={createPayment.isPending}
        onSave={async (body) => {
          setAddOpen(false)
          await createPayment.mutateAsync({ partnerId: partner.id, ...body })
          hapticSuccess()
        }}
      />

      <PartnerPaymentDetailSheet
        partnerId={partner.id}
        payment={selected}
        onClose={() => setSelected(null)}
      />
    </Screen>
  )
}

// ---------------------------------------------------------------------------
// To'lov qo'shish varag'i
// ---------------------------------------------------------------------------
interface PaymentValues {
  amount: number
  method: PayMethod
  paid_at: string
  note?: string
}

function AddPartnerPaymentSheet({
  open,
  onClose,
  partnerName,
  pending,
  onSave,
}: {
  open: boolean
  onClose: () => void
  partnerName: string
  pending: boolean
  onSave: (body: PaymentValues) => Promise<void>
}) {
  const [amount, setAmount] = useState<number | null>(null)
  const [method, setMethod] = useState<PayMethod>('cash')
  const [paidAt, setPaidAt] = useState(today())
  const [note, setNote] = useState('')

  const wasOpen = useRef(false)
  if (open && !wasOpen.current) {
    wasOpen.current = true
    setAmount(null)
    setMethod('cash')
    setPaidAt(today())
    setNote('')
  }
  if (!open && wasOpen.current) wasOpen.current = false

  const ready = (amount ?? 0) > 0 && paidAt.length > 0

  return (
    <BottomSheet
      open={open}
      onClose={onClose}
      title={`To‘lov qo‘shish (${partnerName})`}
    >
      <div className="space-y-3">
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
        <label className="block text-label text-text-muted">
          Sana
          <input
            type="date"
            className={INPUT}
            value={paidAt}
            onChange={(e) => setPaidAt(e.target.value)}
          />
        </label>
        <Segment
          options={METHOD_OPTIONS}
          value={method}
          onChange={setMethod}
        />
        <label className="block text-label text-text-muted">
          Izoh (ixtiyoriy)
          <input
            className={INPUT}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            maxLength={300}
          />
        </label>
        <button
          type="button"
          disabled={!ready || pending}
          onClick={() =>
            void onSave({
              amount: amount ?? 0,
              method,
              paid_at: paidAt,
              note: note.trim() || undefined,
            })
          }
          className="min-h-[44px] w-full rounded-btn bg-primary text-body text-on-primary active:scale-[0.98] disabled:opacity-60"
        >
          Saqlash
        </button>
      </div>
    </BottomSheet>
  )
}

// ---------------------------------------------------------------------------
// To'lov batafsil: tahrirlash / o'chirish
// ---------------------------------------------------------------------------
function PartnerPaymentDetailSheet({
  partnerId,
  payment,
  onClose,
}: {
  partnerId: number
  payment: PartnerPayment | null
  onClose: () => void
}) {
  const { updatePayment, removePayment } = usePartnerMutations()
  const [editing, setEditing] = useState(false)
  const [amount, setAmount] = useState<number | null>(null)
  const [method, setMethod] = useState<PayMethod>('cash')
  const [paidAt, setPaidAt] = useState('')
  const [note, setNote] = useState('')

  const wasOpen = useRef(false)
  if (payment && !wasOpen.current) {
    wasOpen.current = true
    setEditing(false)
  }
  if (!payment && wasOpen.current) wasOpen.current = false

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
    const body = {
      id: payment.id,
      partnerId,
      amount: amount ?? 0,
      method,
      paid_at: paidAt,
      note: note.trim() || null,
    }
    setEditing(false)
    onClose()
    await updatePayment.mutateAsync(body)
    hapticSuccess()
  }

  async function remove() {
    if (!payment) return
    if (!(await confirmDialog('Bu to‘lov o‘chirilsinmi?'))) return
    const id = payment.id
    onClose()
    await removePayment.mutateAsync({ id, partnerId })
    hapticSuccess()
  }

  return (
    <BottomSheet open={!!payment} onClose={onClose} title="To‘lov">
      <div className="space-y-1.5 text-body">
        <Row k="Summa" v={fmtMoney(payment.amount)} strong />
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
            options={METHOD_OPTIONS}
            value={method}
            onChange={setMethod}
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
              maxLength={300}
            />
          </label>
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={save}
              disabled={updatePayment.isPending || (amount ?? 0) <= 0}
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
            disabled={removePayment.isPending}
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
