import { useInfiniteQuery } from '@tanstack/react-query'
import { listTimeline, type TimelineKind } from '../api/timeline'

export function useTimeline(projectId: number, kind?: TimelineKind) {
  return useInfiniteQuery({
    queryKey: ['timeline', projectId, kind ?? 'all'],
    queryFn: ({ pageParam }) =>
      listTimeline({ projectId, kind, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (last) =>
      last.page < last.pages ? last.page + 1 : undefined,
    enabled: projectId > 0,
  })
}
