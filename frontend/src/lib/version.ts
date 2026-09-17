/**
 * Eski bundle'dan himoya. Telegram WebView `index.html` ni keshlab, deploy'dan
 * keyin ham eski JS'ni ko'rsatishi mumkin.
 *
 * Asosiy tekshiruv index.html ichida inline (React'dan oldin). Bu modul —
 * sessiya davomidagi qo'shimcha himoya (ilova ochiq qoldirilib, keyin
 * qaytilganda) va Sozlamalardagi "yangilash" tugmasi.
 *
 * Model: serverdagi `version.json` ID si shu bundle ichidagi `__BUILD_ID__`
 * bilan solishtiriladi. Farq bo'lsa — kesh chetlab o'tiladigan URL bilan
 * reload. Bir build uchun sessiyada bir marta (`reloaded_for`) — aylanmaydi.
 */
const DEBUG_KEY = 'version_debug'

/** Bundle qaysi commit'dan build qilingan — ko'rsatish uchun. */
export const BUILD_ID: string = __BUILD_ID__

/** Sozlamalarda ko'rsatiladigan qisqa shakl — git sha ning 7 belgisi. */
export const BUILD_SHORT = BUILD_ID.slice(0, 7)

/** index.html dagi inline skript yozgan oxirgi tekshiruv natijasi. */
export function readVersionDebug(): string {
  try {
    return localStorage.getItem(DEBUG_KEY) ?? '—'
  } catch {
    return '—'
  }
}

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

/**
 * Yangi index.html ni serverdan (unikal ?t= — kesh mumkin emas) olib,
 * hujjatni joyida almashtiradi. index.html dagi inline skript bilan bir xil
 * usul — Telegram WebView reload/replace ni keshdan berishi mumkin.
 */
async function swapDocument(): Promise<void> {
  const html = await (
    await fetch(`/?t=${Date.now()}`, { cache: 'no-store' })
  ).text()
  document.open()
  document.write(html)
  document.close()
}

/** Ilova ochiq turganda serverda yangi build paydo bo'lsa — almashtirish. */
export async function reloadIfStale(): Promise<void> {
  if (!import.meta.env.PROD) return
  const server = await fetchServerBuild()
  if (!server || server === BUILD_ID) return
  try {
    await swapDocument()
  } catch {
    /* internet uzildi — eski bundle bilan davom etamiz */
  }
}

/** Sozlamalardagi "yangilash" tugmasi: majburan yangi hujjat. */
export function forceReload(): void {
  void swapDocument().catch(() => window.location.reload())
}
