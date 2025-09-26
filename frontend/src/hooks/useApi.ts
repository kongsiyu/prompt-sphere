import { useMutation, useQuery, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { useCallback } from 'react';
import {
  promptsApi,
  categoriesApi,
  tagsApi,
  favoritesApi,
  filesApi,
  systemApi,
} from '../services/api';
import { queryKeys, invalidateByTag, CacheTag } from '../utils/queryClient';
import { useAppStore } from '../stores/appStore';
import { handleError } from '../utils/errorHandler';
import type {
  Prompt,
  CreatePromptRequest,
  UpdatePromptRequest,
  PromptSearchParams,
  PaginatedResponse,
  Category,
  Tag,
  FileUploadResponse,
  SystemHealth,
} from '../types/api';

/**
 * 提示词相关的API Hooks
 */

/**
 * 获取提示词列表
 */
export function usePrompts(params?: PromptSearchParams) {
  return useQuery({
    queryKey: queryKeys.prompts.list(params || {}),
    queryFn: () => promptsApi.getPrompts(params),
    staleTime: 5 * 60 * 1000, // 5分钟
    gcTime: 10 * 60 * 1000, // 10分钟
  });
}

/**
 * 获取提示词详情
 */
export function usePrompt(id: string, enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.prompts.detail(id),
    queryFn: () => promptsApi.getPrompt(id),
    enabled: !!id && enabled,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000, // 详情缓存更久
  });
}

/**
 * 无限滚动获取提示词列表
 */
export function useInfinitePrompts(params?: PromptSearchParams) {
  return useInfiniteQuery({
    queryKey: queryKeys.prompts.list(params || {}),
    queryFn: ({ pageParam = 1 }) =>
      promptsApi.getPrompts({ ...params, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage: PaginatedResponse<Prompt>) => {
      const { page, pages } = lastPage.meta;
      return page < pages ? page + 1 : undefined;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 搜索提示词
 */
export function useSearchPrompts(query: string, params?: PromptSearchParams, enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.prompts.search(query),
    queryFn: () => promptsApi.searchPrompts(query, params),
    enabled: !!query.trim() && enabled,
    staleTime: 2 * 60 * 1000, // 搜索结果缓存较短
  });
}

/**
 * 获取热门提示词
 */
export function usePopularPrompts(limit: number = 10) {
  return useQuery({
    queryKey: [...queryKeys.prompts.all, 'popular', limit],
    queryFn: () => promptsApi.getPopularPrompts(limit),
    staleTime: 10 * 60 * 1000, // 热门内容缓存较长
  });
}

/**
 * 获取最新提示词
 */
export function useLatestPrompts(limit: number = 10) {
  return useQuery({
    queryKey: [...queryKeys.prompts.all, 'latest', limit],
    queryFn: () => promptsApi.getLatestPrompts(limit),
    staleTime: 2 * 60 * 1000, // 最新内容缓存较短
  });
}

/**
 * 创建提示词
 */
export function useCreatePrompt() {
  const queryClient = useQueryClient();
  const addNotification = useAppStore(state => state.actions.addNotification);

  return useMutation({
    mutationFn: (data: CreatePromptRequest) => promptsApi.createPrompt(data),
    onSuccess: (newPrompt) => {
      // 使相关查询无效
      invalidateByTag(CacheTag.PROMPTS);

      // 乐观更新：将新提示词添加到列表缓存的开头
      queryClient.setQueriesData(
        { queryKey: queryKeys.prompts.lists() },
        (oldData: any) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            data: [newPrompt, ...oldData.data],
            meta: {
              ...oldData.meta,
              total: oldData.meta.total + 1,
            },
          };
        }
      );

      addNotification({
        type: 'success',
        title: '创建成功',
        message: '提示词已成功创建',
      });
    },
    onError: (error) => {
      const appError = handleError(error);
      addNotification({
        type: 'error',
        title: '创建失败',
        message: appError.message,
      });
    },
  });
}

/**
 * 更新提示词
 */
export function useUpdatePrompt() {
  const queryClient = useQueryClient();
  const addNotification = useAppStore(state => state.actions.addNotification);

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdatePromptRequest }) =>
      promptsApi.updatePrompt(id, data),
    onSuccess: (updatedPrompt, variables) => {
      // 更新详情缓存
      queryClient.setQueryData(queryKeys.prompts.detail(variables.id), updatedPrompt);

      // 更新列表缓存
      queryClient.setQueriesData(
        { queryKey: queryKeys.prompts.lists() },
        (oldData: any) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            data: oldData.data.map((prompt: Prompt) =>
              prompt.id === variables.id ? updatedPrompt : prompt
            ),
          };
        }
      );

      addNotification({
        type: 'success',
        title: '更新成功',
        message: '提示词已成功更新',
      });
    },
    onError: (error) => {
      const appError = handleError(error);
      addNotification({
        type: 'error',
        title: '更新失败',
        message: appError.message,
      });
    },
  });
}

