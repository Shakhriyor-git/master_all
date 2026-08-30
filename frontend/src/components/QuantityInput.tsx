import { forwardRef, useLayoutEffect, useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import {
  caretAfterDigits,
  parseQtyInput,
  qtyDisplay,
} from '../lib/numberInput'

interface Props {
  value: number | null
  onChange: (value: number | null) => void
  placeholder?: string
  className?: string
  autoFocus?: boolean
  id?: string
  'aria-label'?: string
}

/**
 * Miqdor maydoni: kasr ruxsat (vergul ham nuqta ham), ko'rsatishda vergul,
 * chiqishda son (nuqta). Kursor joyida qoladi.
 */
export const QuantityInput = forwardRef<HTMLInputElement, Props>(
  function QuantityInput(
    { value, onChange, placeholder, className, autoFocus, id, ...rest },
    forwardedRef,
  ) {
    const localRef = useRef<HTMLInputElement | null>(null)
    const caret = useRef<number | null>(null)
    const [text, setText] = useState<string>(() => qtyDisplay(value))

    const external = qtyDisplay(value)
    const lastExternal = useRef(external)
    if (external !== lastExternal.current && external !== text) {
      lastExternal.current = external
      setText(external)
    }

    useLayoutEffect(() => {
      const el = localRef.current
      if (el && caret.current != null) {
        el.setSelectionRange(caret.current, caret.current)
        caret.current = null
      }
    }, [text])

    function setRef(el: HTMLInputElement | null) {
      localRef.current = el
      if (typeof forwardedRef === 'function') forwardedRef(el)
      else if (forwardedRef) forwardedRef.current = el
    }

    function handle(e: ChangeEvent<HTMLInputElement>) {
      const el = e.target
      const prevCaret = el.selectionStart ?? el.value.length
      const rawTyped = el.value
      const { display, value: num } = parseQtyInput(rawTyped)
      caret.current = caretAfterDigits(rawTyped, prevCaret, display)
      setText(display)
      onChange(num)
    }

    return (
      <input
        {...rest}
        id={id}
        ref={setRef}
        inputMode="decimal"
        autoComplete="off"
        value={text}
        onChange={handle}
        placeholder={placeholder}
        className={className}
        autoFocus={autoFocus}
      />
    )
  },
)
