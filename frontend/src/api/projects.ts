import { api } from './client'

export interface Project {
  id: number
  user_id: number
  title: string
  address: string | null
  client_name: string | null
  client_phone: string | null
  status: string
  started_at: string | null
  closed_at: string | null
  created_at: string
  updated_at: string | null
  deleted_at: string | null
}

export const listProjects = (status?: string) =>
  api<Project[]>(`/api/projects${status ? `?status=${status}` : ''}`)

export interface ProjectPatch {
  title?: string
  address?: string | null
  client_name?: string | null
  client_phone?: string | null
  status?: 'active' | 'paused' | 'completed' | 'archived'
}

export const updateProject = (id: number, body: ProjectPatch) =>
  api<Project>(`/api/projects/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })

export const deleteProject = (id: number) =>
  api<void>(`/api/projects/${id}`, { method: 'DELETE' })

export interface Summary {
  labor: {
    works_total: string
    paid: string
    /** manfiy bo'lsa — mijoz avansi */
    remaining: string
  }
  materials: {
    materials_total: string
    expenses_total: string
    paid: string
    remaining: string
  }
  /** paid_by=client yozuvlar — mijoz o'zi olgan, faqat ma'lumot */
  client_bought: string
  meta: { entries_count: number; last_entry_date: string | null }
}

export const getSummary = (projectId: number) =>
  api<Summary>(`/api/projects/${projectId}/summary`)
