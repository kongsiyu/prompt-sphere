import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type { AppConfig, NotificationMessage } from '../types/api';

/**
 * 主题类型
 */
export type Theme = 'light' | 'dark' | 'system';

/**
 * 语言类型
 */
export type Language = 'zh' | 'en';

/**
 * 布局类型
 */
export type Layout = 'sidebar' | 'topbar' | 'compact';

/**
 * 通知位置
 */
export type NotificationPosition = 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';

/**
 * 应用偏好设置
 */
export interface AppPreferences {
  theme: Theme;
  language: Language;
  layout: Layout;

  // UI设置
  sidebarCollapsed: boolean;
  showWelcomeMessage: boolean;
  enableAnimations: boolean;
  enableSounds: boolean;

  // 通知设置
  notifications: {
    enabled: boolean;
    position: NotificationPosition;
    duration: number; // 毫秒
    maxVisible: number;
    enableDesktop: boolean;
    enableEmail: boolean;
  };

  // 编辑器设置
  editor: {
    fontSize: number;
    fontFamily: string;
    tabSize: number;
    wordWrap: boolean;
    lineNumbers: boolean;
    minimap: boolean;
    theme: string;
  };

  // 性能设置
  performance: {
    enableVirtualization: boolean;
    itemsPerPage: number;
    enableLazyLoading: boolean;
    cacheSize: number; // MB
  };
}

/**
 * 应用状态接口
 */
export interface AppState {
  // 基础状态
  isInitialized: boolean;
  isOnline: boolean;
  config: AppConfig | null;

  // 偏好设置
  preferences: AppPreferences;

  // 通知系统
  notifications: NotificationMessage[];

  // UI状态
  loading: {
    global: boolean;
    components: Record<string, boolean>;
  };

  // 模态框状态
  modals: {
    settings: boolean;
    about: boolean;
    shortcuts: boolean;
    feedback: boolean;
    [key: string]: boolean;
  };

  // 搜索状态
  search: {
    query: string;
    isOpen: boolean;
    recentSearches: string[];
    suggestions: string[];
  };

  // 错误状态
  globalError: {
    hasError: boolean;
    message: string;
    details?: any;
  };

  // 性能监控
  performance: {
    renderTime: number;
    memoryUsage: number;
    cacheHitRate: number;
  };

  // 操作方法
  actions: {
    // 初始化
    initialize: () => Promise<void>;
    setConfig: (config: AppConfig) => void;
    setOnlineStatus: (isOnline: boolean) => void;

    // 偏好设置
    updatePreferences: (preferences: Partial<AppPreferences>) => void;
    resetPreferences: () => void;

    // 主题相关
    setTheme: (theme: Theme) => void;
    toggleTheme: () => void;

    // 语言相关
    setLanguage: (language: Language) => void;

    // 布局相关
    setLayout: (layout: Layout) => void;
    toggleSidebar: () => void;
    setSidebarCollapsed: (collapsed: boolean) => void;

    // 通知系统
    addNotification: (notification: Omit<NotificationMessage, 'id' | 'createdAt' | 'read'>) => string;
    removeNotification: (id: string) => void;
    markNotificationRead: (id: string) => void;
    clearNotifications: () => void;
    clearReadNotifications: () => void;

    // 加载状态
    setGlobalLoading: (loading: boolean) => void;
    setComponentLoading: (component: string, loading: boolean) => void;

    // 模态框控制
    openModal: (modal: string) => void;
    closeModal: (modal: string) => void;
    toggleModal: (modal: string) => void;
    closeAllModals: () => void;

    // 搜索相关
    setSearchQuery: (query: string) => void;
    setSearchOpen: (open: boolean) => void;
    addRecentSearch: (query: string) => void;
    clearRecentSearches: () => void;
    setSuggestions: (suggestions: string[]) => void;

    // 错误处理
    setGlobalError: (message: string, details?: any) => void;
    clearGlobalError: () => void;

    // 性能监控
    updatePerformanceMetrics: (metrics: Partial<AppState['performance']>) => void;

    // 实用工具
    exportSettings: () => string;
    importSettings: (settings: string) => void;
    resetApp: () => void;
  };
}

/**
 * 默认偏好设置
 */
const defaultPreferences: AppPreferences = {
  theme: 'system',
  language: 'zh',
  layout: 'sidebar',

  sidebarCollapsed: false,
  showWelcomeMessage: true,
  enableAnimations: true,
  enableSounds: false,

  notifications: {
    enabled: true,
    position: 'top-right',
    duration: 5000,
    maxVisible: 5,
    enableDesktop: true,
    enableEmail: false,
  },

  editor: {
    fontSize: 14,
    fontFamily: 'JetBrains Mono, Consolas, Monaco, monospace',
    tabSize: 2,
    wordWrap: true,
    lineNumbers: true,
    minimap: true,
    theme: 'vs-dark',
  },

  performance: {
    enableVirtualization: true,
    itemsPerPage: 20,
    enableLazyLoading: true,
    cacheSize: 100,
  },
};

