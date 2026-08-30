import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import {
  createEntry,
  deleteEntry,
  listEntries,
  updateEntry,
  type CreateEntryBody,
  type Entry,
  type EntryKind,
  type EntryPage,
  type PaidBy,
  type UpdateEntryBody,
} from '../api/entries'
import { getSummary } from '../api/projects'

interface Filter {
  projectId: number
  kind?: EntryKind
  paidBy?: PaidBy
}

export function useEntries({ projectId, kind, paidBy }: Filter) {
  return useInfiniteQuery({
    queryKey: ['entries', projectId, kind ?? 'all', paidBy ?? 'all'],
    queryFn: ({ pageParam }) =>
      listEntries({ projectId, kind, paidBy, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (last) =>
      last.page < last.pages ? last.page + 1 : undefined,
    enabled: projectId > 0,
  })
}

/** Dashboard uchun: bitta kind bo'yicha oxirgi 3 yozuv. */
export function useRecentEntries(projectId: number, kind: EntryKind) {
  return useQuery({
    queryKey: ['entries', projectId, kind, 'recent'],
    queryFn: () => listEntries({ projectId, kind, page: 1 }),
    enabled: projectId > 0,
    select: (d) => d.items.slice(0, 3),
  })
}

export function useSummary(projectId: number) {
  return useQuery({
    queryKey: ['summary', projectId],
    queryFn: () => getSummary(projectId),
    enabled: projectId > 0,
  })
}

function invalidateProject(
  qc: ReturnType<typeof useQueryClient>,
  projectId: number,
) {
  qc.invalidateQueries({ queryKey: ['entries', projectId] })
  qc.invalidateQueries({ queryKey: ['summary', projectId] })
}

export function useCreateEntry(projectId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: CreateEntryBody) => createEntry(projectId, body),
    onSuccess: () => invalidateProject(qc, projectId),
  })
}

export function useUpdateEntry(projectId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: UpdateEntryBody }) =>
      updateEntry(id, body),
    onSuccess: () => invalidateProject(qc, projectId),
  })
}

export function useDeleteEntry(projectId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteEntry(id),
    onMutate: async (id: number) => {
      await qc.cancelQueries({ queryKey: ['entries', projectId] })
      const snapshots = qc.getQueriesData<{ pages: EntryPage[] }>({
        queryKey: ['entries', projectId],
      })
      for (const [key, data] of snapshots) {
        if (!data) continue
        qc.setQueryData(key, {
          ...data,
          pages: data.pages.map((pg: EntryPage) => ({
            ...pg,
            items: pg.items.filter((e: Entry) => e.id !== id),
            total: Math.max(0, pg.total - 1),
          })),
        })
      }
      return { snapshots }
    },
    onError: (_e, _id, ctx) => {
      ctx?.snapshots.forEach(([key, data]) => qc.setQueryData(key, data))
    },
    onSettled: () => invalidateProject(qc, projectId),
  })
}
