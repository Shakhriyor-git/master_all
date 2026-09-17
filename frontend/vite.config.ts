import { execSync } from 'node:child_process'
import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'

/**
 * Build identifikatori = git commit sha. Lokal va CI bir xil commit'dan
 * bir xil ID beradi — "qaysi commit'dan build qilingan" degan ma'no.
 * CI da GITHUB_SHA, aks holda `git rev-parse HEAD`; git yo'q bo'lsa 'dev'.
 */
function resolveBuildId(): string {
  if (process.env.GITHUB_SHA) return process.env.GITHUB_SHA
  try {
    return execSync('git rev-parse HEAD', { stdio: ['ignore', 'pipe', 'ignore'] })
      .toString()
      .trim()
  } catch {
    return 'dev'
  }
}

const BUILD_ID = resolveBuildId()

/** Commit vaqti — Sozlamalarda "Versiya 17.09.2026 · 11:39" ko'rinishida. */
function resolveBuildDate(): string {
  try {
    // format-local + TZ — CI (UTC) da ham Toshkent vaqti chiqsin
    return execSync(
      'git log -1 --format=%cd --date=format-local:%d.%m.%Y·%H:%M',
      { stdio: ['ignore', 'pipe', 'ignore'], env: { ...process.env, TZ: 'Asia/Tashkent' } },
    )
      .toString()
      .trim()
      .replace('·', ' · ')
  } catch {
    return 'dev'
  }
}

const BUILD_DATE = resolveBuildDate()

/**
 * dist/version.json — ilova ochilganda serverdan olinadi, va index.html ichiga
 * `window.__BUILD_ID__` yoziladi. Ikkisi farq qilsa — HTML eski (keshdan kelgan).
 */
function versionFile(): Plugin {
  return {
    name: 'version-json',
    transformIndexHtml() {
      return [
        {
          tag: 'script',
          injectTo: 'head-prepend',
          children: `window.__BUILD_ID__=${JSON.stringify(BUILD_ID)}`,
        },
      ]
    },
    generateBundle() {
      this.emitFile({
        type: 'asset',
        fileName: 'version.json',
        source: JSON.stringify({ build: BUILD_ID }),
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), versionFile()],
  define: {
    __BUILD_ID__: JSON.stringify(BUILD_ID),
    __BUILD_DATE__: JSON.stringify(BUILD_DATE),
  },
  server: {
    port: 5173,
    host: true,
  },
})
