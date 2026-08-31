import { useState } from 'react'
import type { Me } from '../api/me'
import { useUpdateMe } from '../hooks/useMe'
import { hapticSuccess } from '../lib/telegram'

const INPUT =
  'w-full rounded-btn border border-border bg-surface-2 px-3 py-2.5 text-body text-text outline-none focus:border-primary'

/** +998 dan keyingi 9 raqam. */
function digitsFromPhone(phone: string | null): string {
  const d = (phone ?? '').replace(/\D/g, '')
  return d.startsWith('998') ? d.slice(3, 12) : d.slice(0, 9)
}

export function Onboarding({ me }: { me: Me }) {
  const update = useUpdateMe()
  const [name, setName] = useState(me.full_name ?? '')
  const [digits, setDigits] = useState(digitsFromPhone(me.phone))

  const phoneOk = digits.length === 9
  const nameOk = name.trim().length > 0
  const ready = phoneOk && nameOk && !update.isPending

  async function submit() {
    if (!ready) return
    await update.mutateAsync({
      full_name: name.trim(),
      phone: `+998${digits}`,
      onboarded: true,
    })
    hapticSuccess()
  }

  return (
    <div className="mx-auto flex min-h-full max-w-md flex-col justify-center bg-bg px-6 py-10">
      <h1 className="text-title text-text">Xush kelibsiz!</h1>
      <p className="mt-1 text-label text-text-muted">
        Bu ma’lumotlar hisobotlarda va PDF da ko‘rsatiladi.
      </p>

      <div className="mt-6 space-y-4">
        <label className="block text-label text-text-muted">
          Ismingiz
          <input
            className={`${INPUT} mt-1`}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ism"
          />
        </label>

        <label className="block text-label text-text-muted">
          Telefon
          <div
            className={`mt-1 flex items-center gap-2 rounded-btn border border-border bg-surface-2 px-3 ${''}`}
          >
            <span className="text-body text-text-muted">+998</span>
            <input
              className="min-w-0 flex-1 bg-transparent py-2.5 text-body text-text outline-none"
              inputMode="numeric"
              value={digits}
              onChange={(e) =>
                setDigits(e.target.value.replace(/\D/g, '').slice(0, 9))
              }
              placeholder="90 123 45 67"
            />
          </div>
          {digits.length > 0 && !phoneOk && (
            <span className="mt-1 block text-label text-danger">
              Telefon 9 raqamdan iborat bo‘lishi kerak
            </span>
          )}
        </label>
      </div>

      <button
        type="button"
        disabled={!ready}
        onClick={submit}
        className="mt-8 min-h-[48px] w-full rounded-btn bg-primary text-body text-on-primary active:scale-[0.98] disabled:opacity-50"
      >
        Davom etish
      </button>

      {update.isError && (
        <p className="mt-2 text-center text-label text-danger">
          Saqlab bo‘lmadi, qayta urinib ko‘ring.
        </p>
      )}
    </div>
  )
}
