import type { ReactNode } from 'react'
import { motion, useReducedMotion } from 'framer-motion'

interface Props {
  title: string
  action?: ReactNode
  children: ReactNode
}

/** Ekran karkasi: sarlavha + skroll qilinadigan kontent. */
export function Screen({ title, action, children }: Props) {
  const reduce = useReducedMotion()
  return (
    <motion.div
      className="flex min-h-full flex-col bg-bg"
      initial={reduce ? false : { opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.18, ease: 'easeOut' }}
    >
      <header className="flex items-center justify-between px-4 pb-2 pt-4">
        <h1 className="text-title text-text">{title}</h1>
        {action}
      </header>
      <div className="flex-1 px-4 pb-2">{children}</div>
    </motion.div>
  )
}

export function EmptyState({
  text,
  action,
}: {
  text: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-card border border-border bg-surface px-6 py-10 text-center">
      <p className="text-body text-text-muted">{text}</p>
      {action}
    </div>
  )
}
