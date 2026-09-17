/**
 * Eski bundle'dan himoya. Telegram WebView `index.html` ni keshlab, deploy'dan
 * keyin ham eski JS'ni ko'rsatishi mumkin (refresh qilmaguncha). Shuning
 * uchun ochilganda serverdagi `version.json` bilan solishtiramiz: farq
 * bo'lsa — bir marta majburan qayta yuklaymiz.
 */
const RELOADED_KEY = 'usta:reloaded-for'

export async function reloadIfStale(): Promise<void> {
  if (!import.meta.env.PROD) return
  let server: string | undefined
  try {
    const res = await fetch(`/version.json?t=${Date.now()}`, {
      cache: 'no-store',
    })
    if (!res.ok) return
    server = ((await res.json()) as { build?: string }).build
  } catch {
    return // internet yo'q — eski bundle bilan davom etamiz
  }
  if (!server || server === __BUILD_ID__) return

  // Bir xil versiya uchun ikki marta reload qilmaymiz (aylanib qolmasin)
  let already: string | null = null
  try {
    already = sessionStorage.getItem(RELOADED_KEY)
    sessionStorage.setItem(RELOADED_KEY, server)
  } catch {
    /* sessionStorage yopiq bo'lishi mumkin */
  }
  if (already === server) return

  window.location.reload()
}
