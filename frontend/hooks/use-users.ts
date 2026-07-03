'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { usersService } from '@/services/users'
import type { CreateUserInput, UpdateUserInput } from '@/services/users'

export function useUsers(includeInactive = false) {
  return useQuery({
    queryKey: ['users', includeInactive],
    queryFn: () => usersService.list(includeInactive),
  })
}

export function useCreateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateUserInput) => usersService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}

export function useUpdateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateUserInput }) =>
      usersService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}

export function useDeactivateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) => usersService.deactivate(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}

export function useClientPermissions(clientId: string) {
  return useQuery({
    queryKey: ['client-permissions', clientId],
    queryFn: () => usersService.listClientPermissions(clientId),
    enabled: !!clientId,
  })
}

export function useGrantPermission(clientId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, permesso }: { userId: string; permesso: 'lettura' | 'scrittura' }) =>
      usersService.grantPermission(clientId, userId, permesso),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-permissions', clientId] })
    },
  })
}

export function useRevokePermission(clientId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) => usersService.revokePermission(clientId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-permissions', clientId] })
    },
  })
}
