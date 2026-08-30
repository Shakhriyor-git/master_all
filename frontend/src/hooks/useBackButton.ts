import { useEffect } from 'react'
import { setBackButton } from '../lib/telegram'

/** Ichki ekranlarda Telegram BackButton — o'z tugmangni yasama. */
export function useBackButton(onClick: () => void): void {
  useEffect(() => setBackButton(onClick), [onClick])
}
