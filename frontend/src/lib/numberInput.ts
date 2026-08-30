/**
 * Raqam kiritish maydonlari uchun sof yordamchilar.
 * Botda "20,000" -> 20 bo'lib ketgan; bu yerda takrorlanmasin.
 */

function group(digits: string): string {
  return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

// ---------- PUL (butun son, kasr yo'q) ----------

export interface MoneyParsed {
  display: string
  value: number | null
}

export function parseMoneyInput(raw: string): MoneyParsed {
  let digits = raw.replace(/\D/g, '')
  digits = digits.replace(/^0+(?=\d)/, '')
  if (!digits) return { display: '', value: null }
  return { display: group(digits), value: Number(digits) }
}

export function moneyDisplay(value: number | null): string {
  if (value == null || !Number.isFinite(value)) return ''
  return group(String(Math.round(Math.abs(value))))
}

// ---------- MIQDOR (kasr ruxsat, chiqishda nuqta) ----------

export interface QtyParsed {
  display: string // vergul bilan ko'rsatiladi
  value: number | null
}

export function parseQtyInput(raw: string): QtyParsed {
  // vergul va nuqta -> bitta kasr ajratuvchi
  let s = raw.replace(/\s/g, '').replace(/,/g, '.').replace(/[^\d.]/g, '')
  const dot = s.indexOf('.')
  if (dot !== -1) {
    s = s.slice(0, dot + 1) + s.slice(dot + 1).replace(/\./g, '')
  }
  s = s.replace(/^0+(?=\d)/, '')
  if (s === '' || s === '.') {
    return { display: s === '.' ? '0,' : '', value: null }
  }

  const [rawInt, frac] = s.split('.')
  const intPart = rawInt === '' ? '0' : rawInt
  const displayInt = group(intPart)
  const display = frac !== undefined ? `${displayInt},${frac}` : displayInt
  const num = Number(s.startsWith('.') ? `0${s}` : s)
  return { display, value: Number.isFinite(num) ? num : null }
}

export function qtyDisplay(value: number | null): string {
  if (value == null || !Number.isFinite(value)) return ''
  const rounded = Math.round(value * 1000) / 1000
  const [i, f] = Math.abs(rounded).toString().split('.')
  return f !== undefined ? `${group(i)},${f}` : group(i)
}

// ---------- Kursorni saqlash ----------

/**
 * Formatlashdan keyin kursorni to'g'ri joyga qaytaradi:
 * eski matnda kursordan oldingi raqamlar sonini sanaydi, yangi matnda
 * o'sha sanoqqa yetganda to'xtaydi.
 */
export function caretAfterDigits(
  prevValue: string,
  prevCaret: number,
  nextValue: string,
): number {
  const digitsBefore = (prevValue.slice(0, prevCaret).match(/\d/g) ?? []).length
  if (digitsBefore === 0) {
    // kasr ajratuvchidan keyin turgan bo'lishi mumkin
    const sepBefore = /[.,]/.test(prevValue.slice(0, prevCaret))
    if (sepBefore) {
      const idx = nextValue.search(/[.,]/)
      return idx === -1 ? nextValue.length : idx + 1
    }
    return 0
  }
  let seen = 0
  let pos = 0
  while (pos < nextValue.length && seen < digitsBefore) {
    if (/\d/.test(nextValue[pos])) seen += 1
    pos += 1
  }
  return pos
}
