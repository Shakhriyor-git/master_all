import type { TimelinePayment } from '../api/timeline'
import { METHOD_ICON, METHOD_LABEL, PURPOSE_LABEL } from '../lib/entryVisual'
import { fmtMoney, fmtTime } from '../lib/format'
import { RowCard, RowChip } from './RowCard'

interface Props {
  payment: TimelinePayment
  onOpen: (p: TimelinePayment) => void
}

/** Mijoz to'lovi kartasi — och yashil fon, ikkita chip (maqsad + usul). */
export function PaymentCard({ payment, onOpen }: Props) {
  const MethodIcon = METHOD_ICON[payment.method]
  return (
    <RowCard
      type="payment"
      title="Mijoz to‘lovi"
      chips={
        <>
          <RowChip className="bg-success-soft text-success">
            {PURPOSE_LABEL[payment.purpose]}
          </RowChip>
          <RowChip>
            <MethodIcon size={12} />
            {METHOD_LABEL[payment.method]}
          </RowChip>
        </>
      }
      amount={`+ ${fmtMoney(payment.amount)}`}
      time={fmtTime(payment.created_at)}
      onClick={() => onOpen(payment)}
    />
  )
}
