import {
  IconCash,
  IconChevronRight,
  IconFileText,
  IconLoader2,
  IconMusic,
  IconPackage,
  IconPlayerPauseFilled,
  IconPlayerPlayFilled,
  IconReceipt,
  IconSelector,
  IconTool,
} from '@tabler/icons-react'
import { useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { reportPdfUrl } from '../api/report'
import { AddPaymentSheet } from '../components/AddPaymentSheet'
import { BottomSheet } from '../components/BottomSheet'
import { CountUp } from '../components/CountUp'
import { ProjectPicker } from '../components/ProjectPicker'
import { RowCard } from '../components/RowCard'
import { PaymentCard } from '../components/PaymentCard'
import { EmptyState, Screen } from '../components/Screen'
import { SplashSkeleton } from '../components/states'
import { useActiveProject } from '../hooks/activeProjectContext'
import { useSummary } from '../hooks/useEntries'
import { useTimeline } from '../hooks/useTimeline'
import { fmtMoney, fmtNumber, fmtQty } from '../lib/format'
import { openLink } from '../lib/telegram'
import { useMusic } from '../music/musicContext'

export function Home() {
  const { active, projects, isLoading, setActive } = useActiveProject()
  const [pickerOpen, setPickerOpen] = useState(false)
  const [payOpen, setPayOpen] = useState(false)
  const navigate = useNavigate()
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
  const works = s ? Number(s.labor.works_total) : 0
  const paid = s ? Number(s.labor.paid) : 0
  const owes = s ? Number(s.labor.remaining) : 0

  return (
    <Screen title="Asosiy">
      <div className="mb-3.5 flex items-center justify-between">
        <button
          type="button"
          onClick={() => projects.length > 1 && setPickerOpen(true)}
          className="text-left"
        >
          <div className="text-[11px] text-text-faint">Obyekt</div>
          <div className="flex items-center gap-1 text-[15px] font-medium text-text">
            <span className="truncate">{active.title}</span>
            {projects.length > 1 && (
              <IconSelector size={14} className="shrink-0 text-text-faint" />
            )}
          </div>
        </button>
        <MusicButton />
      </div>

      <Hero owes={owes} works={works} paid={paid} />

      <ReportButton projectId={active.id} />

      <QuickBar
        onAdd={(t) => navigate(`/add?type=${t}`)}
        onPay={() => setPayOpen(true)}
      />

      <div className="mb-2 flex items-baseline justify-between">
        <h2 className="text-[11px] uppercase tracking-[0.06em] text-text-faint">
          So‘nggi yozuvlar
        </h2>
        <button
          type="button"
          onClick={() => navigate('/history')}
          className="text-[11px] text-primary"
        >
          Barchasi
        </button>
      </div>
      <Recent projectId={active.id} />

      <ProjectPicker
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        projects={projects}
        activeId={active.id}
        onPick={setActive}
      />
      <AddPaymentSheet
        open={payOpen}
        onClose={() => setPayOpen(false)}
        projectId={active.id}
      />
    </Screen>
  )
}

function MusicButton() {
  const m = useMusic()
  const [sheetOpen, setSheetOpen] = useState(false)
  const lastTap = useRef(0)
  const longTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const longFired = useRef(false)

  if (!m.available) return null

  function clearLong() {
    if (longTimer.current) {
      clearTimeout(longTimer.current)
      longTimer.current = null
    }
  }

  function handleClick() {
    if (longFired.current) {
      longFired.current = false
      return
    }
    const now = Date.now()
    if (now - lastTap.current < 300) {
      lastTap.current = 0
      m.restart()
    } else {
      lastTap.current = now
      setTimeout(() => {
        if (lastTap.current === now) m.toggle()
      }, 300)
    }
  }

  const Icon = m.loading
    ? IconLoader2
    : m.playing
      ? IconPlayerPauseFilled
      : IconPlayerPlayFilled

  return (
    <>
      <button
        type="button"
        aria-label="Musiqa"
        onClick={handleClick}
        onPointerDown={() => {
          longFired.current = false
          clearLong()
          longTimer.current = setTimeout(() => {
            longFired.current = true
            setSheetOpen(true)
          }, 500)
        }}
        onPointerUp={clearLong}
        onPointerLeave={clearLong}
        onPointerCancel={clearLong}
        className={`flex h-[30px] w-[30px] items-center justify-center rounded-full bg-primary-soft text-primary ${
          m.playing && !m.loading ? 'animate-pulse' : ''
        }`}
      >
        <Icon size={15} className={m.loading ? 'animate-spin' : ''} />
      </button>

      <BottomSheet
        open={sheetOpen}
        onClose={() => setSheetOpen(false)}
        title="Musiqa"
      >
        <div className="space-y-1">
          {m.tracks.map((t, i) => (
            <button
              key={t.id}
              type="button"
              onClick={() => {
                m.playIndex(i)
                setSheetOpen(false)
              }}
              className={`flex min-h-[44px] w-full items-center gap-2 rounded-btn px-3 text-left text-body active:bg-surface-2 ${
                i === m.index ? 'text-primary' : 'text-text'
              }`}
            >
              <IconMusic size={15} className="shrink-0" />
              <span className="truncate">{t.original_name}</span>
            </button>
          ))}
        </div>
      </BottomSheet>
    </>
  )
}

function Hero({
  owes,
  works,
  paid,
}: {
  owes: number
  works: number
  paid: number
}) {
  const advance = owes < 0
  return (
    <div
      className="relative mb-3 overflow-hidden rounded-2xl p-[18px]"
      style={{ background: 'var(--grad)' }}
    >
      <div className="absolute -right-[34px] -top-[34px] h-[126px] w-[126px] rounded-full bg-white/[0.08]" />
      <div className="relative">
        <div className="text-[12px] text-white/80">
          {advance ? 'Mijoz avansi' : 'Mijoz qarzi'}
        </div>
        <CountUp
          value={Math.abs(owes)}
          className="block text-[34px] font-semibold leading-[1.08] tracking-[-0.02em] text-white [font-variant-numeric:tabular-nums]"
        />
        <div className="mt-0.5 text-[12px] text-white/80">so‘m</div>
        <div className="my-[14px] mb-2.5 h-px bg-white/20" />
        <div className="flex gap-4 text-[11px] text-white/[0.88]">
          <span>
            Ishlar <b className="tabular-nums">{fmtNumber(works)}</b>
          </span>
          <span>
            To‘langan <b className="tabular-nums">{fmtNumber(paid)}</b>
          </span>
        </div>
      </div>
    </div>
  )
}

const QUICK: {
  type: 'work' | 'material' | 'expense'
  label: string
  Icon: typeof IconTool
  color: string
}[] = [
  { type: 'work', label: 'Ish', Icon: IconTool, color: 'text-primary' },
  { type: 'material', label: 'Material', Icon: IconPackage, color: 'text-accent' },
  { type: 'expense', label: 'Xarajat', Icon: IconReceipt, color: 'text-danger' },
]

function QuickBar({
  onAdd,
  onPay,
}: {
  onAdd: (t: 'work' | 'material' | 'expense') => void
  onPay: () => void
}) {
  return (
    <div className="mb-4 flex gap-2">
      {QUICK.map(({ type, label, Icon, color }) => (
        <button
          key={type}
          type="button"
          onClick={() => onAdd(type)}
          className="flex-1 rounded-btn border border-border bg-surface px-1 py-2.5 text-center active:scale-[0.97]"
        >
          <Icon size={19} className={`mx-auto ${color}`} />
          <div className="mt-[3px] text-[10px] text-text-muted">{label}</div>
        </button>
      ))}
      <button
        type="button"
        onClick={onPay}
        className="flex-1 rounded-btn border border-border bg-surface px-1 py-2.5 text-center active:scale-[0.97]"
      >
        <IconCash size={19} className="mx-auto text-success" />
        <div className="mt-[3px] text-[10px] text-text-muted">To‘lov</div>
      </button>
    </div>
  )
}

function Recent({ projectId }: { projectId: number }) {
  const navigate = useNavigate()
  const q = useTimeline(projectId)
  const items = (q.data?.pages[0]?.items ?? []).slice(0, 5)

  if (q.isPending) {
    return (
      <div className="space-y-2">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="h-[58px] animate-pulse rounded-[13px] border border-border bg-surface"
          />
        ))}
      </div>
    )
  }
  if (items.length === 0) {
    return (
      <p className="rounded-[13px] border border-border bg-surface px-3 py-4 text-label text-text-faint">
        Hali yozuv yo‘q — yuqoridagi tugmalardan qo‘shing
      </p>
    )
  }

  return (
    <div className="space-y-2">
      {items.map((it) =>
        it.type === 'payment' ? (
          <PaymentCard
            key={`p${it.id}`}
            payment={it}
            onOpen={() => navigate('/history?kind=payment')}
          />
        ) : (
          <RowCard
            key={`e${it.id}`}
            type={it.kind}
            title={it.name}
            sub={
              it.kind !== 'expense'
                ? `${fmtQty(it.quantity, it.unit_label ?? it.unit)} × ${fmtMoney(it.unit_price)}`
                : undefined
            }
            amount={fmtMoney(it.amount)}
            amountStrike={it.is_rework}
            onClick={() => navigate(`/history?kind=${it.kind}`)}
          />
        ),
      )}
    </div>
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
        className="mb-4 flex w-full items-center justify-center gap-1.5 rounded-[13px] border border-border bg-surface py-2.5 text-label text-primary active:scale-[0.99]"
      >
        <IconFileText size={16} /> Hisobot (PDF)
      </button>

      <BottomSheet open={open} onClose={() => setOpen(false)} title="Hisobot (PDF)">
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
            hint="Materiallar, xarajatlar va jami"
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
