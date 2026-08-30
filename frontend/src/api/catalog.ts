import { api } from './client'

export interface Category {
  id: number
  user_id: number
  name: string
  kind: 'work' | 'material'
  icon: string | null
  sort_order: number
  is_active: boolean
  items_count: number
}

export interface PriceItem {
  id: number
  user_id: number
  category_id: number | null
  name: string
  kind: string
  unit: string
  default_price: string
  is_active: boolean
  category_name: string | null
  unit_label: string | null
}

export interface Unit {
  id: number
  code: string
  label: string
  is_system: boolean
  is_active: boolean
}

export const listCategories = (kind: 'work' | 'material') =>
  api<Category[]>(`/api/categories?kind=${kind}`)

export function listPriceItems(params: {
  kind?: string
  categoryId?: number
  q?: string
}) {
  const qs = new URLSearchParams()
  if (params.kind) qs.set('kind', params.kind)
  if (params.categoryId != null) qs.set('category_id', String(params.categoryId))
  if (params.q) qs.set('q', params.q)
  const s = qs.toString()
  return api<PriceItem[]>(`/api/price-items${s ? `?${s}` : ''}`)
}

export const listUnits = () => api<Unit[]>('/api/units')

export const createPriceItem = (body: {
  category_id?: number
  name: string
  kind: string
  unit: string
  default_price: number | string
}) =>
  api<PriceItem>('/api/price-items', {
    method: 'POST',
    body: JSON.stringify(body),
  })

export const updatePriceItem = (
  id: number,
  body: {
    category_id?: number | null
    name?: string
    unit?: string
    default_price?: number | string
  },
) =>
  api<PriceItem>(`/api/price-items/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })

export const deletePriceItem = (id: number) =>
  api<void>(`/api/price-items/${id}`, { method: 'DELETE' })

/** Bir so'rovda 50 tagacha pozitsiya narxini yangilaydi. */
export const bulkUpdatePriceItems = (
  items: { id: number; default_price: number | string }[],
) =>
  api<PriceItem[]>('/api/price-items/bulk', {
    method: 'PATCH',
    body: JSON.stringify({ items }),
  })

export const createCategory = (body: {
  name: string
  kind: 'work' | 'material'
  icon?: string | null
}) =>
  api<Category>('/api/categories', {
    method: 'POST',
    body: JSON.stringify(body),
  })

export const updateCategory = (
  id: number,
  body: { name?: string; icon?: string | null; is_active?: boolean },
) =>
  api<Category>(`/api/categories/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })

export const deleteCategory = (id: number) =>
  api<void>(`/api/categories/${id}`, { method: 'DELETE' })

export const createUnit = (body: { code: string; label: string }) =>
  api<Unit>('/api/units', { method: 'POST', body: JSON.stringify(body) })

// --- Eski standart katalogni tozalash (bir martalik) ---

export interface SeededInfo {
  price_items: number
  categories: number
}

export const getSeededInfo = () =>
  api<SeededInfo>('/api/price-items/seeded')

export const deleteSeededCatalog = async (): Promise<void> => {
  await api('/api/price-items/seeded', { method: 'DELETE' })
  await api('/api/categories/seeded', { method: 'DELETE' })
}
