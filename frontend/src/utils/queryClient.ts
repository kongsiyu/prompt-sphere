import { QueryClient, DefaultOptions } from '@tanstack/react-query';
import { handleError, logError, ErrorType } from './errorHandler';

/**
 * React Query 默认配置选项
 */
const defaultOptions: DefaultOptions = {
  queries: {
    // 默认缓存时间 5 分钟
    gcTime: 5 * 60 * 1000,
    // 数据过期时间 1 分钟
    staleTime: 1 * 60 * 1000,
    // 重试配置
    retry: (failureCount, error) => {
      const appError = handleError(error);

      // 对于认证错误、验证错误等不进行重试
      const nonRetryableErrors = [
        ErrorType.AUTH_ERROR,
        ErrorType.VALIDATION_ERROR,
        ErrorType.FORBIDDEN,
        ErrorType.NOT_FOUND
      ];

      if (nonRetryableErrors.includes(appError.type)) {
        return false;
      }

      // 最多重试 3 次
      return failureCount < 3;
    },
    // 重试延迟 (指数退避)
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    // 窗口重新获得焦点时重新获取数据
    refetchOnWindowFocus: true,
    // 网络重新连接时重新获取数据
    refetchOnReconnect: true,
    // 组件挂载时重新获取数据
    refetchOnMount: true,
  },
  mutations: {
    // 变更重试配置
    retry: (failureCount, error) => {
      const appError = handleError(error);

      // 只对网络错误和服务器错误进行重试
      const retryableErrors = [
        ErrorType.NETWORK_ERROR,
        ErrorType.SERVER_ERROR,
        ErrorType.RATE_LIMIT
      ];

      if (!retryableErrors.includes(appError.type)) {
        return false;
      }

      return failureCount < 2; // 变更操作最多重试 2 次
    },
    // 变更重试延迟
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
  },
};

/**
 * 创建 Query Client 实例
 */
export const queryClient = new QueryClient({
  defaultOptions,
  logger: {
    log: (message) => {
      if (process.env.NODE_ENV === 'development') {
        console.log('[React Query]', message);
      }
    },
    warn: (message) => {
      console.warn('[React Query]', message);
    },
    error: (message) => {
      const error = handleError(new Error(message));
      logError(error, { source: 'react-query' });
      console.error('[React Query]', message);
    },
  },
});

/**
 * Query Keys 工厂函数
 */
export const queryKeys = {
  // 认证相关
  auth: {
    all: ['auth'] as const,
    user: () => [...queryKeys.auth.all, 'user'] as const,
    profile: (userId?: string) => [...queryKeys.auth.all, 'profile', userId] as const,
  },

  // 提示词相关
  prompts: {
    all: ['prompts'] as const,
    lists: () => [...queryKeys.prompts.all, 'list'] as const,
    list: (filters: any) => [...queryKeys.prompts.lists(), filters] as const,
    details: () => [...queryKeys.prompts.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.prompts.details(), id] as const,
    search: (query: string) => [...queryKeys.prompts.all, 'search', query] as const,
  },

  // 分类相关
  categories: {
    all: ['categories'] as const,
    lists: () => [...queryKeys.categories.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.categories.all, 'detail', id] as const,
  },

  // 标签相关
  tags: {
    all: ['tags'] as const,
    lists: () => [...queryKeys.tags.all, 'list'] as const,
    popular: () => [...queryKeys.tags.all, 'popular'] as const,
  },

  // 收藏相关
  favorites: {
    all: ['favorites'] as const,
    lists: () => [...queryKeys.favorites.all, 'list'] as const,
    check: (promptId: string) => [...queryKeys.favorites.all, 'check', promptId] as const,
  },

  // 使用统计
  usage: {
    all: ['usage'] as const,
    stats: () => [...queryKeys.usage.all, 'stats'] as const,
    history: (userId?: string) => [...queryKeys.usage.all, 'history', userId] as const,
  },

  // 系统相关
  system: {
    all: ['system'] as const,
    health: () => [...queryKeys.system.all, 'health'] as const,
    config: () => [...queryKeys.system.all, 'config'] as const,
  },
} as const;

/**
 * 缓存标签枚举
 */
export enum CacheTag {
  AUTH = 'auth',
  PROMPTS = 'prompts',
  CATEGORIES = 'categories',
  TAGS = 'tags',
  FAVORITES = 'favorites',
  USAGE = 'usage',
  SYSTEM = 'system',
}

/**
 * 通过标签清除缓存
 */
export function invalidateByTag(tag: CacheTag): void {
  queryClient.invalidateQueries({
    predicate: (query) => {
      const queryKey = query.queryKey[0] as string;
      return queryKey.startsWith(tag);
    },
  });
}

