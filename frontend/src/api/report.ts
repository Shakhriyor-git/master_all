import { getInitData } from '../lib/telegram'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/** Hisobot turi — alohida ikkita hujjat. */
export type ReportKind = 'labor' | 'materials'

/**
 * Hisobot PDF URL'i. initData sarlavha orqali yuborib bo'lmaydi
 * (openLink tashqi brauzer), shuning uchun `?tma=` bilan uzatiladi.
 */
export function reportPdfUrl(
  projectId: number,
  kind: ReportKind,
  range: { dateFrom?: string; dateTo?: string } = {},
): string {
  const qs = new URLSearchParams({ tma: getInitData() })
  if (range.dateFrom) qs.set('date_from', range.dateFrom)
  if (range.dateTo) qs.set('date_to', range.dateTo)
  const doc = kind === 'labor' ? 'labor' : 'materials'
  return `${BASE}/api/projects/${projectId}/report/${doc}.pdf?${qs}`
}
