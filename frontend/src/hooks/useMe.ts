import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getMe, patchMe, type Me, type MePatch } from '../api/me'

export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    staleTime: 60_000,
    retry: 1,
  })
}

export function useUpdateMe() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: MePatch) => patchMe(body),
    onSuccess: (data: Me) => qc.setQueryData(['me'], data),
  })
}
