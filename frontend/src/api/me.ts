import { api } from './client'

export type ThemePref = 'light' | 'dark' | 'auto'

export interface Me {
  id: number
  full_name: string
  username: string | null
  phone: string | null
  language: string
  theme: ThemePref
  avatar_url: string | null
  active_projects: number
  completed_projects: number
}

export interface MePatch {
  full_name?: string
  phone?: string
  theme?: ThemePref
  language?: string
}

export const getMe = () => api<Me>('/api/me')

export const patchMe = (body: MePatch) =>
  api<Me>('/api/me', { method: 'PATCH', body: JSON.stringify(body) })

export function uploadAvatar(file: File): Promise<Me> {
  const fd = new FormData()
  fd.append('file', file)
  return api<Me>('/api/me/avatar', { method: 'POST', body: fd })
}

export const deleteAvatar = () =>
  api<Me>('/api/me/avatar', { method: 'DELETE' })
