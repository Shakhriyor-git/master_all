import { useEffect, useRef, useState } from 'react'
import { useReducedMotion } from 'framer-motion'
import { fmtMoney } from '../lib/format'

interface Props {
  value: number
  /** true — 'so'm' qo'shiladi; false — faqat raqam */
  money?: boolean
  className?: string
}

/** Katta summalar 400 ms da sanab chiqadi. Asosiy karta va yakuniy hisobda. */
export function CountUp({ value, money = true, className }: Props) {
  const reduce = useReducedMotion()
  const [shown, setShown] = useState(reduce ? value : 0)
  const from = useRef(0)

  useEffect(() => {
    if (reduce) {
      setShown(value)
      return
    }
    const start = performance.now()
    const a = from.current
    const b = value
    let raf = 0
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / 400)
      const eased = 1 - (1 - t) ** 3
      setShown(a + (b - a) * eased)
      if (t < 1) raf = requestAnimationFrame(tick)
      else from.current = b
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [value, reduce])

  const rounded = Math.round(shown)
  return (
    <span className={className}>
      {money ? fmtMoney(rounded) : rounded.toLocaleString('ru-RU')}
    </span>
  )
}
