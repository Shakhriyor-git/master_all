/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

/** vite.config.ts `define` orqali — build identifikatori */
declare const __BUILD_ID__: string
