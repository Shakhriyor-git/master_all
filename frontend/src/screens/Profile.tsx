import { useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  IconChevronRight,
  IconNotes,
  IconPencil,
  IconTag,
  IconUsers,
} from '@tabler/icons-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { mediaUrl } from '../api/client'
import {
  deleteAvatar,
  patchMe,
  uploadAvatar,
  type Me,
  type MePatch,
  type SocialLink,
} from '../api/me'
import { BottomSheet } from '../components/BottomSheet'
import { Screen } from '../components/Screen'
import { SocialLinks } from '../components/SocialLinks'
import { SplashSkeleton } from '../components/states'
import { useMe } from '../hooks/useMe'
import { getTelegramPhotoUrl, hapticSuccess } from '../lib/telegram'

const INPUT =
  'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

export function Profile() {
  const { data: me, isPending } = useMe()
  const qc = useQueryClient()
  const [avatarOpen, setAvatarOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const saveMe = useMutation({
    mutationFn: (body: MePatch) => patchMe(body),
    onSuccess: (data: Me) => {
      qc.setQueryData(['me'], data)
      hapticSuccess()
    },
  })
  const upload = useMutation({
    mutationFn: (file: File) => uploadAvatar(file),
    onSuccess: (data: Me) => qc.setQueryData(['me'], data),
  })
  const removeAvatar = useMutation({
    mutationFn: () => deleteAvatar(),
    onSuccess: (data: Me) => qc.setQueryData(['me'], data),
  })

  if (isPending || !me) return <SplashSkeleton />

  const tgPhoto = getTelegramPhotoUrl()
  const avatarSrc = me.avatar_url ? mediaUrl(me.avatar_url) : tgPhoto

  const initial = (me.full_name || '?').slice(0, 1).toUpperCase()

  return (
    <Screen title="Profil">
      {/* Gradient sarlavha — kafel naqshi FAQAT shu ekranda */}
      <div className="overflow-hidden rounded-[18px]">
        <div
          className="relative px-4 pb-[18px] pt-[22px] text-center text-on-primary"
          style={{ background: 'var(--grad)' }}
        >
          <svg
            className="pointer-events-none absolute inset-0 h-full w-full"
            aria-hidden="true"
          >
            <defs>
              <pattern
                id="profile-tile"
                width="17"
                height="17"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M17 0 L0 0 L0 17"
                  fill="none"
                  stroke="rgba(255,255,255,0.20)"
                  strokeWidth="0.9"
                />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#profile-tile)" />
          </svg>
          <div className="relative">
            <button
              type="button"
              onClick={() => setAvatarOpen(true)}
              className="mx-auto block h-[84px] w-[84px] rounded-full bg-white/30 p-[3px] active:scale-95"
            >
              <span className="flex h-full w-full items-center justify-center overflow-hidden rounded-full bg-primary-soft text-[30px] font-semibold text-primary">
                {avatarSrc ? (
                  <img
                    src={avatarSrc}
                    alt=""
                    className="h-full w-full object-cover"
                  />
                ) : (
                  initial
                )}
              </span>
            </button>
            <div className="mt-2.5 text-[20px] font-semibold">
              {me.full_name}
            </div>
            <div className="text-[12px] text-white/85">
              {me.phone ?? 'telefon kiritilmagan'}
            </div>
            <button
              type="button"
              onClick={() => setEditOpen(true)}
              className="mt-2.5 inline-flex items-center gap-1.5 rounded-chip bg-white/20 px-[13px] py-[5px] text-[12px] active:scale-95"
            >
              <IconPencil size={13} /> Tahrirlash
            </button>
          </div>
        </div>
        <div className="flex text-on-primary">
          <div
            className="flex-1 py-[11px] text-center"
            style={{ background: 'var(--grad-stat-a)' }}
          >
            <span className="text-[17px] font-semibold">
              {me.active_projects}
            </span>
            <span className="ml-1.5 text-[11px] text-white/80">faol obyekt</span>
          </div>
          <div className="w-px bg-white/25" />
          <div
            className="flex-1 py-[11px] text-center"
            style={{ background: 'var(--grad-stat-b)' }}
          >
            <span className="text-[17px] font-semibold">
              {me.completed_projects}
            </span>
            <span className="ml-1.5 text-[11px] text-white/80">tugatilgan</span>
          </div>
        </div>
      </div>

      <h2 className="mb-1.5 mt-5 text-[11px] uppercase tracking-[0.06em] text-text-faint">
        Mening sahifalarim
      </h2>
      <div className="overflow-hidden rounded-card border border-border bg-surface">
        <SocialLinks
          links={me.social_links}
          onChange={(next: SocialLink[]) =>
            saveMe.mutateAsync({ social_links: next })
          }
        />
      </div>

      <div className="mt-3 overflow-hidden rounded-card border border-border bg-surface">
        <LinkRow
          to="/catalog"
          icon={<IconTag size={18} />}
          tint="bg-primary-soft text-primary"
          label="Xizmatlarim"
          sub={`${me.catalog_items} pozitsiya · ${me.catalog_unpriced} narxsiz`}
        />
        <LinkRow
          to="/notes"
          icon={<IconNotes size={18} />}
          tint="bg-[#FEF0C7] text-[#B45309]"
          label="Qaydlarim"
          sub={`${me.notes_count} ta ro‘yxat`}
        />
        <div className="flex items-center gap-3 px-4 py-3 opacity-50">
          <span className="flex h-[34px] w-[34px] items-center justify-center rounded-[10px] bg-surface-2 text-text-muted">
            <IconUsers size={18} />
          </span>
          <span className="flex-1 text-body text-text">Brigada</span>
          <span className="rounded-chip bg-surface-2 px-2 py-0.5 text-label text-text-muted">
            Tez orada
          </span>
        </div>
      </div>

      <input
        ref={fileRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          e.target.value = ''
          if (file) {
            upload.mutate(file)
            setAvatarOpen(false)
          }
        }}
      />

      <BottomSheet
        open={avatarOpen}
        onClose={() => setAvatarOpen(false)}
        title="Rasm"
      >
        <div className="space-y-2">
          <SheetButton
            onClick={() => {
              removeAvatar.mutate()
              setAvatarOpen(false)
            }}
          >
            Telegram rasmim
          </SheetButton>
          <SheetButton onClick={() => fileRef.current?.click()}>
            Galereyadan yuklash
          </SheetButton>
          {upload.isError && (
            <p className="text-label text-danger">
              Rasmni yuklab bo‘lmadi. Boshqa rasm tanlang.
            </p>
          )}
        </div>
      </BottomSheet>

      <EditSheet
        open={editOpen}
        onClose={() => setEditOpen(false)}
        me={me}
        onSave={(body) =>
          saveMe.mutateAsync(body).then(() => setEditOpen(false))
        }
        saving={saveMe.isPending}
      />
    </Screen>
  )
}

