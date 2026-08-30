interface Option<T extends string> {
  value: T
  label: string
}

interface Props<T extends string> {
  options: Option<T>[]
  value: T
  onChange: (v: T) => void
}

export function Segment<T extends string>({
  options,
  value,
  onChange,
}: Props<T>) {
  return (
    <div className="flex gap-1 rounded-btn border border-border bg-surface-2 p-1">
      {options.map((o) => {
        const active = o.value === value
        return (
          <button
            key={o.value}
            type="button"
            onClick={() => onChange(o.value)}
            className={
              active
                ? 'min-h-[44px] flex-1 rounded-[10px] bg-primary px-3 text-body text-on-primary'
                : 'min-h-[44px] flex-1 rounded-[10px] px-3 text-body text-text-muted'
            }
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}
