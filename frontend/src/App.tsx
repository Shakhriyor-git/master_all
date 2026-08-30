import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { OpenInTelegram } from './components/OpenInTelegram'
import { getInitData } from './lib/telegram'
import { Root } from './Root'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { refetchOnWindowFocus: false, retry: 1 },
  },
})

export function App() {
  if (!getInitData()) return <OpenInTelegram />

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Root />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
