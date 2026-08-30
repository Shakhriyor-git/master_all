import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  deleteProject,
  updateProject,
  type ProjectPatch,
} from '../api/projects'

export function useProjectMutations() {
  const qc = useQueryClient()
  const done = () => {
    qc.invalidateQueries({ queryKey: ['projects'] })
    qc.invalidateQueries({ queryKey: ['summary'] })
  }

  return {
    update: useMutation({
      mutationFn: ({ id, ...body }: { id: number } & ProjectPatch) =>
        updateProject(id, body),
      onSuccess: done,
    }),
    remove: useMutation({
      mutationFn: (id: number) => deleteProject(id),
      onSuccess: done,
    }),
  }
}
