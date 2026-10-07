import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError, queryString } from './client'
import type {
  Context,
  ContextInput,
  Opportunity,
  OpportunityFilters,
  Project,
  ProjectInput,
  Role,
  Run,
  User,
} from './types'

// --- sesión ---

export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: () =>
      api<User>('/auth/me').catch((error) => {
        if (error instanceof ApiError && error.status === 401) return null
        throw error
      }),
    staleTime: Infinity,
  })
}

export function useLogin() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (body: { email: string; password: string }) => api<User>('/auth/login', { method: 'POST', body }),
    onSuccess: (user) => client.setQueryData(['me'], user),
  })
}

export function useLogout() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: () => api<void>('/auth/logout', { method: 'POST' }),
    onSuccess: () => {
      client.clear()
      client.setQueryData(['me'], null)
    },
  })
}

// --- oportunidades ---

export function useOpportunities(filters: OpportunityFilters) {
  return useQuery({
    queryKey: ['opportunities', filters],
    queryFn: () => api<Opportunity[]>(`/opportunities${queryString(filters)}`),
    placeholderData: keepPreviousData,
  })
}

export function useOpportunity(id: string) {
  return useQuery({ queryKey: ['opportunity', id], queryFn: () => api<Opportunity>(`/opportunities/${id}`) })
}

export function useUpdateOpportunity() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string; review_status?: string; is_saved?: boolean }) =>
      api<Opportunity>(`/opportunities/${id}`, { method: 'PATCH', body }),
    onSuccess: (opportunity) => {
      client.setQueryData(['opportunity', opportunity.id], opportunity)
      client.invalidateQueries({ queryKey: ['opportunities'] })
    },
  })
}

// --- proyectos ---

export function useProjects() {
  return useQuery({ queryKey: ['projects'], queryFn: () => api<Project[]>('/projects') })
}

export function useSaveProject() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id?: string; body: ProjectInput }) =>
      id ? api<Project>(`/projects/${id}`, { method: 'PUT', body }) : api<Project>('/projects', { method: 'POST', body }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['projects'] }),
  })
}

export function useDeleteProject() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api<void>(`/projects/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ['projects'] })
      client.invalidateQueries({ queryKey: ['opportunities'] })
    },
  })
}

// --- contexto ---

export function useContextConfig() {
  return useQuery({ queryKey: ['context'], queryFn: () => api<Context>('/context') })
}

export function useSaveContext() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (body: ContextInput) => api<Context>('/context', { method: 'PUT', body }),
    onSuccess: (context) => client.setQueryData(['context'], context),
  })
}

// --- búsquedas ---

export function useRuns() {
  return useQuery({
    queryKey: ['runs'],
    queryFn: () => api<Run[]>('/runs'),
    // Poll only while a search is running.
    refetchInterval: (query) => (query.state.data?.some((run) => run.status === 'en_curso') ? 3000 : false),
  })
}

export function useStartRun() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: () => api<Run>('/runs', { method: 'POST' }),
    onSettled: () => client.invalidateQueries({ queryKey: ['runs'] }),
  })
}

// --- usuarios ---

export function useUsers() {
  return useQuery({ queryKey: ['users'], queryFn: () => api<User[]>('/users') })
}

export function useCreateUser() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (body: { email: string; name: string; password: string; role: Role }) =>
      api<User>('/users', { method: 'POST', body }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['users'] }),
  })
}

export function useUpdateUser() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string; role?: Role; is_active?: boolean; password?: string }) =>
      api<User>(`/users/${id}`, { method: 'PATCH', body }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['users'] }),
  })
}
