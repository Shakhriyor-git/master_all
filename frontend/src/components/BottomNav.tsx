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

export function BottomNav() {
  const navigate = useNavigate()

  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-border bg-surface">
      <div className="mx-auto grid max-w-md grid-cols-5 items-end px-2 pb-[env(safe-area-inset-bottom)] pt-1.5">
        {TABS.slice(0, 2).map((t) => (
          <Tab key={t.to} {...t} />
        ))}

        <div className="flex justify-center">
          <button
            type="button"
            aria-label="Tez qo‘shish"
            onClick={() => {
              hapticSuccess()
              navigate('/add')
            }}
            className="-mt-6 flex h-14 w-14 min-h-[44px] min-w-[44px] items-center justify-center rounded-full bg-primary text-on-primary shadow-md active:scale-95"
          >
            <IconPlus size={26} />
          </button>
        </div>

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
      className="flex min-h-[44px] flex-col items-center gap-0.5 py-1"
    >
      {({ isActive }) => (
        <span
          className={
            isActive
              ? 'flex flex-col items-center gap-0.5 text-primary'
              : 'flex flex-col items-center gap-0.5 text-text-faint'
          }
        >
          {isActive ? <IconActive size={24} /> : <Icon size={23} />}
          <span className="text-label">{label}</span>
        </span>
      )}
    </NavLink>
  )
}
