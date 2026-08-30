import { useEffect } from 'react'
import { setMainButton } from '../lib/telegram'

interface Opts {
  text: string
  onClick: () => void
  visible: boolean
  enabled?: boolean
  loading?: boolean
}

/** Telegram MainButton — o'z tugmangni yasama. */
export function useMainButton({
  text,
  onClick,
  visible,
  enabled = true,
  loading = false,
}: Opts) {
  useEffect(() => {
    if (!visible) return
    return setMainButton({ text, onClick, enabled, loading })
  }, [text, onClick, visible, enabled, loading])
}
