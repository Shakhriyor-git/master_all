/**
 * Eski bundle'dan himoya. Telegram WebView `index.html` ni keshlab, deploy'dan
 * keyin ham eski JS'ni ko'rsatishi mumkin (refresh qilmaguncha).
 *
 * Model: serverdagi `version.json` ID si sessiyada oxirgi ko'rilgan ID
 * (`sessionStorage.seen_build`) bilan solishtiriladi. Farq bo'lsa — yangi ID
 * yoziladi va bir marta reload. Bir sessiyada bir marta — aylanma bo'lmaydi.
 *
 * `__BUILD_ID__` (bundle ichidagi git sha) solishtirishda ISHLATILMAYDI —
 * faqat ko'rsatish/debug uchun (Sozlamalar ekrani).
 */
const SEEN_KEY = 'seen_build'

/** Bundle qaysi commit'dan build qilingan — ko'rsatish uchun. */
export const BUILD_ID: string = __BUILD_ID__

/** Sozlamalarda ko'rsatiladigan qisqa shakl — git sha ning 7 belgisi. */
export const BUILD_SHORT = BUILD_ID.slice(0, 7)

async function fetchServerBuild(): Promise<string | null> {
  try {
    // ?t= — brauzer keshi ham chetlab o'tilsin
    const res = await fetch(`/version.json?t=${Date.now()}`, {
      cache: 'no-store',
    })
    if (!res.ok) return null
    return ((await res.json()) as { build?: string }).build ?? null
  } catch {
    return null // internet yo'q — eski bundle bilan davom etamiz
  }
}

function readSeen(): string | null {
  try {
    return sessionStorage.getItem(SEEN_KEY)
  } catch {
    return null
  }
}

function writeSeen(id: string): boolean {
  try {
    sessionStorage.setItem(SEEN_KEY, id)
    return true
  } catch {
    return false // sessionStorage yopiq — reload aylanmasin, tekshirmaymiz
  }
}

export async function reloadIfStale(): Promise<void> {
  if (!import.meta.env.PROD) return
  const server = await fetchServerBuild()
  if (!server) return
  if (readSeen() === server) return
  if (!writeSeen(server)) return
  window.location.reload()
}

/** Sozlamalardagi "yangilash" tugmasi: belgini tozalab majburan reload. */
export function forceReload(): void {
  try {
    sessionStorage.removeItem(SEEN_KEY)
  } catch {
    /* noop */
  }
  window.location.reload()
}
