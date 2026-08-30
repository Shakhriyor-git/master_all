import { IconPhoto } from '@tabler/icons-react'
import { motion } from 'framer-motion'
import { useRef, useState } from 'react'
import type { ReactNode } from 'react'
import type { TimelineEntry } from '../api/timeline'
import {
  KIND_AMOUNT,
  KIND_ICON,
  KIND_ICON_BG,
  METHOD_ICON,
  METHOD_LABEL,
} from '../lib/entryVisual'
import { fmtMoney, fmtQty, fmtTime } from '../lib/format'

interface Props {
  entry: TimelineEntry
  onOpen: (e: TimelineEntry) => void
  onDelete: (e: TimelineEntry) => void
}

/** Tarix lentasidagi yozuv kartasi — EntryCard bilan bir xil ko'rinish. */
export function TimelineEntryCard({ entry, onOpen, onDelete }: Props) {
  const Icon = KIND_ICON[entry.kind]
  const MethodIcon = entry.payment_method
    ? METHOD_ICON[entry.payment_method]
    : null
  const startX = useRef(0)
  const [dx, setDx] = useState(0)

  return (
    <div className="relative overflow-hidden rounded-card">
      <div className="absolute inset-y-0 right-0 flex items-center bg-danger-soft px-5 text-label text-danger">
        O‘chirish
      </div>
      <motion.button
        type="button"
        onClick={() => onOpen(entry)}
        onPointerDown={(e) => {
          startX.current = e.clientX
        }}
        onPointerMove={(e) => {
          if (!startX.current) return
          const d = Math.min(0, e.clientX - startX.current)
          setDx(Math.max(d, -96))
        }}
        onPointerUp={() => {
          if (dx < -64) onDelete(entry)
          setDx(0)
          startX.current = 0
        }}
        onPointerCancel={() => {
          setDx(0)
          startX.current = 0
        }}
        animate={{ x: dx }}
        transition={{ type: 'tween', duration: 0.12 }}
        whileTap={{ scale: 0.985 }}
        className="relative block w-full border border-border bg-surface p-3 text-left"
      >
        <div className="flex items-start gap-3">
          <span
            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-btn ${KIND_ICON_BG[entry.kind]}`}
          >
            <Icon size={18} />
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex items-baseline justify-between gap-2">
              <span className="truncate text-body text-text">{entry.name}</span>
              <span
                className={`shrink-0 text-body ${KIND_AMOUNT[entry.kind]} ${
                  entry.is_rework ? 'line-through opacity-60' : ''
                }`}
              >
                {fmtMoney(entry.amount)}
              </span>
            </div>
            {entry.kind !== 'expense' && (
              <div className="text-label text-text-muted">
                {fmtQty(entry.quantity, entry.unit_label ?? entry.unit)} ×{' '}
                {fmtMoney(entry.unit_price)}
              </div>
            )}
          </div>
        </div>

        <div className="mt-2 flex items-center gap-1.5 border-t border-border pt-2">
          {entry.is_rework && (
            <Chip className="bg-danger-soft text-danger">⚠️ Brak</Chip>
          )}
          {entry.kind !== 'work' && (
            <Chip
              className={
                entry.paid_by === 'client'
                  ? 'bg-success-soft text-success'
                  : 'bg-surface-2 text-text-muted'
              }
            >
              {entry.paid_by === 'client' ? 'Mijoz to‘ladi' : 'Usta to‘ladi'}
            </Chip>
          )}
          {MethodIcon && entry.payment_method && (
            <Chip className="bg-surface-2 text-text-muted">
              <MethodIcon size={12} />
              {METHOD_LABEL[entry.payment_method]}
            </Chip>
          )}
          {entry.has_receipt && (
            <IconPhoto size={14} className="text-text-faint" />
          )}
          <span className="ml-auto text-label text-text-faint">
            {fmtTime(entry.created_at)}
          </span>
        </div>
      </motion.button>
    </div>
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