/**
 * 初始状态
 */
const initialState: Omit<AppState, 'actions'> = {
  isInitialized: false,
  isOnline: navigator.onLine,
  config: null,

  preferences: defaultPreferences,

  notifications: [],

  loading: {
    global: false,
    components: {},
  },

  modals: {
    settings: false,
    about: false,
    shortcuts: false,
    feedback: false,
  },

  search: {
    query: '',
    isOpen: false,
    recentSearches: [],
    suggestions: [],
  },

  globalError: {
    hasError: false,
    message: '',
  },

  performance: {
    renderTime: 0,
    memoryUsage: 0,
    cacheHitRate: 0,
  },
};

/**
 * 持久化配置
 */
const persistConfig = {
  name: 'app-store',
  storage: createJSONStorage(() => localStorage),
  partialize: (state: AppState) => ({
    preferences: state.preferences,
    search: {
      recentSearches: state.search.recentSearches,
    },
  }),
  version: 1,
  migrate: (persistedState: any, version: number) => {
    if (version < 1) {
      return {
        ...persistedState,
        preferences: { ...defaultPreferences, ...persistedState.preferences },
      };
    }
    return persistedState;
  },
};

/**
 * 创建应用存储
 */
export const useAppStore = create<AppState>()(
  subscribeWithSelector(
    persist(
      immer((set, get) => ({
        ...initialState,

        actions: {
          /**
           * 初始化应用
           */
          initialize: async () => {
            try {
              // 设置在线状态监听器
              const updateOnlineStatus = () => {
                set((state) => {
                  state.isOnline = navigator.onLine;
                });
              };

              window.addEventListener('online', updateOnlineStatus);
              window.addEventListener('offline', updateOnlineStatus);

              // 设置性能监控
              if ('memory' in performance) {
                const updateMemoryUsage = () => {
                  const memory = (performance as any).memory;
                  set((state) => {
                    state.performance.memoryUsage = memory.usedJSHeapSize / 1024 / 1024; // MB
                  });
                };

                setInterval(updateMemoryUsage, 30000); // 30秒更新一次
              }

              // 应用主题
              get().actions.setTheme(get().preferences.theme);

              set((state) => {
                state.isInitialized = true;
              });
            } catch (error) {
              console.error('应用初始化失败:', error);
            }
          },

          /**
           * 设置配置
           */
          setConfig: (config: AppConfig) => {
            set((state) => {
              state.config = config;
            });
          },

          /**
           * 设置在线状态
           */
          setOnlineStatus: (isOnline: boolean) => {
            set((state) => {
              state.isOnline = isOnline;
            });
          },

          /**
           * 更新偏好设置
           */
          updatePreferences: (preferences: Partial<AppPreferences>) => {
            set((state) => {
              state.preferences = { ...state.preferences, ...preferences };
            });
          },

          /**
           * 重置偏好设置
           */
          resetPreferences: () => {
            set((state) => {
              state.preferences = { ...defaultPreferences };
            });
          },

          /**
           * 设置主题
           */
          setTheme: (theme: Theme) => {
            set((state) => {
              state.preferences.theme = theme;
            });

            // 应用主题到DOM
            const root = document.documentElement;
            if (theme === 'system') {
              const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
              root.classList.toggle('dark', prefersDark);
            } else {
              root.classList.toggle('dark', theme === 'dark');
            }
          },

          /**
           * 切换主题
           */
          toggleTheme: () => {
            const currentTheme = get().preferences.theme;
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            get().actions.setTheme(newTheme);
          },

          /**
           * 设置语言
           */
          setLanguage: (language: Language) => {
            set((state) => {
              state.preferences.language = language;
            });

            // 更新HTML语言属性
            document.documentElement.lang = language;
          },

          /**
           * 设置布局
           */
          setLayout: (layout: Layout) => {
            set((state) => {
              state.preferences.layout = layout;
            });
          },

          /**
           * 切换侧边栏
           */
          toggleSidebar: () => {
            set((state) => {
              state.preferences.sidebarCollapsed = !state.preferences.sidebarCollapsed;
            });
          },

          /**
           * 设置侧边栏折叠状态
           */
          setSidebarCollapsed: (collapsed: boolean) => {
            set((state) => {
              state.preferences.sidebarCollapsed = collapsed;
            });
          },

          /**
           * 添加通知
           */
          addNotification: (notification: Omit<NotificationMessage, 'id' | 'createdAt' | 'read'>) => {
            const id = `notification_${Date.now()}_${Math.random().toString(36).substring(2)}`;
            const newNotification: NotificationMessage = {
              ...notification,
              id,
              createdAt: new Date().toISOString(),
              read: false,
            };

            set((state) => {
              state.notifications.unshift(newNotification);

              // 限制通知数量
              const maxVisible = state.preferences.notifications.maxVisible;
              if (state.notifications.length > maxVisible * 2) {
                state.notifications = state.notifications.slice(0, maxVisible * 2);
              }
            });

            // 自动删除通知
            if (get().preferences.notifications.duration > 0) {
              setTimeout(() => {
                get().actions.removeNotification(id);
              }, get().preferences.notifications.duration);
            }

            // 桌面通知
            if (get().preferences.notifications.enableDesktop && 'Notification' in window) {
              if (Notification.permission === 'granted') {
                new Notification(notification.title, {
                  body: notification.message,
                  icon: '/favicon.ico',
                });
              }
            }

            return id;
          },

          /**
           * 移除通知
           */
          removeNotification: (id: string) => {
            set((state) => {
              state.notifications = state.notifications.filter(n => n.id !== id);
            });
          },

          /**
           * 标记通知已读
           */
          markNotificationRead: (id: string) => {
            set((state) => {
              const notification = state.notifications.find(n => n.id === id);
              if (notification) {
                notification.read = true;
              }
            });
          },

          /**
           * 清除所有通知
           */
          clearNotifications: () => {
            set((state) => {
              state.notifications = [];
            });
          },

          /**
           * 清除已读通知
           */
          clearReadNotifications: () => {
            set((state) => {
              state.notifications = state.notifications.filter(n => !n.read);
            });
          },

          /**
           * 设置全局加载状态
           */
          setGlobalLoading: (loading: boolean) => {
            set((state) => {
              state.loading.global = loading;
            });
          },

          /**
           * 设置组件加载状态
           */
          setComponentLoading: (component: string, loading: boolean) => {
            set((state) => {
              if (loading) {
                state.loading.components[component] = true;
              } else {
                delete state.loading.components[component];
              }
            });
          },

          /**
           * 打开模态框
           */
          openModal: (modal: string) => {
            set((state) => {
              state.modals[modal] = true;
            });
          },

          /**
           * 关闭模态框
           */
          closeModal: (modal: string) => {
            set((state) => {
              state.modals[modal] = false;
            });
          },

          /**
           * 切换模态框
           */
          toggleModal: (modal: string) => {
            set((state) => {
              state.modals[modal] = !state.modals[modal];
            });
          },

          /**
           * 关闭所有模态框
           */
          closeAllModals: () => {
            set((state) => {
              Object.keys(state.modals).forEach(modal => {
                state.modals[modal] = false;
              });
            });
          },

          /**
           * 设置搜索查询
           */
          setSearchQuery: (query: string) => {
            set((state) => {
              state.search.query = query;
            });
          },

          /**
           * 设置搜索打开状态
           */
          setSearchOpen: (open: boolean) => {
            set((state) => {
              state.search.isOpen = open;
            });
          },

          /**
           * 添加最近搜索
           */
          addRecentSearch: (query: string) => {
            if (!query.trim()) return;

            set((state) => {
              // 移除重复项
              state.search.recentSearches = state.search.recentSearches.filter(
                search => search.toLowerCase() !== query.toLowerCase()
              );

              // 添加到开头
              state.search.recentSearches.unshift(query.trim());

              // 限制数量
              if (state.search.recentSearches.length > 10) {
                state.search.recentSearches = state.search.recentSearches.slice(0, 10);
              }
            });
          },

          /**
           * 清除最近搜索
           */
          clearRecentSearches: () => {
            set((state) => {
              state.search.recentSearches = [];
            });
          },

          /**
           * 设置搜索建议
           */
          setSuggestions: (suggestions: string[]) => {
            set((state) => {
              state.search.suggestions = suggestions;
            });
          },

          /**
           * 设置全局错误
           */
          setGlobalError: (message: string, details?: any) => {
            set((state) => {
              state.globalError = {
                hasError: true,
                message,
                details,
              };
            });
          },

          /**
           * 清除全局错误
           */
          clearGlobalError: () => {
            set((state) => {
              state.globalError = {
                hasError: false,
                message: '',
              };
            });
          },

          /**
           * 更新性能指标
           */
          updatePerformanceMetrics: (metrics: Partial<AppState['performance']>) => {
            set((state) => {
              state.performance = { ...state.performance, ...metrics };
            });
          },

          /**
           * 导出设置
           */
          exportSettings: (): string => {
            const state = get();
            const settings = {
              preferences: state.preferences,
              search: {
                recentSearches: state.search.recentSearches,
              },
            };
            return JSON.stringify(settings, null, 2);
          },

          /**
           * 导入设置
           */
          importSettings: (settings: string) => {
            try {
              const parsedSettings = JSON.parse(settings);

              set((state) => {
                if (parsedSettings.preferences) {
                  state.preferences = { ...defaultPreferences, ...parsedSettings.preferences };
                }
                if (parsedSettings.search?.recentSearches) {
                  state.search.recentSearches = parsedSettings.search.recentSearches;
                }
              });

              // 重新应用主题
              get().actions.setTheme(get().preferences.theme);

              get().actions.addNotification({
                type: 'success',
                title: '导入成功',
                message: '设置已成功导入',
              });
            } catch (error) {
              get().actions.addNotification({
                type: 'error',
                title: '导入失败',
                message: '设置文件格式无效',
              });
            }
          },

          /**
           * 重置应用
           */
          resetApp: () => {
            set(() => ({ ...initialState }));
            localStorage.removeItem('app-store');
            get().actions.addNotification({
              type: 'info',
              title: '应用已重置',
              message: '所有设置已恢复为默认值',
            });
          },
        },
      })),
      persistConfig
    )
  )
);

