import { useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { IconCheck, IconChevronRight, IconDotsVertical } from '@tabler/icons-react'
import type { Project } from '../api/projects'
import { useProjectMutations } from '../hooks/useProjects'
import { confirmDialog, hapticSuccess } from '../lib/telegram'
import { BottomSheet } from './BottomSheet'

const INPUT =
  'w-full rounded-btn border border-border bg-surface-2 px-3 py-2 text-body text-text outline-none focus:border-primary'

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
  const [menu, setMenu] = useState<Project | null>(null)
  const [edit, setEdit] = useState<Project | null>(null)
  const [showDone, setShowDone] = useState(false)

  const activeList = projects.filter((p) => p.status !== 'completed')
  const doneList = projects.filter((p) => p.status === 'completed')

  return (
    <>
      <BottomSheet open={open} onClose={onClose} title="Obyektlar">
        <ul className="space-y-1">
          {activeList.map((p) => (
            <Row
              key={p.id}
              project={p}
              activeId={activeId}
              onPick={(id) => {
                onPick(id)
                onClose()
              }}
              onMenu={() => setMenu(p)}
            />
          ))}
        </ul>

        {doneList.length > 0 && (
          <div className="mt-3">
            <button
              type="button"
              onClick={() => setShowDone((v) => !v)}
              className="flex w-full items-center justify-between rounded-btn px-3 py-2 text-label text-text-muted"
            >
              <span>Tugatilgan ({doneList.length})</span>
              <IconChevronRight
                size={16}
                className={showDone ? 'rotate-90 transition' : 'transition'}
              />
            </button>
            {showDone && (
              <ul className="space-y-1">
                {doneList.map((p) => (
                  <Row
                    key={p.id}
                    project={p}
                    activeId={activeId}
                    onPick={(id) => {
                      onPick(id)
                      onClose()
                    }}
                    onMenu={() => setMenu(p)}
                  />
                ))}
              </ul>
            )}
          </div>
        )}
      </BottomSheet>

      <ProjectMenuSheet
        project={menu}
        projects={projects}
        activeId={activeId}
        onPick={onPick}
        onClose={() => setMenu(null)}
        onEdit={(p) => {
          setMenu(null)
          setEdit(p)
        }}
      />
      <ProjectEditSheet project={edit} onClose={() => setEdit(null)} />
    </>
  )
}

function Row({
  project,
  activeId,
  onPick,
  onMenu,
}: {
  project: Project
  activeId: number | undefined
  onPick: (id: number) => void
  onMenu: () => void
}) {
  return (
    <li className="flex items-center gap-1">
      <button
        type="button"
        onClick={() => onPick(project.id)}
        className="flex min-h-[44px] flex-1 items-center justify-between gap-2 rounded-btn px-3 text-left text-body text-text active:bg-surface-2"
      >
        <span className="truncate">{project.title}</span>
        {project.id === activeId && (
          <IconCheck size={18} className="shrink-0 text-primary" />
        )}
      </button>
      <button
        type="button"
        aria-label="Amallar"
        onClick={onMenu}
        className="shrink-0 p-2 text-text-faint active:text-text"
      >
        <IconDotsVertical size={18} />
      </button>
    </li>
  )
}

function ProjectMenuSheet({
  project,
  projects,
  activeId,
  onPick,
  onClose,
  onEdit,
}: {
  project: Project | null
  projects: Project[]
  activeId: number | undefined
  onPick: (id: number) => void
  onClose: () => void
  onEdit: (p: Project) => void
}) {
  const { update, remove } = useProjectMutations()
  if (!project) return null
  const isDone = project.status === 'completed'
  const target = project

  return (
    <BottomSheet open={!!project} onClose={onClose} title={project.title}>
      <div className="space-y-2">
        <Btn onClick={() => onEdit(project)}>Tahrirlash</Btn>
        <Btn
          onClick={async () => {
            await update.mutateAsync({
              id: target.id,
              status: isDone ? 'active' : 'completed',
            })
            hapticSuccess()
            // faol obyekt tugatilsa — Asosiy boshqa obyektga o'tsin
            if (!isDone && target.id === activeId) {
              const other = projects.find(
                (p) => p.id !== target.id && p.status !== 'completed',
              )
              if (other) onPick(other.id)
            }
            onClose()
          }}
        >
          {isDone ? 'Qayta faollashtirish' : 'Tugatildi'}
        </Btn>
        <Btn
          danger
          onClick={async () => {
            if (!(await confirmDialog(`"${project.title}" o‘chirilsinmi?`)))
              return
            await remove.mutateAsync(project.id)
            hapticSuccess()
            onClose()
          }}
        >
          O‘chirish
        </Btn>
      </div>
    </BottomSheet>
  )
}

function ProjectEditSheet({
  project,
  onClose,
}: {
  project: Project | null
  onClose: () => void
}) {
  const { update } = useProjectMutations()
  const [title, setTitle] = useState('')
  const [client, setClient] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')

  const seed = useRef<number | null>(null)
  if (project && seed.current !== project.id) {
    seed.current = project.id
    setTitle(project.title)
    setClient(project.client_name ?? '')
    setPhone(project.client_phone ?? '')
    setAddress(project.address ?? '')
  }
  if (!project) {
    if (seed.current !== null) seed.current = null
    return null
  }

  return (
    <BottomSheet open={!!project} onClose={onClose} title="Obyektni tahrirlash">
      <div className="space-y-3">
        <Field label="Nomi" value={title} onChange={setTitle} />
        <Field label="Mijoz" value={client} onChange={setClient} />
        <Field label="Telefon" value={phone} onChange={setPhone} tel />
        <Field label="Manzil" value={address} onChange={setAddress} />
        <button
          type="button"
          disabled={!title.trim() || update.isPending}
          onClick={async () => {
            await update.mutateAsync({
              id: project.id,
              title: title.trim(),
              client_name: client.trim() || null,
              client_phone: phone.trim() || null,
              address: address.trim() || null,
            })
            hapticSuccess()
            onClose()
          }}
          className="min-h-[44px] w-full rounded-btn bg-primary text-body text-on-primary active:scale-[0.98] disabled:opacity-60"
        >
          Saqlash
        </button>
      </div>
    </BottomSheet>
  )
}

function Field({
  label,
  value,
  onChange,
  tel,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  tel?: boolean
}) {
  return (
    <label className="block text-label text-text-muted">
      {label}
      <input
        className={INPUT}
        inputMode={tel ? 'tel' : undefined}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  )
}

function Btn({
  children,
  onClick,
  danger,
}: {
  children: ReactNode
  onClick: () => void
  danger?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        danger
          ? 'min-h-[44px] w-full rounded-btn bg-danger-soft text-body text-danger active:scale-[0.98]'
          : 'min-h-[44px] w-full rounded-btn bg-surface-2 text-body text-text active:scale-[0.98]'
      }
    >
      {children}
    </button>
  )
}
