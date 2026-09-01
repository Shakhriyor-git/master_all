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
import { motion } from 'framer-motion'
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

// Ikonka o'lchami HAR DOIM bir xil — faqat rang/to'ldirilish o'zgaradi.
const ICON_SIZE = 24
const SPRING = { type: 'spring', stiffness: 300, damping: 30 } as const

export function BottomNav() {
  const navigate = useNavigate()

  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-border bg-surface">
      <div className="mx-auto grid max-w-md grid-cols-5 px-2 pb-[env(safe-area-inset-bottom)]">
        {TABS.slice(0, 2).map((t) => (
          <Tab key={t.to} {...t} />
        ))}

        <div className="flex h-14 items-center justify-center">
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
      // Balandlik QAT'IY — panel hech qachon sakramaydi
      className="relative flex h-14 min-h-[44px] flex-col items-center justify-center gap-0.5"
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <motion.span
              layoutId="nav-indicator"
              transition={SPRING}
              className="absolute top-0 h-0.5 w-7 rounded-full bg-primary"
            />
          )}
          <span
            className={`transition-colors duration-150 ${
              isActive ? 'text-primary' : 'text-text-faint'
            }`}
          >
            {isActive ? (
              <IconActive size={ICON_SIZE} />
            ) : (
              <Icon size={ICON_SIZE} />
            )}
          </span>
          <span
            className={`text-label leading-none transition-colors duration-150 ${
              isActive ? 'text-primary' : 'text-text-faint'
            }`}
          >
            {label}
          </span>
        </>
      )}
    </NavLink>
  )
}
