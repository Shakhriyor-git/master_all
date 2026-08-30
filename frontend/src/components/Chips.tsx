interface ChipOption {
  value: string
  label: string
}

interface Props {
  options: ChipOption[]
  value: string | null
  onChange: (v: string) => void
}

export function Chips({ options, value, onChange }: Props) {
  return (
    <div className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1">
      {options.map((o) => {
        const active = o.value === value
        return (
          <button
            key={o.value}
            type="button"
            onClick={() => onChange(o.value)}
            className={
              active
                ? 'min-h-[40px] shrink-0 rounded-chip bg-primary px-4 text-body text-on-primary'
                : 'min-h-[40px] shrink-0 rounded-chip border border-border bg-surface px-4 text-body text-text-muted'
            }
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}
