import {
  IconBolt,
  IconBrush,
  IconBucket,
  IconCheckbox,
  IconDoor,
  IconDroplet,
  IconHammer,
  IconLayoutGrid,
  IconPackage,
  IconPlug,
  IconRuler2,
  IconStack2,
  IconStairs,
  IconTool,
  IconWall,
  IconWindow,
  type Icon,
} from '@tabler/icons-react'

export interface CatIcon {
  name: string
  Icon: Icon
  /** ikonka rangi; foni shu rangning ~12% shaffofligi (ikkala mavzuda) */
  color: string
  label: string
}

/** Kategoriya ikonkalari — maket 7-bo'lim. Rang har biriga biriktirilgan. */
export const CATEGORY_ICONS: CatIcon[] = [
  { name: 'stack-2', Icon: IconStack2, color: '#2563EB', label: 'Shift' },
  { name: 'wall', Icon: IconWall, color: '#4B5563', label: 'Devor' },
  { name: 'layout-grid', Icon: IconLayoutGrid, color: '#6D28D9', label: 'Pol' },
  { name: 'checkbox', Icon: IconCheckbox, color: '#0E7490', label: 'Kafel' },
  { name: 'bolt', Icon: IconBolt, color: '#B45309', label: 'Elektrika' },
  { name: 'droplet', Icon: IconDroplet, color: '#0369A1', label: 'Santexnika' },
  { name: 'hammer', Icon: IconHammer, color: '#8A3512', label: 'Demontaj' },
  { name: 'tool', Icon: IconTool, color: '#57534E', label: 'Umumiy' },
  { name: 'bucket', Icon: IconBucket, color: '#92400E', label: 'Aralashma' },
  { name: 'brush', Icon: IconBrush, color: '#BE185D', label: 'Bo‘yoq' },
  { name: 'plug', Icon: IconPlug, color: '#B45309', label: 'Elektr mol' },
  { name: 'window', Icon: IconWindow, color: '#15803D', label: 'Deraza' },
  { name: 'door', Icon: IconDoor, color: '#B91C1C', label: 'Eshik' },
  { name: 'stairs', Icon: IconStairs, color: '#4338CA', label: 'Zina' },
  { name: 'ruler-2', Icon: IconRuler2, color: '#475569', label: 'O‘lchov' },
  { name: 'package', Icon: IconPackage, color: '#C2410C', label: 'Boshqa' },
]

const BY_NAME = new Map(CATEGORY_ICONS.map((c) => [c.name, c]))

const FALLBACK: CatIcon = {
  name: 'tool',
  Icon: IconTool,
  color: '#8A8A96',
  label: 'Umumiy',
}

/** Nom bo'yicha ikonka; topilmasa `tool` + kulrang (yiqilmaydi). */
export function catIcon(name: string | null | undefined): CatIcon {
  return (name && BY_NAME.get(name)) || FALLBACK
}

/** Ikonka doirasi uchun inline uslub — fon = rangning ~12% shaffofligi. */
export function catIconStyle(color: string): { background: string; color: string } {
  return { background: `${color}1f`, color }
}
