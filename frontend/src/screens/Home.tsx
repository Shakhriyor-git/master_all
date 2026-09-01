import {
  IconChevronRight,
  IconFileText,
  IconPackage,
  IconPlus,
  IconSelector,
} from '@tabler/icons-react'
import { useState } from 'react'
import type { ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import type { Entry, EntryKind } from '../api/entries'
import { reportPdfUrl } from '../api/report'
import { AddPaymentSheet } from '../components/AddPaymentSheet'
import { BottomSheet } from '../components/BottomSheet'
import { CountUp } from '../components/CountUp'
import { EmptyState, Screen } from '../components/Screen'
import { ProjectPicker } from '../components/ProjectPicker'
import { SplashSkeleton } from '../components/states'
import { useActiveProject } from '../hooks/activeProjectContext'
import { useRecentEntries, useSummary } from '../hooks/useEntries'
import { usePayments } from '../hooks/usePayments'
import { KIND_AMOUNT, KIND_LABEL, PURPOSE_LABEL } from '../lib/entryVisual'
import { fmtMoney, fmtQty } from '../lib/format'
import { openLink } from '../lib/telegram'

export function Home() {
  const { active, projects, isLoading, setActive } = useActiveProject()
  const [pickerOpen, setPickerOpen] = useState(false)
  const summary = useSummary(active?.id ?? 0)

  if (isLoading) return <SplashSkeleton />
  if (!active) {
    return (
      <Screen title="Asosiy">
        <EmptyState text="Hali obyekt yo‘q. Obyektni bot orqali oching." />
      </Screen>
    )
  }

  const s = summary.data
  const laborTotal = s ? Number(s.labor.works_total) : 0
  const spendTotal = s
    ? Number(s.labor.materials_by_master) +
      Number(s.labor.expenses_by_master) +
      Number(s.budget.spent_materials) +
      Number(s.budget.spent_expenses)
    : 0
  const owes = s ? Number(s.labor.client_owes) : 0
  const budgetLeft = s ? Number(s.budget.balance) : 0

  return (
    <Screen title="Asosiy">
      <button
        type="button"
        onClick={() => projects.length > 1 && setPickerOpen(true)}
        style={{ background: 'var(--grad)' }}
        className="w-full rounded-card p-4 text-left text-on-primary shadow-sm active:scale-[0.99]"
      >
        <div className="flex items-center gap-1">
          <span className="truncate text-title">{active.title}</span>
          {projects.length > 1 && (
            <IconSelector size={18} className="shrink-0 opacity-80" />
          )}
        </div>
        {active.client_name && (
          <div className="text-label opacity-80">{active.client_name}</div>
        )}
        <div className="mt-3 grid grid-cols-2 gap-3">
          <div>
            <div className="text-label opacity-80">Jami ish haqi</div>
            <CountUp value={laborTotal} className="text-title" />
          </div>
          <div>
            <div className="text-label opacity-80">Jami xarajat</div>
            <CountUp value={spendTotal} className="text-title" />
          </div>
        </div>
      </button>

      <ReportButton projectId={active.id} />

      <Block kind="work" projectId={active.id} title="Bajarilgan ishlar" />
      <Block kind="material" projectId={active.id} title="Materiallar" />
      <Block
        kind="expense"
        projectId={active.id}
        title="Xarajatlar"
        hideIfEmpty
      />

      <PaymentsBlock projectId={active.id} />

      <div className="mt-3 grid grid-cols-2 gap-3">
        <MiniCard
          label={owes < 0 ? 'Mijoz avansi' : 'Mijoz qarzi'}
          value={fmtMoney(Math.abs(owes))}
        />
        <MiniCard
          label="Budjet qoldig‘i"
          value={fmtMoney(budgetLeft)}
          to="/budget"
        />
      </div>

      <ProjectPicker
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        projects={projects}
        activeId={active.id}
        onPick={setActive}
      />
    </Screen>
  )
}

function Block({
  kind,
  projectId,
  title,
  hideIfEmpty,
}: {
  kind: EntryKind
  projectId: number
  title: string
  hideIfEmpty?: boolean
}) {
  const navigate = useNavigate()
  const { data: recent = [], isLoading } = useRecentEntries(projectId, kind)

  if (hideIfEmpty && !isLoading && recent.length === 0) return null

  return (
    <section className="mt-4">
      <div className="mb-1.5 flex items-center justify-between">
        <h2 className="text-label uppercase text-text-muted">{title}</h2>
        {recent.length > 0 && (
          <Link
            to={`/history?kind=${kind}`}
            className="text-label text-primary"
          >
            Barchasi
          </Link>
        )}
      </div>

      <div className="overflow-hidden rounded-card border border-border bg-surface">
        {recent.length === 0 ? (
          <p className="px-3 py-3 text-label text-text-faint">
            Hali qo‘shilmagan
          </p>
        ) : (
          recent.map((e: Entry) => (
            <div
              key={e.id}
              className="flex items-baseline justify-between gap-2 border-b border-border px-3 py-2 last:border-b-0"
            >
              <span className="truncate text-body text-text">{e.name}</span>
              <span className={`shrink-0 text-body ${KIND_AMOUNT[kind]}`}>
                {kind === 'expense'
                  ? fmtMoney(e.amount)
                  : `${fmtQty(e.quantity, e.unit_label ?? e.unit)} · ${fmtMoney(e.amount)}`}
              </span>
            </div>
          ))
        )}
        <button
          type="button"
          onClick={() => navigate(`/add?type=${kind}`)}
          className="flex w-full items-center justify-center gap-1 border-t border-dashed border-border py-2.5 text-label text-primary active:bg-surface-2"
        >
          + {KIND_LABEL[kind]} qo‘shish
          <IconChevronRight size={14} />
        </button>
      </div>
    </section>
  )
}

function ReportButton({ projectId }: { projectId: number }) {
  const [open, setOpen] = useState(false)
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')

  const inputClass =
    'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-card border border-border bg-surface py-2.5 text-label text-primary active:scale-[0.99]"
      >
        <IconFileText size={16} /> Hisobot (PDF)
      </button>

      <BottomSheet
        open={open}
        onClose={() => setOpen(false)}
        title="Hisobot (PDF)"
      >
        <div className="space-y-3">
          <p className="text-label text-text-muted">
            Sana oralig‘ini tanlamasangiz — butun davr bo‘yicha.
          </p>
          <div className="grid grid-cols-2 gap-2">
            <label className="block text-label text-text-muted">
              Dan
              <input
                type="date"
                className={inputClass}
                value={from}
                onChange={(e) => setFrom(e.target.value)}
              />
            </label>
            <label className="block text-label text-text-muted">
              Gacha
              <input
                type="date"
                className={inputClass}
                value={to}
                onChange={(e) => setTo(e.target.value)}
              />
            </label>
          </div>

          <ReportOption
            icon={<IconFileText size={20} />}
            title="Ish haqi hisoboti"
            hint="Bajarilgan ishlar va qoldiq"
            onClick={() => {
              openLink(
                reportPdfUrl(projectId, 'labor', {
                  dateFrom: from || undefined,
                  dateTo: to || undefined,
                }),
              )
              setOpen(false)
            }}
          />
          <ReportOption
            icon={<IconPackage size={20} />}
            title="Material va xarajatlar"
            hint="Materiallar, xarajatlar va qoldiq"
            onClick={() => {
              openLink(
                reportPdfUrl(projectId, 'materials', {
                  dateFrom: from || undefined,
                  dateTo: to || undefined,
                }),
              )
              setOpen(false)
            }}
          />
        </div>
      </BottomSheet>
    </>
  )
}

