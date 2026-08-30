import { IconBrandTelegram } from '@tabler/icons-react'

export function OpenInTelegram() {
  return (
    <div className="flex min-h-full flex-col items-center justify-center gap-4 bg-bg px-8 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-card bg-primary-soft text-primary">
        <IconBrandTelegram size={32} />
      </div>
      <h1 className="text-title text-text">Bu ilovani Telegram orqali oching</h1>
      <p className="max-w-xs text-body text-text-muted">
        Ilova botning menyu tugmasi orqali ishlaydi. Brauzerda emas, Telegram
        ichida oching.
      </p>
    </div>
  )
}
