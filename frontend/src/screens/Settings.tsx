import { useState } from 'react'
import type { ReactNode } from 'react'
import { Screen } from '../components/Screen'
import { Segment } from '../components/Segment'
import { MoneyInput } from '../components/MoneyInput'
import { QuantityInput } from '../components/QuantityInput'
import { useTheme } from '../theme/themeContext'
import type { ThemePref } from '../api/me'
import {
  fmtDate,
  fmtDateGroup,
  fmtMoney,
  fmtQty,
} from '../lib/format'

const THEME_OPTIONS: { value: ThemePref; label: string }[] = [
  { value: 'light', label: 'Kunduzgi' },
  { value: 'dark', label: 'Tungi' },
  { value: 'auto', label: 'Avtomatik' },
]

const APP_VERSION = '0.1.0'

export function Settings() {
  const { pref, setPref } = useTheme()

  return (
    <Screen title="Sozlamalar">
      <Row label="Mavzu">
        <Segment options={THEME_OPTIONS} value={pref} onChange={setPref} />
      </Row>

      <Row label="Til">
        <Segment
          options={[{ value: 'uz', label: "O'zbekcha" }]}
          value="uz"
          onChange={() => {}}
        />
        <p className="mt-1 text-label text-text-faint">Rus tili keyin qo‘shiladi.</p>
      </Row>

      <Row label="Bildirishnomalar">
        <Toggle />
      </Row>

      <DebugSection />

      <p className="mt-6 text-center text-label text-text-faint">
        Versiya {APP_VERSION}
      </p>
    </Screen>
  )
}

function Row({
  label,
  children,
}: {
  label: string
  children: ReactNode
}) {
  return (
    <div className="mt-3 rounded-card border border-border bg-surface p-4">
      <div className="mb-2 text-label text-text-muted">{label}</div>
      {children}
    </div>
  )
}

function Toggle() {
  const [on, setOn] = useState(true)
  return (
    <button
      type="button"
      onClick={() => setOn((v) => !v)}
      className={
        on
          ? 'h-7 w-12 rounded-chip bg-primary p-1 transition-colors'
          : 'h-7 w-12 rounded-chip bg-surface-2 p-1 transition-colors'
      }
      aria-pressed={on}
    >
      <span
        className={
          on
            ? 'block h-5 w-5 translate-x-5 rounded-full bg-on-primary transition-transform'
            : 'block h-5 w-5 rounded-full bg-text-faint transition-transform'
        }
      />
    </button>
  )
}

function DebugSection() {
  const [money, setMoney] = useState<number | null>(null)
  const [qty, setQty] = useState<number | null>(null)
  const now = new Date()
  const yesterday = new Date(Date.now() - 86_400_000)
  const older = new Date('2026-08-12T09:15:00')

  const inputClass =
    'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

  return (
    <div className="mt-4 rounded-card border border-dashed border-border bg-surface p-4">
      <div className="mb-3 text-label text-text-muted">DEBUG — komponentlar</div>

      <label className="text-label text-text-muted">MoneyInput</label>
      <MoneyInput
        value={money}
        onChange={setMoney}
        placeholder="0"
        className={inputClass}
        aria-label="pul debug"
      />
      <div className="mt-1 text-label text-text-faint">
        toza son: {money ?? 'null'} · {fmtMoney(money ?? 0)}
      </div>

      <label className="mt-3 block text-label text-text-muted">
        QuantityInput
      </label>
      <QuantityInput
        value={qty}
        onChange={setQty}
        placeholder="0"
        className={inputClass}
        aria-label="miqdor debug"
      />
      <div className="mt-1 text-label text-text-faint">
        toza son: {qty ?? 'null'} · {fmtQty(qty ?? 0, 'm²')}
      </div>

      <div className="mt-3 space-y-1 text-label text-text-faint">
        <div>fmtMoney(1250000) = {fmtMoney(1250000)}</div>
        <div>fmtQty(11.5, "m²") = {fmtQty(11.5, 'm²')}</div>
        <div>fmtDate(bugun) = {fmtDate(now)}</div>
        <div>fmtDateGroup(bugun) = {fmtDateGroup(now)}</div>
        <div>fmtDateGroup(kecha) = {fmtDateGroup(yesterday)}</div>
        <div>fmtDateGroup(12-avg) = {fmtDateGroup(older)}</div>
      </div>
    </div>
  )
}