/**
 * 订阅主题变化
 */
useAppStore.subscribe(
  (state) => state.preferences.theme,
  (theme) => {
    // 监听系统主题变化
    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = (e: MediaQueryListEvent) => {
        document.documentElement.classList.toggle('dark', e.matches);
      };

      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }
);

/**
 * 选择器函数
 */
export const appSelectors = {
  // 基础状态
  isInitialized: (state: AppState) => state.isInitialized,
  isOnline: (state: AppState) => state.isOnline,
  config: (state: AppState) => state.config,

  // 偏好设置
  preferences: (state: AppState) => state.preferences,
  theme: (state: AppState) => state.preferences.theme,
  language: (state: AppState) => state.preferences.language,
  layout: (state: AppState) => state.preferences.layout,
  sidebarCollapsed: (state: AppState) => state.preferences.sidebarCollapsed,

  // 通知
  notifications: (state: AppState) => state.notifications,
  unreadNotifications: (state: AppState) => state.notifications.filter(n => !n.read),
  notificationCount: (state: AppState) => state.notifications.filter(n => !n.read).length,

  // 加载状态
  isGlobalLoading: (state: AppState) => state.loading.global,
  componentLoadingStates: (state: AppState) => state.loading.components,

  // 模态框
  modals: (state: AppState) => state.modals,

  // 搜索
  searchQuery: (state: AppState) => state.search.query,
  isSearchOpen: (state: AppState) => state.search.isOpen,
  recentSearches: (state: AppState) => state.search.recentSearches,
  searchSuggestions: (state: AppState) => state.search.suggestions,

  // 错误状态
  globalError: (state: AppState) => state.globalError,
  hasGlobalError: (state: AppState) => state.globalError.hasError,

  // 性能指标
  performance: (state: AppState) => state.performance,

  // 动作
  actions: (state: AppState) => state.actions,
};

