import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';
import { getKit, getAvailableTools, listKits, searchKits } from '../lib/api';

// Query keys
export const kitKeys = {
  all: ['kits'] as const,
  lists: () => [...kitKeys.all, 'list'] as const,
  list: (filters: { query?: string; filter?: string }) => [...kitKeys.lists(), filters] as const,
  details: () => [...kitKeys.all, 'detail'] as const,
  detail: (slug: string) => [...kitKeys.details(), slug] as const,
};

export const toolKeys = {
  all: ['tools'] as const,
  available: () => [...toolKeys.all, 'available'] as const,
};

// Hook for kit list with caching
export function useKitList(query: string = '', filter: 'all' | 'mine' = 'all') {
  return useQuery({
    queryKey: kitKeys.list({ query, filter }),
    queryFn: async () => {
      if (query.trim() || filter === 'mine') {
        return searchKits(query, filter);
      }
      return listKits();
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

// Hook for kit detail with caching
export function useKitDetail(slug: string) {
  return useQuery({
    queryKey: kitKeys.detail(slug),
    queryFn: () => getKit(slug),
    staleTime: 1000 * 60 * 5, // 5 minutes - kit details don't change often
    enabled: !!slug,
  });
}

// Hook for prefetching kit details
export function usePrefetchKit() {
  const queryClient = useQueryClient();

  return useCallback(
    (slug: string) => {
      // Only prefetch if not already in cache
      if (!queryClient.getQueryData(kitKeys.detail(slug))) {
        queryClient.prefetchQuery({
          queryKey: kitKeys.detail(slug),
          queryFn: () => getKit(slug),
          staleTime: 1000 * 60 * 5,
        });
      }
    },
    [queryClient]
  );
}

// Hook for available tools - lazy loaded only when needed
export function useAvailableTools(enabled: boolean = false) {
  return useQuery({
    queryKey: toolKeys.available(),
    queryFn: async () => {
      const response = await getAvailableTools();
      return response.tools;
    },
    staleTime: 1000 * 60 * 10, // 10 minutes - tools don't change often
    enabled, // Only fetch when enabled (e.g., when owner opens add tool form)
  });
}

// Prefetch hook for kit list
export function usePrefetchKitList() {
  const queryClient = useQueryClient();

  return useCallback(
    (query: string = '', filter: 'all' | 'mine' = 'all') => {
      const key = kitKeys.list({ query, filter });
      if (!queryClient.getQueryData(key)) {
        queryClient.prefetchQuery({
          queryKey: key,
          queryFn: async () => {
            if (query.trim() || filter === 'mine') {
              return searchKits(query, filter);
            }
            return listKits();
          },
          staleTime: 1000 * 60 * 2,
        });
      }
    },
    [queryClient]
  );
}
