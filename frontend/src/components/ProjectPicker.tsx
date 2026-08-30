import { IconCheck } from '@tabler/icons-react'
import type { Project } from '../api/projects'
import { BottomSheet } from './BottomSheet'

interface Props {
  open: boolean
  onClose: () => void
  projects: Project[]
  activeId: number | undefined
  onPick: (id: number) => void
}

export function ProjectPicker({
  open,
  onClose,
  projects,
  activeId,
  onPick,
}: Props) {
  return (
    <BottomSheet open={open} onClose={onClose} title="Obyektni tanlang">
      <ul className="space-y-1">
        {projects.map((p) => (
          <li key={p.id}>
            <button
              type="button"
              onClick={() => {
                onPick(p.id)
                onClose()
              }}
              className="flex min-h-[44px] w-full items-center justify-between rounded-btn px-3 text-left text-body text-text active:bg-surface-2"
            >
              <span className="truncate">{p.title}</span>
              {p.id === activeId && (
                <IconCheck size={18} className="shrink-0 text-primary" />
              )}
            </button>
          </li>
        ))}
      </ul>
    </BottomSheet>
  )
}