function ReportOption({
  icon,
  title,
  hint,
  onClick,
}: {
  icon: ReactNode
  title: string
  hint: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-center gap-3 rounded-card border border-border bg-surface px-4 py-3 text-left active:scale-[0.99]"
    >
      <span className="text-primary">{icon}</span>
      <span className="min-w-0">
        <span className="block text-body text-text">{title}</span>
        <span className="block text-label text-text-faint">{hint}</span>
      </span>
      <IconChevronRight size={16} className="ml-auto shrink-0 text-text-faint" />
    </button>
  )
}

function PaymentsBlock({ projectId }: { projectId: number }) {
  const { data: payments = [] } = usePayments(projectId)
  const [addOpen, setAddOpen] = useState(false)
  const recent = payments.slice(0, 3)

  return (
    <section className="mt-4">
      <div className="mb-1.5 flex items-center justify-between">
        <h2 className="text-label uppercase text-text-muted">
          Mijoz to‘lovlari
        </h2>
        {payments.length > 0 && (
          <Link to="/history?kind=payment" className="text-label text-primary">
            Barchasi
          </Link>
        )}
      </div>

      <div className="overflow-hidden rounded-card border border-border bg-surface">
        {recent.length === 0 ? (
          <p className="px-3 py-3 text-label text-text-faint">
            Hali to‘lov yo‘q
          </p>
        ) : (
          recent.map((p) => (
            <div
              key={p.id}
              className="flex items-baseline justify-between gap-2 border-b border-border px-3 py-2 last:border-b-0"
            >
              <span className="truncate text-label text-text-muted">
                {PURPOSE_LABEL[p.purpose]}
              </span>
              <span className="shrink-0 text-body text-success">
                + {fmtMoney(p.amount)}
              </span>
            </div>
          ))
        )}
        <button
          type="button"
          onClick={() => setAddOpen(true)}
          className="flex w-full items-center justify-center gap-1 border-t border-dashed border-border py-2.5 text-label text-primary active:bg-surface-2"
        >
          + To‘lov qo‘shish
          <IconPlus size={14} />
        </button>
      </div>

      <AddPaymentSheet
        open={addOpen}
        onClose={() => setAddOpen(false)}
        projectId={projectId}
      />
    </section>
  )
}

function MiniCard({
  label,
  value,
  to,
}: {
  label: string
  value: string
  to?: string
}) {
  const inner = (
    <>
      <div className="text-label text-text-muted">{label}</div>
      <div className="mt-0.5 text-body text-text">{value}</div>
    </>
  )
  const cls = 'block rounded-card border border-border bg-surface p-3'
  return to ? (
    <Link to={to} className={`${cls} active:scale-[0.99]`}>
      {inner}
    </Link>
  ) : (
    <div className={cls}>{inner}</div>
  )
}
