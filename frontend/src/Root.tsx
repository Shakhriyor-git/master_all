import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/AppLayout'
import { ErrorScreen, SplashSkeleton } from './components/states'
import { ThemeProvider } from './theme/ThemeProvider'
import { ActiveProjectProvider } from './hooks/activeProject'
import { useMe, useUpdateMe } from './hooks/useMe'
import { Home } from './screens/Home'
import { History } from './screens/History'
import { Profile } from './screens/Profile'
import { Settings } from './screens/Settings'
import { Add } from './screens/Add'

export function Root() {
  const me = useMe()
  const updateMe = useUpdateMe()

  if (me.isPending) return <SplashSkeleton />
  if (me.isError || !me.data) {
    return <ErrorScreen error={me.error} onRetry={() => void me.refetch()} />
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
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppLayout>
      </ActiveProjectProvider>
    </ThemeProvider>
  )
}
