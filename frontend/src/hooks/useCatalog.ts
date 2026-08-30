import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  bulkUpdatePriceItems,
  createCategory,
  createPriceItem,
  createUnit,
  deleteCategory,
  deletePriceItem,
  listCategories,
  listPriceItems,
  listUnits,
  updateCategory,
  updatePriceItem,
} from '../api/catalog'

type Kind = 'work' | 'material'

export function useCategories(kind: Kind) {
  return useQuery({
    queryKey: ['categories', kind],
    queryFn: () => listCategories(kind),
  })
}

export function usePriceItems(kind: Kind, categoryId?: number) {
  return useQuery({
    queryKey: ['price-items', kind, categoryId ?? 'all', ''],
    queryFn: () => listPriceItems({ kind, categoryId }),
  })
}

export function useUnits() {
  return useQuery({ queryKey: ['units'], queryFn: listUnits })
}

/** Katalog o'zgargach — kategoriya sanoqlari va ro'yxatlar yangilansin. */
function invalidateCatalog(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ['categories'] })
  qc.invalidateQueries({ queryKey: ['price-items'] })
}

export function useCatalogMutations() {
  const qc = useQueryClient()
  const done = () => invalidateCatalog(qc)

  return {
    createCategory: useMutation({ mutationFn: createCategory, onSuccess: done }),
    updateCategory: useMutation({
      mutationFn: ({
        id,
        ...body
      }: { id: number; name?: string; icon?: string | null }) =>
        updateCategory(id, body),
      onSuccess: done,
    }),
    deleteCategory: useMutation({
      mutationFn: (id: number) => deleteCategory(id),
      onSuccess: done,
    }),
    createItem: useMutation({ mutationFn: createPriceItem, onSuccess: done }),
    updateItem: useMutation({
      mutationFn: ({
        id,
        ...body
      }: {
        id: number
        category_id?: number | null
        name?: string
        unit?: string
        default_price?: number | string
      }) => updatePriceItem(id, body),
      onSuccess: done,
    }),
    deleteItem: useMutation({
      mutationFn: (id: number) => deletePriceItem(id),
      onSuccess: done,
    }),
    bulkPrices: useMutation({
      mutationFn: (items: { id: number; default_price: number | string }[]) =>
        bulkUpdatePriceItems(items),
      onSuccess: done,
    }),
    createUnit: useMutation({
      mutationFn: createUnit,
      onSuccess: () => qc.invalidateQueries({ queryKey: ['units'] }),
    }),
  }
}