/**
 * 清除所有缓存
 */
export function clearAllCache(): void {
  queryClient.clear();
}

/**
 * 预加载数据
 */
export function prefetchQuery<T>(
  queryKey: readonly unknown[],
  queryFn: () => Promise<T>,
  options?: {
    staleTime?: number;
    gcTime?: number;
  }
): Promise<void> {
  return queryClient.prefetchQuery({
    queryKey,
    queryFn,
    staleTime: options?.staleTime,
    gcTime: options?.gcTime,
  });
}

/**
 * 设置查询数据
 */
export function setQueryData<T>(
  queryKey: readonly unknown[],
  data: T | ((oldData?: T) => T)
): void {
  queryClient.setQueryData(queryKey, data);
}

/**
 * 获取查询数据
 */
export function getQueryData<T>(queryKey: readonly unknown[]): T | undefined {
  return queryClient.getQueryData(queryKey);
}

/**
 * 检查网络连接状态
 */
export function isOnline(): boolean {
  return navigator.onLine;
}

/**
 * 离线状态处理
 */
export function setupOfflineHandling(): void {
  // 监听网络状态变化
  window.addEventListener('online', () => {
    // 网络恢复时，重新获取过期的数据
    queryClient.resumePausedMutations();
    queryClient.invalidateQueries({
      predicate: (query) => query.isStale(),
    });
  });

  window.addEventListener('offline', () => {
    // 网络断开时暂停变更操作
    console.log('Network is offline. Mutations will be paused.');
  });
}

/**
 * 批量更新配置
 */
export interface BatchUpdateConfig {
  queries?: Array<{
    queryKey: readonly unknown[];
    data: any;
  }>;
  invalidate?: readonly unknown[][];
  remove?: readonly unknown[][];
}

/**
 * 批量更新缓存
 */
export function batchUpdateCache(config: BatchUpdateConfig): void {
  // 更新数据
  if (config.queries) {
    config.queries.forEach(({ queryKey, data }) => {
      setQueryData(queryKey, data);
    });
  }

  // 使缓存失效
  if (config.invalidate) {
    config.invalidate.forEach((queryKey) => {
      queryClient.invalidateQueries({ queryKey });
    });
  }

  // 移除缓存
  if (config.remove) {
    config.remove.forEach((queryKey) => {
      queryClient.removeQueries({ queryKey });
    });
  }
}

/**
 * 乐观更新工具函数
 */
export function optimisticUpdate<T>(
  queryKey: readonly unknown[],
  updater: (oldData?: T) => T,
  rollback?: T
): {
  commit: () => void;
  rollback: () => void;
} {
  const previousData = getQueryData<T>(queryKey);

  // 执行乐观更新
  setQueryData(queryKey, updater);

  return {
    commit: () => {
      // 提交更新，使缓存失效以获取最新数据
      queryClient.invalidateQueries({ queryKey });
    },
    rollback: () => {
      // 回滚到之前的数据
      setQueryData(queryKey, rollback ?? previousData);
    },
  };
}

/**
 * 监听缓存变化
 */
export function subscribeToCache<T>(
  queryKey: readonly unknown[],
  callback: (data?: T) => void
): () => void {
  return queryClient.getQueryCache().subscribe((event) => {
    if (event.query.queryKey.join('|') === queryKey.join('|')) {
      callback(event.query.state.data as T);
    }
  });
}

/**
 * 获取缓存统计信息
 */
export function getCacheStats(): {
  queryCount: number;
  activeQueryCount: number;
  staleQueryCount: number;
  inactiveQueryCount: number;
} {
  const cache = queryClient.getQueryCache();
  const queries = cache.getAll();

  return {
    queryCount: queries.length,
    activeQueryCount: queries.filter(q => q.getObserversCount() > 0).length,
    staleQueryCount: queries.filter(q => q.isStale()).length,
    inactiveQueryCount: queries.filter(q => q.isInactive()).length,
  };
}

/**
 * 开发环境缓存调试工具
 */
export const cacheDebugger = {
  logCacheState: () => {
    if (process.env.NODE_ENV === 'development') {
      const stats = getCacheStats();
      console.log('Cache Stats:', stats);
      console.log('All Queries:', queryClient.getQueryCache().getAll());
    }
  },

  logQueryState: (queryKey: readonly unknown[]) => {
    if (process.env.NODE_ENV === 'development') {
      const query = queryClient.getQueryCache().find({ queryKey });
      console.log(`Query [${queryKey.join(', ')}]:`, query?.state);
    }
  },

  clearQueryByKey: (queryKey: readonly unknown[]) => {
    queryClient.removeQueries({ queryKey });
    console.log(`Cleared query: [${queryKey.join(', ')}]`);
  },
};