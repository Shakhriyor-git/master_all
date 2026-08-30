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

export function initTelegram(): void {
  try {
    WebApp.ready()
    WebApp.expand()
  } catch {
    /* Telegram tashqarisida — e'tibor bermaymiz */
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
