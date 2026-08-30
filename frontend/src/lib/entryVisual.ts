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

/** ikon foni */
export const KIND_ICON_BG: Record<EntryKind, string> = {
  work: 'bg-primary-soft text-primary',
  material: 'bg-accent-soft text-accent',
  expense: 'bg-surface-2 text-text-muted',
}

/** summa rangi */
export const KIND_AMOUNT: Record<EntryKind, string> = {
  work: 'text-primary',
  material: 'text-accent',
  expense: 'text-text-muted',
}

export const METHOD_LABEL: Record<PayMethod, string> = {
  cash: 'Naqd',
  card: 'Karta',
  transfer: 'O‘tkazma',
}

export const METHOD_ICON: Record<PayMethod, typeof IconCash> = {
  cash: IconCash,
  card: IconCreditCard,
  transfer: IconBuildingBank,
}
