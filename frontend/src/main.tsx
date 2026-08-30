import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import './index.css'

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import { getColorScheme, initTelegram } from './lib/telegram'

// Splash paytida ham to'g'ri mavzu
document.documentElement.setAttribute('data-theme', getColorScheme())
initTelegram()

const root = document.getElementById('root')
if (!root) throw new Error('#root topilmadi')

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
