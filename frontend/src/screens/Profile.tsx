import { mediaUrl } from '../api/client'
import { Screen } from '../components/Screen'
import { useMe } from '../hooks/useMe'

export function Profile() {
  const { data: me } = useMe()

  return (
    <Screen title="Profil">
      <div className="flex items-center gap-3 rounded-card border border-border bg-surface p-4">
        <div className="flex h-14 w-14 items-center justify-center overflow-hidden rounded-full bg-primary-soft text-title text-primary">
          {me?.avatar_url ? (
            <img
              src={mediaUrl(me.avatar_url) ?? undefined}
              alt=""
              className="h-full w-full object-cover"
            />
          ) : (
            (me?.full_name ?? '?').slice(0, 1)
          )}
        </div>
        <div>
          <div className="text-body text-text">{me?.full_name}</div>
          <div className="text-label text-text-muted">
            {me?.phone ?? 'telefon kiritilmagan'}
          </div>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3">
        <Metric label="Faol obyektlar" value={me?.active_projects ?? 0} />
        <Metric label="Tugatilgan" value={me?.completed_projects ?? 0} />
      </div>

      <p className="mt-4 text-label text-text-faint">
        To‘liq profil (avatar, Xizmatlarim, Qaydlar) C bosqichida.
      </p>
    </Screen>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-card border border-border bg-surface p-4">
      <div className="text-title text-text">{value}</div>
      <div className="text-label text-text-muted">{label}</div>
    </div>
  )
}
