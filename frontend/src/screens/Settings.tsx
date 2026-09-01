import type { ReactNode } from 'react'
import { Screen } from '../components/Screen'
import { Segment } from '../components/Segment'
import { useTheme } from '../theme/themeContext'
import type { ThemePref } from '../api/me'

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
        <p className="mt-1 text-label text-text-faint">
          Rus tili keyin qo‘shiladi.
        </p>
      </Row>

      <p className="mt-6 text-center text-label text-text-faint">
        Versiya {APP_VERSION}
      </p>
    </Screen>
  )
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="mt-3 rounded-card border border-border bg-surface p-4">
      <div className="mb-2 text-label text-text-muted">{label}</div>
      {children}
    </div>
  )
}
