/**
 * Barcha formatlash SHU YERDA. Hech qayerda qo'lda formatlash bo'lmasin.
 */

const MONTHS_UZ = [
  'yanvar',
  'fevral',
  'mart',
  'aprel',
  'may',
  'iyun',
  'iyul',
  'avgust',
  'sentabr',
  'oktabr',
  'noyabr',
  'dekabr',
]

function groupInt(digits: string): string {
  return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

type Num = number | string | null | undefined

/** 1250000 -> "1 250 000 so'm" */
export function fmtMoney(value: Num): string {
  const n = Math.round(Number(value) || 0)
  const sign = n < 0 ? '-' : ''
  return `${sign}${groupInt(String(Math.abs(n)))} so'm`
}

/** Faqat raqam, so'm yozuvisiz: 1250000 -> "1 250 000" */
export function fmtNumber(value: Num): string {
  const n = Math.round(Number(value) || 0)
  const sign = n < 0 ? '-' : ''
  return `${sign}${groupInt(String(Math.abs(n)))}`
}

/** fmtQty(11.5, "m²") -> "11,5 m²" — kasr vergul bilan */
export function fmtQty(value: Num, unit?: string | null): string {
  const num = Number(value) || 0
  const rounded = Math.round(num * 1000) / 1000
  const [intPart, frac] = Math.abs(rounded).toString().split('.')
  const sign = rounded < 0 ? '-' : ''
  const body = frac ? `${groupInt(intPart)},${frac}` : groupInt(intPart)
  return unit ? `${sign}${body} ${unit}` : `${sign}${body}`
}

function toDate(d: string | number | Date): Date {
  return d instanceof Date ? d : new Date(d)
}

/** "28 avgust 2026" */
export function fmtDate(d: string | number | Date): string {
  const x = toDate(d)
  return `${x.getDate()} ${MONTHS_UZ[x.getMonth()]} ${x.getFullYear()}`
}

/** Tarix ro'yxati sarlavhasi: "Bugun" / "Kecha" / "28 avgust" */
export function fmtDateGroup(d: string | number | Date): string {
  const x = toDate(d)
  const start = new Date()
  start.setHours(0, 0, 0, 0)
  const that = new Date(x)
  that.setHours(0, 0, 0, 0)
  const diffDays = Math.round((start.getTime() - that.getTime()) / 86_400_000)
  if (diffDays === 0) return 'Bugun'
  if (diffDays === 1) return 'Kecha'
  const sameYear = x.getFullYear() === new Date().getFullYear()
  return sameYear
    ? `${x.getDate()} ${MONTHS_UZ[x.getMonth()]}`
    : fmtDate(x)
}

/** "14:30" */
export function fmtTime(d: string | number | Date): string {
  const x = toDate(d)
  return x.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

/** "+998901234567" -> "+998 90 123 45 67"; boshqa formatlar o'zgarmaydi */
export function fmtPhone(phone: string | null | undefined): string {
  if (!phone) return ''
  const digits = phone.replace(/\D/g, '')
  if (digits.length === 12 && digits.startsWith('998')) {
    return `+998 ${digits.slice(3, 5)} ${digits.slice(5, 8)} ${digits.slice(8, 10)} ${digits.slice(10)}`
  }
  return phone
}
