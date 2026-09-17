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
const RELOADED_KEY = 'reloaded_for'

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

function alreadyReloadedFor(id: string): boolean {
  try {
    return sessionStorage.getItem(RELOADED_KEY) === id
  } catch {
    return true // sessionStorage yopiq — aylanma bo'lmasin, reload qilmaymiz
  }
}

/** Kesh chetlab o'tilsin: URL ga ?v=<sha7> qo'shib yuklaymiz. */
function reloadBypassingCache(id: string): void {
  try {
    sessionStorage.setItem(RELOADED_KEY, id)
  } catch {
    return
  }
  const u = new URL(window.location.href)
  u.searchParams.set('v', id.slice(0, 7))
  window.location.replace(u.toString())
}

/** index.html dagi inline skript bilan bir xil semantika. */
export async function reloadIfStale(): Promise<void> {
  if (!import.meta.env.PROD) return
  const server = await fetchServerBuild()
  if (!server || server === BUILD_ID) return
  if (alreadyReloadedFor(server)) return
  reloadBypassingCache(server)
}

/** Sozlamalardagi "yangilash" tugmasi: belgini tozalab majburan reload. */
export function forceReload(): void {
  try {
    sessionStorage.removeItem(RELOADED_KEY)
  } catch {
    /* noop */
  }
  const u = new URL(window.location.href)
  u.searchParams.set('v', String(Date.now()))
  window.location.replace(u.toString())
}
