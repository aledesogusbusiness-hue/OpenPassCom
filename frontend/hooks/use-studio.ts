'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { studioService } from '@/services/studio'
import type { CreateTaskInput, UpdateTaskInput } from '@/services/studio'

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: () => studioService.getDashboard(),
  })
}

export function useTasks() {
  return useQuery({
    queryKey: ['tasks'],
    queryFn: () => studioService.listTasks(),
  })
}

export function useCreateTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateTaskInput) => studioService.createTask(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  })
}

export function useUpdateTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateTaskInput }) =>
      studioService.updateTask(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useCompleteTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, completatoIl }: { id: string; completatoIl: string }) =>
      studioService.completeTask(id, completatoIl),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}
