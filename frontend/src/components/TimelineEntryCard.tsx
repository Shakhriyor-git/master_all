import { IconPhoto } from '@tabler/icons-react'
import { motion } from 'framer-motion'
import { useRef, useState } from 'react'
import type { TimelineEntry } from '../api/timeline'
import { METHOD_ICON, METHOD_LABEL } from '../lib/entryVisual'
import { fmtMoney, fmtQty, fmtTime } from '../lib/format'
import { RowCard, RowChip } from './RowCard'

interface Props {
  entry: TimelineEntry
  onOpen: (e: TimelineEntry) => void
  onDelete: (e: TimelineEntry) => void
}

/** Tarix lentasidagi yozuv kartasi — swipe bilan o'chirish + RowCard ko'rinishi. */
export function TimelineEntryCard({ entry, onOpen, onDelete }: Props) {
  const MethodIcon = entry.payment_method
    ? METHOD_ICON[entry.payment_method]
    : null
  const startX = useRef(0)
  const [dx, setDx] = useState(0)

  const chips = (
    <>
      {entry.is_rework && (
        <RowChip className="bg-danger-soft text-danger">⚠️ Brak</RowChip>
      )}
      {MethodIcon && entry.payment_method && (
        <RowChip>
          <MethodIcon size={12} />
          {METHOD_LABEL[entry.payment_method]}
        </RowChip>
      )}
      {entry.has_receipt && (
        <IconPhoto size={14} className="text-text-faint" />
      )}
    </>
  )

  return (
    <div className="relative overflow-hidden rounded-[13px]">
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
        className="relative block w-full text-left"
      >
        <RowCard
          type={entry.kind}
          title={entry.name}
          sub={
            entry.kind !== 'expense'
              ? `${fmtQty(entry.quantity, entry.unit_label ?? entry.unit)} × ${fmtMoney(entry.unit_price)}`
              : undefined
          }
          chips={chips}
          amount={fmtMoney(entry.amount)}
          amountStrike={entry.is_rework}
          time={fmtTime(entry.created_at)}
        />
      </motion.button>
    </div>
  )
}
