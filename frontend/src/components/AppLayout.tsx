import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import { MusicProvider } from '../music/MusicProvider'
import { BottomNav } from './BottomNav'

/**
 * App shell — sahifaning O'ZI hech qachon scroll qilinmaydi (index.css da
 * `overflow:hidden`). Faqat `main` scroll bo'ladi. Balandlik `--tg-vh`
 * (haqiqiy viewport), shuning uchun Telegram sarlavhasi yig'ilsa yoki tab
 * almashsa ham navbar bir piksel qimirlamaydi.
 */
export function AppLayout({ children }: { children: ReactNode }) {
  const mainRef = useRef<HTMLDivElement>(null)
  const { pathname } = useLocation()

  useEffect(() => {
    // Tab almashganda scroll boshiga — animatsiyasiz (silliq scroll sakrashni kuchaytiradi)
    mainRef.current?.scrollTo({ top: 0, behavior: 'auto' })
  }, [pathname])

  return (
    <MusicProvider>
      <div
        className="mx-auto flex max-w-md flex-col overflow-hidden bg-bg"
        style={{ height: 'var(--tg-vh)' }}
      >
        <main
          ref={mainRef}
          className="flex-1 overflow-y-auto overscroll-contain pb-4"
        >
          {children}
        </main>
        <BottomNav />
      </div>
    </MusicProvider>
  )
}