/**
 * Hook 形式的选择器
 */
export const useAppActions = () => useAppStore(appSelectors.actions);
export const useTheme = () => useAppStore(appSelectors.theme);
export const useLanguage = () => useAppStore(appSelectors.language);
export const useIsOnline = () => useAppStore(appSelectors.isOnline);
export const useNotifications = () => useAppStore(appSelectors.notifications);
export const useUnreadNotifications = () => useAppStore(appSelectors.unreadNotifications);
export const useIsGlobalLoading = () => useAppStore(appSelectors.isGlobalLoading);
export const useGlobalError = () => useAppStore(appSelectors.globalError);

/**
 * 组合Hook
 */
export const useComponentLoading = (component: string) => {
  const { setComponentLoading } = useAppActions();
  const loadingStates = useAppStore(appSelectors.componentLoadingStates);

  return {
    isLoading: !!loadingStates[component],
    setLoading: (loading: boolean) => setComponentLoading(component, loading),
  };
};

export const useModal = (modalName: string) => {
  const { openModal, closeModal, toggleModal } = useAppActions();
  const modals = useAppStore(appSelectors.modals);

  return {
    isOpen: !!modals[modalName],
    open: () => openModal(modalName),
    close: () => closeModal(modalName),
    toggle: () => toggleModal(modalName),
  };
};