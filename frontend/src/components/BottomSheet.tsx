import { AnimatePresence, motion } from 'framer-motion'
import { useEffect } from 'react'
import type { ReactNode } from 'react'

interface Props {
  open: boolean
  onClose: () => void
  title?: string
  children: ReactNode
}

export function BottomSheet({ open, onClose, title, children }: Props) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            className="fixed inset-0 z-30 bg-black/40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div
            className="fixed inset-x-0 bottom-0 z-40 mx-auto max-h-[85vh] max-w-md overflow-y-auto rounded-t-[20px] border border-border bg-surface pb-[env(safe-area-inset-bottom)]"
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'tween', duration: 0.22 }}
          >
            <div className="sticky top-0 flex items-center justify-center bg-surface pt-2">
              <span className="h-1 w-10 rounded-chip bg-border" />
            </div>
            {title && (
              <h2 className="px-4 pb-1 pt-2 text-title text-text">{title}</h2>
            )}
            <div className="px-4 pb-4 pt-2">{children}</div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
