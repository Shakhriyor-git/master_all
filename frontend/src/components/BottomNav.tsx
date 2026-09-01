import {
  IconHistory,
  IconHistoryToggle,
  IconHome,
  IconHomeFilled,
  IconPlus,
  IconSettings,
  IconSettingsFilled,
  IconUser,
  IconUserFilled,
  type Icon,
} from '@tabler/icons-react'
import { NavLink, useNavigate } from 'react-router-dom'
import { hapticSuccess } from '../lib/telegram'

interface TabDef {
  to: string
  label: string
  Icon: Icon
  IconActive: Icon
}

const TABS: TabDef[] = [
  { to: '/', label: 'Asosiy', Icon: IconHome, IconActive: IconHomeFilled },
  {
    to: '/history',
    label: 'Tarix',
    Icon: IconHistoryToggle,
    IconActive: IconHistory,
  },
  { to: '/profile', label: 'Profil', Icon: IconUser, IconActive: IconUserFilled },
  {
    to: '/settings',
    label: 'Sozlamalar',
    Icon: IconSettings,
    IconActive: IconSettingsFilled,
  },
]

// Ikonka o'lchami HAR DOIM bir xil — faqat rang o'zgaradi. Hech qanday
// scale / translate / spring animatsiya yo'q (panel sakramasligi uchun).
const ICON_SIZE = 23

export function BottomNav() {
  const navigate = useNavigate()

  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-border bg-surface pb-[env(safe-area-inset-bottom)]">
      <div className="mx-auto flex h-[62px] max-w-md items-end justify-around px-1">
        {TABS.slice(0, 2).map((t) => (
          <Tab key={t.to} {...t} />
        ))}

        <button
          type="button"
          aria-label="Tez qo‘shish"
          onClick={() => {
            hapticSuccess()
            navigate('/add')
          }}
          className="mx-1 flex h-[52px] w-[52px] flex-none -translate-y-[14px] items-center justify-center rounded-full bg-primary text-on-primary shadow-[0_4px_14px_var(--fab-glow)] transition-transform duration-100 active:scale-[0.94]"
        >
          <IconPlus size={26} />
        </button>

        {TABS.slice(2).map((t) => (
          <Tab key={t.to} {...t} />
        ))}
      </div>
    </nav>
  )
}

function Tab({ to, label, Icon, IconActive }: TabDef) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className="flex flex-1 flex-col items-center gap-0.5 pb-[9px] pt-1"
    >
      {({ isActive }) => (
        <span
          className={`flex flex-col items-center gap-0.5 transition-colors duration-150 ${
            isActive ? 'text-primary' : 'text-text-faint'
          }`}
        >
          {isActive ? (
            <IconActive size={ICON_SIZE} />
          ) : (
            <Icon size={ICON_SIZE} />
          )}
          <span className="text-[10px] font-medium leading-none">{label}</span>
        </span>
      )}
    </NavLink>
  )
}
