import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/AppLayout'
import { ErrorScreen, SplashSkeleton } from './components/states'
import { ThemeProvider } from './theme/ThemeProvider'
import { ActiveProjectProvider } from './hooks/activeProject'
import { useMe, useUpdateMe } from './hooks/useMe'
import { Home } from './screens/Home'
import { History } from './screens/History'
import { Onboarding } from './screens/Onboarding'
import { Profile } from './screens/Profile'
import { Settings } from './screens/Settings'
import { Add } from './screens/Add'
import { Catalog } from './screens/Catalog'
import { Notes } from './screens/Notes'
import { Budget } from './screens/Budget'

export function Root() {
  const me = useMe()
  const updateMe = useUpdateMe()

  if (me.isPending) return <SplashSkeleton />
  if (me.isError || !me.data) {
    return <ErrorScreen error={me.error} onRetry={() => void me.refetch()} />
  }

  if (!me.data.onboarded) {
    return (
      <ThemeProvider
        pref={me.data.theme}
        onPrefChange={(theme) => updateMe.mutate({ theme })}
      >
        <Onboarding me={me.data} />
      </ThemeProvider>
    )
  }

  return (
    <ThemeProvider
      pref={me.data.theme}
      onPrefChange={(theme) => updateMe.mutate({ theme })}
    >
      <ActiveProjectProvider>
        <AppLayout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/history" element={<History />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/add" element={<Add />} />
            <Route path="/catalog" element={<Catalog />} />
            <Route path="/notes" element={<Notes />} />
            <Route path="/budget" element={<Budget />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppLayout>
      </ActiveProjectProvider>
    </ThemeProvider>
  )
}
