import {
  IconBuildingBank,
  IconCash,
  IconCreditCard,
  IconPackage,
  IconReceipt,
  IconTool,
} from '@tabler/icons-react'
import type { EntryKind, PayMethod } from '../api/entries'

export const KIND_LABEL: Record<EntryKind, string> = {
  work: 'Ish',
  material: 'Material',
  expense: 'Xarajat',
}

export const KIND_ICON: Record<EntryKind, typeof IconTool> = {
  work: IconTool,
  material: IconPackage,
  expense: IconReceipt,
}

/** Yozuv/to'lov kartasi turi — bitta joyda markazlashtirilgan xaritalash. */
export type RowType = EntryKind | 'payment'

/** Karta chegarasi + foni (maket 8-bo'lim "Rang xaritasi"). */
export const ROW_EDGE: Record<RowType, string> = {
  work: 'border-[color:var(--border-work)] bg-surface',
  material: 'border-[color:var(--border-material)] bg-surface',
  expense: 'border-[color:var(--border-expense)] bg-surface',
  payment: 'border-[color:var(--border-payment)] bg-[var(--bg-payment)]',
}

export const ROW_ICON: Record<RowType, typeof IconTool> = {
  work: IconTool,
  material: IconPackage,
  expense: IconReceipt,
  payment: IconCash,
}

/** Ikon doirasi foni + rangi. */
export const ROW_ICON_BG: Record<RowType, string> = {
  work: 'bg-primary-soft text-primary',
  material: 'bg-accent-soft text-accent',
  expense: 'bg-danger-soft text-danger',
  payment: 'bg-success-soft text-success',
}

/** Summa matni rangi. */
export const ROW_AMOUNT: Record<RowType, string> = {
  work: 'text-primary',
  material: 'text-accent',
  expense: 'text-danger',
  payment: 'text-success',
}

export const METHOD_LABEL: Record<PayMethod, string> = {
  cash: 'Naqd',
  card: 'Karta',
  transfer: 'O‘tkazma',
}

export const PURPOSE_LABEL: Record<'labor' | 'material', string> = {
  labor: 'Ish haqi uchun',
  material: 'Material uchun',
}

export const METHOD_ICON: Record<PayMethod, typeof IconCash> = {
  cash: IconCash,
  card: IconCreditCard,
  transfer: IconBuildingBank,
}
