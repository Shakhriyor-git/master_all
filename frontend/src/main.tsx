import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import './index.css'

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import { bindViewportSync, getColorScheme, initTelegram } from './lib/telegram'
import { reloadIfStale } from './lib/version'

// Splash paytida ham to'g'ri mavzu
document.documentElement.setAttribute('data-theme', getColorScheme())
initTelegram()
bindViewportSync()
void reloadIfStale()

const root = document.getElementById('root')
if (!root) throw new Error('#root topilmadi')

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
