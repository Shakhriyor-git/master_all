import { useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  IconChevronRight,
  IconNote,
  IconTool,
  IconUsersGroup,
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

  return (
    <Screen title="Profil">
      {/* Gradient sarlavha */}
      <div
        style={{ background: 'var(--grad)' }}
        className="flex flex-col items-center rounded-card px-4 pb-5 pt-6 text-on-primary"
      >
        <button
          type="button"
          onClick={() => setAvatarOpen(true)}
          className="rounded-full bg-white/20 p-1 active:scale-95"
        >
          <span className="flex h-[88px] w-[88px] items-center justify-center overflow-hidden rounded-full bg-primary-soft text-title text-primary">
            {avatarSrc ? (
              <img
                src={avatarSrc}
                alt=""
                className="h-full w-full object-cover"
              />
            ) : (
              (me.full_name || '?').slice(0, 1).toUpperCase()
            )}
          </span>
        </button>
        <div className="mt-2 text-title">{me.full_name}</div>
        <div className="text-label opacity-90">
          {me.phone ?? 'telefon kiritilmagan'}
        </div>
        <button
          type="button"
          onClick={() => setEditOpen(true)}
          className="mt-1 rounded-chip bg-white/15 px-3 py-0.5 text-label active:scale-95"
        >
          Tahrirlash
        </button>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3">
        <Metric label="Faol" value={me.active_projects} />
        <Metric label="Tugadi" value={me.completed_projects} />
      </div>

      <h2 className="mb-1.5 mt-5 text-label uppercase text-text-muted">
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
        <LinkRow to="/catalog" icon={<IconTool size={20} />} label="Xizmatlarim" />
        <LinkRow to="/notes" icon={<IconNote size={20} />} label="Qaydlarim" />
        <div className="flex items-center gap-3 px-4 py-3 opacity-60">
          <span className="text-text-muted">
            <IconUsersGroup size={20} />
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

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-card border border-border bg-surface p-4 text-center">
      <div className="text-title text-text">{value}</div>
      <div className="text-label text-text-muted">{label}</div>
    </div>
  )
}

function LinkRow({
  to,
  icon,
  label,
}: {
  to: string
  icon: ReactNode
  label: string
}) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 border-b border-border px-4 py-3 last:border-b-0 active:bg-surface-2"
    >
      <span className="text-primary">{icon}</span>
      <span className="flex-1 text-body text-text">{label}</span>
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