function LinkRow({
  to,
  icon,
  tint,
  label,
  sub,
}: {
  to: string
  icon: ReactNode
  tint: string
  label: string
  sub?: string
}) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 border-b border-border px-4 py-3 last:border-b-0 active:bg-surface-2"
    >
      <span
        className={`flex h-[34px] w-[34px] items-center justify-center rounded-[10px] ${tint}`}
      >
        {icon}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-body text-text">{label}</span>
        {sub && (
          <span className="block text-[11px] text-text-faint">{sub}</span>
        )}
      </span>
      <IconChevronRight size={16} className="text-text-faint" />
    </Link>
  )
}

function SheetButton({
  children,
  onClick,
}: {
  children: ReactNode
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="min-h-[44px] w-full rounded-btn bg-surface-2 text-body text-text active:scale-[0.98]"
    >
      {children}
    </button>
  )
}

function EditSheet({
  open,
  onClose,
  me,
  onSave,
  saving,
}: {
  open: boolean
  onClose: () => void
  me: Me
  onSave: (body: MePatch) => Promise<unknown>
  saving: boolean
}) {
  const [name, setName] = useState(me.full_name)
  const [phone, setPhone] = useState(me.phone ?? '')

  const lastMe = useRef(me)
  if (lastMe.current !== me) {
    lastMe.current = me
    setName(me.full_name)
    setPhone(me.phone ?? '')
  }

  const ready = name.trim().length > 0

  return (
    <BottomSheet open={open} onClose={onClose} title="Profilni tahrirlash">
      <div className="space-y-3">
        <label className="block text-label text-text-muted">
          Ism
          <input
            className={INPUT}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <label className="block text-label text-text-muted">
          Telefon
          <input
            className={INPUT}
            inputMode="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+998…"
          />
        </label>
        <button
          type="button"
          disabled={!ready || saving}
          onClick={() =>
            onSave({
              full_name: name.trim(),
              phone: phone.trim() || undefined,
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
