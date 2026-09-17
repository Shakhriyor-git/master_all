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
  },
  server: {
    port: 5173,
    host: true,
  },
})
