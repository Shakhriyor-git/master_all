import { useCallback, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { IconChevronRight, IconPlus } from '@tabler/icons-react'
import type { PartnerListItem } from '../api/partners'
import { BottomSheet } from '../components/BottomSheet'
import { EmptyState, Screen } from '../components/Screen'
import { SplashSkeleton } from '../components/states'
import { useBackButton } from '../hooks/useBackButton'
import { usePartnerMutations, usePartners } from '../hooks/usePartners'
import { fmtDateGroup, fmtMoney, fmtPhone } from '../lib/format'
import { hapticSuccess } from '../lib/telegram'

const INPUT =
  'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

/**
 * Brigada — ustaning shaxsiy daftari: sheriklarga qancha berdim.
 * Obyektga bog'lanmaydi, hisobot/PDF ga kirmaydi. Qarz emas — tarix.
 */
export function Partners() {
  const navigate = useNavigate()
  const [newOpen, setNewOpen] = useState(false)
  const list = usePartners()
  const { createPartner } = usePartnerMutations()

  const back = useCallback(() => navigate(-1), [navigate])
  useBackButton(back)

  if (list.isPending) return <SplashSkeleton />

  const partners = list.data?.partners ?? []
  const addButton = (
    <button
      type="button"
      onClick={() => setNewOpen(true)}
      className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-card border border-dashed border-border py-3 text-label text-primary active:bg-surface-2"
    >
      <IconPlus size={16} /> Sherik qo‘shish
    </button>
  )

  return (
    <Screen title="Brigada">
      {partners.length === 0 ? (
        <EmptyState
          text="Sheriklaringiz yo‘q. Yordamchilarga bergan pullaringizni yozib boring."
          action={addButton}
        />
      ) : (
        <>
          <div className="mb-3 border-b border-border pb-3">
            <div className="text-label text-text-muted">Jami berilgan</div>
            <div className="text-title text-text">
              {fmtMoney(list.data?.grand_total)}
            </div>
          </div>
          <div className="space-y-2">
            {partners.map((p) => (
              <PartnerCard
                key={p.id}
                partner={p}
                onOpen={() => navigate(`/partners/${p.id}`)}
              />
            ))}
          </div>
          {addButton}
        </>
      )}

      <PartnerFormSheet
        open={newOpen}
        onClose={() => setNewOpen(false)}
        title="Sherik qo‘shish"
        pending={createPartner.isPending}
        onSave={async (body) => {
          const created = await createPartner.mutateAsync(body)
          hapticSuccess()
          setNewOpen(false)
          navigate(`/partners/${created.id}`)
        }}
      />
    </Screen>
  )
}

function PartnerCard({
  partner,
  onOpen,
}: {
  partner: PartnerListItem
  onOpen: () => void
}) {
  const initial = (partner.name || '?').slice(0, 1).toUpperCase()
  return (
    <button
      type="button"
      onClick={onOpen}
      className="flex w-full items-center gap-3 rounded-card border border-border bg-surface p-3 text-left active:scale-[0.99]"
    >
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-2 text-body font-semibold text-text-muted">
        {initial}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-body text-text">
          {partner.name}
        </span>
        {partner.phone && (
          <span className="block text-label text-text-muted">
            {fmtPhone(partner.phone)}
          </span>
        )}
        <span className="block text-label text-text-faint">
          {partner.last_payment_at
            ? `Oxirgi: ${fmtDateGroup(partner.last_payment_at)}`
            : 'To‘lov yo‘q'}
        </span>
      </span>
      <span className="shrink-0 text-body text-text">
        {fmtMoney(partner.total_paid)}
      </span>
      <IconChevronRight size={16} className="shrink-0 text-text-faint" />
    </button>
  )
}

// ---------------------------------------------------------------------------
// Sherik qo'shish / tahrirlash varag'i (ikkala ekranda ishlatiladi)
// ---------------------------------------------------------------------------
export interface PartnerFormValues {
  name: string
  phone?: string | null
  note?: string | null
}

export function PartnerFormSheet({
  open,
  onClose,
  title,
  initial,
  pending,
  onSave,
}: {
  open: boolean
  onClose: () => void
  title: string
  initial?: PartnerFormValues
  pending: boolean
  onSave: (body: PartnerFormValues) => Promise<void>
}) {
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [note, setNote] = useState('')

  const wasOpen = useRef(false)
  if (open && !wasOpen.current) {
    wasOpen.current = true
    setName(initial?.name ?? '')
    setPhone(initial?.phone ?? '')
    setNote(initial?.note ?? '')
  }
  if (!open && wasOpen.current) wasOpen.current = false

  const ready = name.trim().length > 0

  return (
    <BottomSheet open={open} onClose={onClose} title={title}>
      <div className="space-y-3">
        <label className="block text-label text-text-muted">
          Ismi
          <input
            className={INPUT}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="masalan: Otabek"
            maxLength={100}
            autoFocus
          />
        </label>
        <label className="block text-label text-text-muted">
          Telefon (ixtiyoriy)
          <input
            className={INPUT}
            inputMode="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+998…"
            maxLength={20}
          />
        </label>
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
              name: name.trim(),
              phone: phone.trim() || null,
              note: note.trim() || null,
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
