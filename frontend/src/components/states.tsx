import { ApiError } from '../api/client'

export function SplashSkeleton() {
  return (
    <div className="min-h-full bg-bg px-4 pt-6">
      <div className="h-6 w-32 animate-pulse rounded-btn bg-surface-2" />
      <div className="mt-4 space-y-3">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="h-24 animate-pulse rounded-card border border-border bg-surface"
          />
        ))}
      </div>
    </div>
  )
}

export function ErrorScreen({
  error,
  onRetry,
}: {
  error: unknown
  onRetry: () => void
}) {
  const network = error instanceof ApiError && error.isNetwork
  return (
    <div className="flex min-h-full flex-col items-center justify-center gap-4 bg-bg px-8 text-center">
      <h1 className="text-title text-text">
        {network ? 'Internet yo‘q' : 'Nimadir noto‘g‘ri ketdi'}
      </h1>
      <p className="text-body text-text-muted">
        Ulanishni tekshirib, qayta urinib ko‘ring.
      </p>
      <button
        type="button"
        onClick={onRetry}
        className="min-h-[44px] rounded-btn bg-primary px-6 text-body text-on-primary active:scale-[0.98]"
      >
        Qayta urinish
      </button>
    </div>
  )
}
