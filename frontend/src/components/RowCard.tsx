import type { ReactNode } from 'react'
import {
  ROW_AMOUNT,
  ROW_EDGE,
  ROW_ICON,
  ROW_ICON_BG,
  type RowType,
} from '../lib/entryVisual'

interface Props {
  type: RowType
  title: string
  /** ikkinchi qator — `5 m² × 25 000` yoki `DOM STROY · kecha` */
  sub?: ReactNode
  /** sub ostidagi chiplar qatori */
  chips?: ReactNode
  /** formatlangan summa (kerak bo'lsa `+` ni chaqiruvchi qo'shadi) */
  amount: string
  amountStrike?: boolean
  /** o'ng pastda, 10px */
  time?: string
  right?: ReactNode
  onClick?: () => void
}

/** Yagona yozuv/to'lov kartasi — maket 2/3-bo'lim. Bir qator:
 *  [ikonka] [nom / sub / chiplar] [summa / vaqt]. Chegara turi bo'yicha. */
export function RowCard({
  type,
  title,
  sub,
  chips,
  amount,
  amountStrike,
  time,
  right,
  onClick,
}: Props) {
  const Icon = ROW_ICON[type]
  const Tag = onClick ? 'button' : 'div'
  return (
    <Tag
      {...(onClick ? { type: 'button' as const, onClick } : {})}
      className={`flex w-full items-center gap-2.5 rounded-[13px] border p-3 text-left ${ROW_EDGE[type]} ${
        onClick ? 'active:scale-[0.985]' : ''
      }`}
    >
      <span
        className={`flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-btn ${ROW_ICON_BG[type]}`}
      >
        <Icon size={15} />
      </span>
      <div className="min-w-0 flex-1">
        <div className="truncate text-[13px] font-medium text-text">{title}</div>
        {sub && <div className="text-[11px] text-text-faint">{sub}</div>}
        {chips && <div className="mt-1 flex flex-wrap gap-1.5">{chips}</div>}
      </div>
      {right ?? (
        <div className="shrink-0 text-right">
          <div
            className={`text-[14px] font-medium tabular-nums ${ROW_AMOUNT[type]} ${
              amountStrike ? 'line-through opacity-60' : ''
            }`}
          >
            {amount}
          </div>
          {time && (
            <div className="text-[10px] text-text-faint">{time}</div>
          )}
        </div>
      )}
    </Tag>
  )
}

export function RowChip({
  children,
  className = 'bg-surface-2 text-text-muted',
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-chip px-2 py-0.5 text-[11px] ${className}`}
    >
      {children}
    </span>
  )
}
