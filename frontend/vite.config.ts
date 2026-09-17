import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'

// Har build uchun yangi ID. `version.json` ga yoziladi va bundle'ga
// kiritiladi — ilova ochilganda ikkisi solishtiriladi (src/lib/version.ts).
const BUILD_ID = Date.now().toString(36)

function versionFile(): Plugin {
  return {
    name: 'version-json',
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
