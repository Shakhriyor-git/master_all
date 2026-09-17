import WebApp from '@twa-dev/sdk'

export type Scheme = 'light' | 'dark'

const THEME_BG: Record<Scheme, `#${string}`> = {
  light: '#f5f6f8',
  dark: '#0b0b10',
}

/** Telegram ichida ochilgan-ochilmaganini bildiradi. */
export function getInitData(): string {
  try {
    return WebApp.initData ?? ''
  } catch {
    return ''
  }
}

/** initData imzosiz — faqat ko'rinish uchun (rasm), ishonchli emas. */
export function getTelegramPhotoUrl(): string | null {
  try {
    return WebApp.initDataUnsafe?.user?.photo_url ?? null
  } catch {
    return null
  }
}

export function initTelegram(): void {
  try {
    WebApp.ready()
    WebApp.expand()
  } catch {
    /* Telegram tashqarisida — e'tibor bermaymiz */
  }
  syncViewport()
}

/**
 * `--tg-vh` — haqiqiy ko'rinadigan balandlik. App shell (AppLayout) shu
 * o'zgaruvchini `height` sifatida ishlatadi, shuning uchun `100vh` yoki
 * Telegram sarlavhasi yig'ilishi navbar'ni siljitmaydi.
 *
 * `viewportStableHeight` — klaviatura ochilganda O'ZGARMAYDI (viewportHeight'dan farqi).
 *
 * Ikki marta rAF: `viewportChanged` Telegram animatsiyasi paytida keladi va
 * `viewportStableHeight` hali eski qiymatda bo'ladi. Ikki kadr kutsak
 * Telegram qiymatni yangilashga ulguradi.
 */
function readStableHeight(): number {
  try {
    return WebApp.viewportStableHeight || 0
  } catch {
    return 0
  }
}

// Ekran shunchalik kichik bo'lmaydi — bu animatsiya oralig'idagi xato qiymat
const MIN_VH = 200

export function syncViewport(): void {
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      let h = readStableHeight()
      if (!h && typeof window !== 'undefined') h = window.innerHeight
      if (h < MIN_VH) return
      document.documentElement.style.setProperty('--tg-vh', `${h}px`)
    })
  })
}

function currentVh(): number {
  return parseInt(
    document.documentElement.style.getPropertyValue('--tg-vh'),
    10,
  )
}

let _viewportBound = false
export function bindViewportSync(): void {
  if (_viewportBound) return
  _viewportBound = true
  syncViewport()
  try {
    // isStateStable=false — animatsiya davom etyapti, oraliq qiymatni olmaymiz
    WebApp.onEvent('viewportChanged', (e) => {
      if (e && e.isStateStable === false) return
      syncViewport()
    })
  } catch {
    /* noop */
  }
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', syncViewport)
    // Safety net: Telegram hodisa yubormay qolsa ham 500ms ichida tuzatiladi
    window.setInterval(() => {
      const h = readStableHeight()
      const cur = currentVh()
      if (h >= MIN_VH && (Number.isNaN(cur) || Math.abs(h - cur) > 4)) {
        syncViewport()
      }
    }, 500)
  }
}

export function getColorScheme(): Scheme {
  try {
    return WebApp.colorScheme === 'dark' ? 'dark' : 'light'
  } catch {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
    }
    return 'light'
  }
}

export function onSchemeChange(cb: () => void): () => void {
  const handlers: Array<() => void> = []
  try {
    WebApp.onEvent('themeChanged', cb)
    handlers.push(() => WebApp.offEvent('themeChanged', cb))
  } catch {
    /* noop */
  }
  if (typeof window !== 'undefined' && window.matchMedia) {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    mq.addEventListener('change', cb)
    handlers.push(() => mq.removeEventListener('change', cb))
  }
  return () => handlers.forEach((h) => h())
}

export function applyTelegramChrome(scheme: Scheme): void {
  try {
    WebApp.setBackgroundColor(THEME_BG[scheme])
    WebApp.setHeaderColor(THEME_BG[scheme])
  } catch {
    /* noop */
  }
}

export function hapticSuccess(): void {
  try {
    WebApp.HapticFeedback.impactOccurred('medium')
  } catch {
    /* noop */
  }
}

/** Tashqi havolani ochadi (PDF yuklab olish uchun). */
export function openLink(url: string): void {
  try {
    WebApp.openLink(url)
  } catch {
    window.open(url, '_blank', 'noopener')
  }
}

export function confirmDialog(message: string): Promise<boolean> {
  return new Promise((resolve) => {
    try {
      WebApp.showConfirm(message, (ok) => resolve(Boolean(ok)))
    } catch {
      resolve(window.confirm(message))
    }
  })
}

interface MainButtonOpts {
  text: string
  onClick: () => void
  loading?: boolean
  enabled?: boolean
}

/** Telegram MainButton — o'z tugmangni yasama. */
export function setMainButton({
  text,
  onClick,
  loading = false,
  enabled = true,
}: MainButtonOpts): () => void {
  try {
    const mb = WebApp.MainButton
    mb.setText(text)
    mb.offClick(onClick)
    mb.onClick(onClick)
    if (loading) mb.showProgress(false)
    else mb.hideProgress()
    if (enabled) mb.enable()
    else mb.disable()
    mb.show()
    return () => {
      try {
        mb.offClick(onClick)
        mb.hide()
      } catch {
        /* noop */
      }
    }
  } catch {
    return () => {}
  }
}

export function setBackButton(onClick: (() => void) | null): () => void {
  try {
    const bb = WebApp.BackButton
    if (!onClick) {
      bb.hide()
      return () => {}
    }
    bb.onClick(onClick)
    bb.show()
    return () => {
      try {
        bb.offClick(onClick)
        bb.hide()
      } catch {
        /* noop */
      }
    }
  } catch {
    return () => {}
  }
}
