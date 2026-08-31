import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Entry } from '../api/entries'
import { EntryCard } from '../components/EntryCard'
import { EntryDetailSheet } from '../components/EntryDetailSheet'
import { BottomSheet } from '../components/BottomSheet'
import { CountUp } from '../components/CountUp'
import { MoneyInput } from '../components/MoneyInput'
import { EmptyState, Screen } from '../components/Screen'
import { SplashSkeleton } from '../components/states'
import { useActiveProject } from '../hooks/activeProjectContext'
import { useBackButton } from '../hooks/useBackButton'
import { useDeleteEntry, useEntries, useSummary } from '../hooks/useEntries'
import { useCreatePayment } from '../hooks/usePayments'
import { fmtMoney } from '../lib/format'
import { confirmDialog, hapticSuccess } from '../lib/telegram'

const INPUT =
  'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

export function Budget() {
  const navigate = useNavigate()
  const { active, isLoading } = useActiveProject()
  useBackButton(() => navigate(-1))

  const summary = useSummary(active?.id ?? 0)
  const entriesQ = useEntries({
    projectId: active?.id ?? 0,
    paidBy: 'client',
  })
  const del = useDeleteEntry(active?.id ?? 0)
  const createPayment = useCreatePayment(active?.id ?? 0)

  const [addOpen, setAddOpen] = useState(false)
  const [selected, setSelected] = useState<Entry | null>(null)

  if (isLoading) return <SplashSkeleton />
  if (!active) {
    return (
      <Screen title="Budjet">
        <EmptyState text="Obyekt topilmadi." />
      </Screen>
    )
  }

  const b = summary.data?.budget
  const given = b ? Number(b.given) : 0
  const spent = b ? Number(b.spent_total) : 0
  const balance = b ? Number(b.balance) : 0

  const entries = entriesQ.data?.pages.flatMap((p) => p.items) ?? []

  async function quickDelete(e: Entry) {
    if (!(await confirmDialog('Bu yozuv o‘chirilsinmi?'))) return
    await del.mutateAsync(e.id)
    hapticSuccess()
  }

  return (
    <Screen title="Budjet">
      <div className="rounded-card border border-border bg-surface p-4">
        <div className="grid grid-cols-2 gap-2">
          <Num label="Berilgan" value={given} />
          <Num label="Sarflangan" value={spent} />
        </div>
        <div className="mt-3 border-t border-border pt-3">
          <div className="text-label text-text-muted">Qoldiq</div>
          <CountUp
            value={balance}
            className={`block text-title ${
              balance < 0 ? 'text-danger' : 'text-text'
            }`}
          />
        </div>
      </div>

      <button
        type="button"
        onClick={() => setAddOpen(true)}
        className="mt-3 w-full rounded-btn bg-primary py-3 text-body text-on-primary active:scale-[0.99]"
      >
        + Mijoz pul berdi
      </button>

      {given === 0 ? (
        <div className="mt-4">
          <EmptyState text="Mijoz hali pul bermagan." />
        </div>
      ) : (
        <section className="mt-4">
          <h2 className="mb-1.5 text-label uppercase text-text-muted">
            Budjetdan sarflangan
          </h2>
          {entriesQ.isPending ? (
            <div className="space-y-2">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="h-20 animate-pulse rounded-card border border-border bg-surface"
                />
              ))}
            </div>
          ) : entries.length === 0 ? (
            <EmptyState text="Bu budjetdan hali xarajat yo‘q." />
          ) : (
            <div className="space-y-2">
              {entries.map((e) => (
                <EntryCard
                  key={e.id}
                  entry={e}
                  onOpen={setSelected}
                  onDelete={quickDelete}
                />
              ))}
            </div>
          )}
        </section>
      )}

      <AddBudgetSheet
        open={addOpen}
        onClose={() => setAddOpen(false)}
        pending={createPayment.isPending}
        onSave={async (amount, paidAt, note) => {
          await createPayment.mutateAsync({
            amount,
            purpose: 'budget',
            paid_at: paidAt,
            note: note || undefined,
          })
          hapticSuccess()
          setAddOpen(false)
        }}
      />
      <EntryDetailSheet
        projectId={active.id}
        entry={selected}
        onClose={() => setSelected(null)}
      />
    </Screen>
  )
}

function Num({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="text-label text-text-muted">{label}</div>
      <div className="text-body text-text">{fmtMoney(value)}</div>
    </div>
  )
}

function AddBudgetSheet({
  open,
  onClose,
  onSave,
  pending,
}: {
  open: boolean
  onClose: () => void
  onSave: (amount: number, paidAt: string, note: string) => Promise<void>
  pending: boolean
}) {
  const [amount, setAmount] = useState<number | null>(null)
  const [paidAt, setPaidAt] = useState(today())
  const [note, setNote] = useState('')

  const wasOpen = useRef(false)
  if (open && !wasOpen.current) {
    wasOpen.current = true
    setAmount(null)
    setPaidAt(today())
    setNote('')
  }
  if (!open && wasOpen.current) wasOpen.current = false

  return (
    <BottomSheet open={open} onClose={onClose} title="Mijoz pul berdi">
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
          disabled={(amount ?? 0) <= 0 || pending}
          onClick={() => {
            if ((amount ?? 0) > 0) void onSave(amount ?? 0, paidAt, note.trim())
          }}
          className="min-h-[44px] w-full rounded-btn bg-primary text-body text-on-primary active:scale-[0.98] disabled:opacity-60"
        >
          Saqlash
        </button>
      </div>
    </BottomSheet>
  )
}