/**
 * 删除提示词
 */
export function useDeletePrompt() {
  const queryClient = useQueryClient();
  const addNotification = useAppStore(state => state.actions.addNotification);

  return useMutation({
    mutationFn: (id: string) => promptsApi.deletePrompt(id),
    onSuccess: (_, deletedId) => {
      // 移除详情缓存
      queryClient.removeQueries({ queryKey: queryKeys.prompts.detail(deletedId) });

      // 更新列表缓存
      queryClient.setQueriesData(
        { queryKey: queryKeys.prompts.lists() },
        (oldData: any) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            data: oldData.data.filter((prompt: Prompt) => prompt.id !== deletedId),
            meta: {
              ...oldData.meta,
              total: Math.max(0, oldData.meta.total - 1),
            },
          };
        }
      );

      addNotification({
        type: 'success',
        title: '删除成功',
        message: '提示词已成功删除',
      });
    },
    onError: (error) => {
      const appError = handleError(error);
      addNotification({
        type: 'error',
        title: '删除失败',
        message: appError.message,
      });
    },
  });
}

/**
 * 分类相关的API Hooks
 */

/**
 * 获取分类列表
 */
export function useCategories() {
  return useQuery({
    queryKey: queryKeys.categories.lists(),
    queryFn: () => categoriesApi.getCategories(),
    staleTime: 30 * 60 * 1000, // 分类不常变化，缓存较长
    gcTime: 60 * 60 * 1000,
  });
}

/**
 * 获取分类详情
 */
export function useCategory(id: string, enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.categories.detail(id),
    queryFn: () => categoriesApi.getCategory(id),
    enabled: !!id && enabled,
    staleTime: 30 * 60 * 1000,
  });
}

/**
 * 标签相关的API Hooks
 */

/**
 * 获取标签列表
 */
export function useTags() {
  return useQuery({
    queryKey: queryKeys.tags.lists(),
    queryFn: () => tagsApi.getTags(),
    staleTime: 15 * 60 * 1000,
  });
}

/**
 * 获取热门标签
 */
export function usePopularTags(limit: number = 20) {
  return useQuery({
    queryKey: queryKeys.tags.popular(),
    queryFn: () => tagsApi.getPopularTags(limit),
    staleTime: 15 * 60 * 1000,
  });
}

/**
 * 收藏相关的API Hooks
 */

/**
 * 获取收藏列表
 */
