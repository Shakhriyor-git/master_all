import { IconCashBanknote } from '@tabler/icons-react'
import type { ReactNode } from 'react'
import type { TimelinePayment } from '../api/timeline'
import { METHOD_ICON, METHOD_LABEL, PURPOSE_LABEL } from '../lib/entryVisual'
import { fmtMoney, fmtTime } from '../lib/format'

interface Props {
  payment: TimelinePayment
  onOpen: (p: TimelinePayment) => void
}

/** To'lov kartasi — yozuv kartasidan vizual farq qiladi: yashil, `+`. */
export function PaymentCard({ payment, onOpen }: Props) {
  const MethodIcon = METHOD_ICON[payment.method]
  return (
    <button
      type="button"
      onClick={() => onOpen(payment)}
      className="block w-full rounded-card border border-border bg-success-soft p-3 text-left active:scale-[0.985]"
    >
      <div className="flex items-start gap-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-btn bg-success-soft text-success">
          <IconCashBanknote size={18} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline justify-between gap-2">
            <span className="truncate text-body text-text">
              Mijoz to‘lovi
            </span>
            <span className="shrink-0 text-body text-success">
              + {fmtMoney(payment.amount)}
            </span>
          </div>
          {payment.note && (
            <div className="truncate text-label text-text-muted">
              {payment.note}
            </div>
          )}
        </div>
      </div>

      <div className="mt-2 flex items-center gap-1.5 border-t border-border pt-2">
        <Chip className="bg-surface-2 text-text-muted">
          {PURPOSE_LABEL[payment.purpose]}
        </Chip>
        <Chip className="bg-surface-2 text-text-muted">
          <MethodIcon size={12} />
          {METHOD_LABEL[payment.method]}
        </Chip>
        <span className="ml-auto text-label text-text-faint">
          {fmtTime(payment.created_at)}
        </span>
      </div>
    </button>
  )
}

function Chip({
  children,
  className,
}: {
  children: ReactNode
  className: string
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-chip px-2 py-0.5 text-label ${className}`}
    >
      {children}
    </span>
  )
}