export function useFavorites() {
  return useQuery({
    queryKey: queryKeys.favorites.lists(),
    queryFn: () => favoritesApi.getFavorites(),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 检查是否已收藏
 */
export function useIsFavorited(promptId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.favorites.check(promptId),
    queryFn: () => favoritesApi.isFavorited(promptId),
    enabled: !!promptId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 添加收藏
 */
export function useAddFavorite() {
  const queryClient = useQueryClient();
  const addNotification = useAppStore(state => state.actions.addNotification);

  return useMutation({
    mutationFn: (promptId: string) => favoritesApi.addFavorite(promptId),
    onMutate: async (promptId) => {
      // 乐观更新：立即标记为已收藏
      await queryClient.cancelQueries({ queryKey: queryKeys.favorites.check(promptId) });
      const previousValue = queryClient.getQueryData(queryKeys.favorites.check(promptId));
      queryClient.setQueryData(queryKeys.favorites.check(promptId), true);
      return { previousValue, promptId };
    },
    onSuccess: (_, promptId) => {
      // 使收藏列表缓存无效
      invalidateByTag(CacheTag.FAVORITES);

      addNotification({
        type: 'success',
        title: '收藏成功',
        message: '已添加到收藏夹',
      });
    },
    onError: (error, _, context) => {
      // 回滚乐观更新
      if (context) {
        queryClient.setQueryData(
          queryKeys.favorites.check(context.promptId),
          context.previousValue
        );
      }

      const appError = handleError(error);
      addNotification({
        type: 'error',
        title: '收藏失败',
        message: appError.message,
      });
    },
  });
}

/**
 * 取消收藏
 */
export function useRemoveFavorite() {
  const queryClient = useQueryClient();
  const addNotification = useAppStore(state => state.actions.addNotification);

  return useMutation({
    mutationFn: (promptId: string) => favoritesApi.removeFavorite(promptId),
    onMutate: async (promptId) => {
      // 乐观更新：立即标记为未收藏
      await queryClient.cancelQueries({ queryKey: queryKeys.favorites.check(promptId) });
      const previousValue = queryClient.getQueryData(queryKeys.favorites.check(promptId));
      queryClient.setQueryData(queryKeys.favorites.check(promptId), false);
      return { previousValue, promptId };
    },
    onSuccess: (_, promptId) => {
      // 使收藏列表缓存无效
      invalidateByTag(CacheTag.FAVORITES);

      addNotification({
        type: 'success',
        title: '取消收藏',
        message: '已从收藏夹移除',
      });
    },
    onError: (error, _, context) => {
      // 回滚乐观更新
      if (context) {
        queryClient.setQueryData(
          queryKeys.favorites.check(context.promptId),
          context.previousValue
        );
      }

      const appError = handleError(error);
      addNotification({
        type: 'error',
        title: '操作失败',
        message: appError.message,
      });
    },
  });
}

/**
 * 收藏切换Hook
 */
export function useFavoriteToggle(promptId: string) {
  const { data: isFavorited, isLoading: isCheckingFavorite } = useIsFavorited(promptId);
  const addFavorite = useAddFavorite();
  const removeFavorite = useRemoveFavorite();

  const toggle = useCallback(() => {
    if (isFavorited) {
      removeFavorite.mutate(promptId);
    } else {
      addFavorite.mutate(promptId);
    }
  }, [isFavorited, addFavorite, removeFavorite, promptId]);

  return {
    isFavorited: !!isFavorited,
    isLoading: isCheckingFavorite || addFavorite.isPending || removeFavorite.isPending,
    toggle,
    error: addFavorite.error || removeFavorite.error,
  };
}

/**
 * 文件上传相关的API Hooks
 */

/**
 * 上传文件
 */
export function useUploadFile() {
  const addNotification = useAppStore(state => state.actions.addNotification);

  return useMutation({
    mutationFn: ({ file, onProgress }: { file: File; onProgress?: (progress: number) => void }) =>
      filesApi.uploadFile(file, onProgress),
    onSuccess: (result: FileUploadResponse) => {
      addNotification({
        type: 'success',
        title: '上传成功',
        message: `文件 ${result.originalName} 上传成功`,
      });
    },
    onError: (error) => {
      const appError = handleError(error);
      addNotification({
        type: 'error',
        title: '上传失败',
        message: appError.message,
      });
    },
  });
}

/**
 * 删除文件
 */
export function useDeleteFile() {
  const addNotification = useAppStore(state => state.actions.addNotification);

  return useMutation({
    mutationFn: (id: string) => filesApi.deleteFile(id),
    onSuccess: () => {
      addNotification({
        type: 'success',
        title: '删除成功',
        message: '文件已成功删除',
      });
    },
    onError: (error) => {
      const appError = handleError(error);
      addNotification({
        type: 'error',
        title: '删除失败',
        message: appError.message,
      });
    },
  });
}

/**
 * 系统相关的API Hooks
 */

/**
 * 获取系统健康状态
 */
export function useSystemHealth() {
  return useQuery({
    queryKey: queryKeys.system.health(),
    queryFn: () => systemApi.getHealth(),
    staleTime: 30 * 1000, // 30秒
    gcTime: 2 * 60 * 1000,
    refetchInterval: 60 * 1000, // 每分钟自动刷新
    retry: 1, // 健康检查失败时只重试1次
  });
}

/**
 * 获取系统配置
 */
export function useSystemConfig() {
  return useQuery({
    queryKey: queryKeys.system.config(),
    queryFn: () => systemApi.getConfig(),
    staleTime: 60 * 60 * 1000, // 配置不常变化，缓存1小时
    gcTime: 2 * 60 * 60 * 1000,
  });
}

/**
 * 批量操作Hook
 */
export function useBatchOperations() {
  const queryClient = useQueryClient();
  const addNotification = useAppStore(state => state.actions.addNotification);

  const batchDeletePrompts = useMutation({
    mutationFn: async (ids: string[]) => {
      const results = await Promise.allSettled(
        ids.map(id => promptsApi.deletePrompt(id))
      );
      return results;
    },
    onSuccess: (results, ids) => {
      const successCount = results.filter(result => result.status === 'fulfilled').length;
      const failureCount = results.length - successCount;

      // 使提示词缓存无效
      invalidateByTag(CacheTag.PROMPTS);

      if (failureCount === 0) {
        addNotification({
          type: 'success',
          title: '批量删除成功',
          message: `已成功删除 ${successCount} 个提示词`,
        });
      } else {
        addNotification({
          type: 'warning',
          title: '部分删除失败',
          message: `成功删除 ${successCount} 个，失败 ${failureCount} 个`,
        });
      }
    },
    onError: (error) => {
      const appError = handleError(error);
      addNotification({
        type: 'error',
        title: '批量删除失败',
        message: appError.message,
      });
    },
  });

  return {
    batchDeletePrompts,
  };
}

/**
 * 数据预加载Hook
 */
export function useDataPrefetch() {
  const queryClient = useQueryClient();

  const prefetchPrompts = useCallback((params?: PromptSearchParams) => {
    return queryClient.prefetchQuery({
      queryKey: queryKeys.prompts.list(params || {}),
      queryFn: () => promptsApi.getPrompts(params),
      staleTime: 5 * 60 * 1000,
    });
  }, [queryClient]);

  const prefetchPrompt = useCallback((id: string) => {
    return queryClient.prefetchQuery({
      queryKey: queryKeys.prompts.detail(id),
      queryFn: () => promptsApi.getPrompt(id),
      staleTime: 5 * 60 * 1000,
    });
  }, [queryClient]);

  const prefetchCategories = useCallback(() => {
    return queryClient.prefetchQuery({
      queryKey: queryKeys.categories.lists(),
      queryFn: () => categoriesApi.getCategories(),
      staleTime: 30 * 60 * 1000,
    });
  }, [queryClient]);

  return {
    prefetchPrompts,
    prefetchPrompt,
    prefetchCategories,
  };
}

/**
 * 缓存管理Hook
 */
export function useCacheManager() {
  const queryClient = useQueryClient();

  const invalidatePrompts = useCallback(() => {
    invalidateByTag(CacheTag.PROMPTS);
  }, []);

  const invalidateFavorites = useCallback(() => {
    invalidateByTag(CacheTag.FAVORITES);
  }, []);

  const clearAllCache = useCallback(() => {
    queryClient.clear();
  }, [queryClient]);

  const removePromptFromCache = useCallback((id: string) => {
    queryClient.removeQueries({ queryKey: queryKeys.prompts.detail(id) });
  }, [queryClient]);

  return {
    invalidatePrompts,
    invalidateFavorites,
    clearAllCache,
    removePromptFromCache,
  };
}

/**
 * 实时数据同步Hook
 */
export function useRealtimeSync() {
  const queryClient = useQueryClient();

  const syncPrompt = useCallback((prompt: Prompt) => {
    // 更新详情缓存
    queryClient.setQueryData(queryKeys.prompts.detail(prompt.id), prompt);

    // 更新列表缓存
    queryClient.setQueriesData(
      { queryKey: queryKeys.prompts.lists() },
      (oldData: any) => {
        if (!oldData) return oldData;
        return {
          ...oldData,
          data: oldData.data.map((p: Prompt) =>
            p.id === prompt.id ? prompt : p
          ),
        };
      }
    );
  }, [queryClient]);

  const syncPromptDelete = useCallback((promptId: string) => {
    // 移除详情缓存
    queryClient.removeQueries({ queryKey: queryKeys.prompts.detail(promptId) });

    // 更新列表缓存
    queryClient.setQueriesData(
      { queryKey: queryKeys.prompts.lists() },
      (oldData: any) => {
        if (!oldData) return oldData;
        return {
          ...oldData,
          data: oldData.data.filter((p: Prompt) => p.id !== promptId),
          meta: {
            ...oldData.meta,
            total: Math.max(0, oldData.meta.total - 1),
          },
        };
      }
    );
  }, [queryClient]);

  return {
    syncPrompt,
    syncPromptDelete,
  };
}