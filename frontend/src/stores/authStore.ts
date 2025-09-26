import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type { User, LoginRequest, DingTalkAuthRequest, UserProfile } from '../types/api';
import { authService, AuthStatus, AuthEventType } from '../services/auth';
import { AppError, handleError } from '../utils/errorHandler';

/**
 * 认证状态接口
 */
export interface AuthState {
  // 状态
  status: AuthStatus;
  user: User | null;
  error: AppError | null;
  isLoading: boolean;
  isInitialized: boolean;

  // 用户会话信息
  sessionInfo: {
    lastLoginAt: string | null;
    loginMethod: 'email' | 'dingtalk' | null;
    ipAddress: string | null;
    userAgent: string | null;
  };

  // 权限相关
  permissions: string[];
  roles: string[];

  // UI状态
  showLoginModal: boolean;
  redirectUrl: string | null;

  // 操作方法
  actions: {
    // 登录相关
    login: (credentials: LoginRequest) => Promise<void>;
    loginWithDingTalk: (authData: DingTalkAuthRequest) => Promise<void>;
    logout: () => Promise<void>;
    refreshToken: () => Promise<void>;

    // 用户信息
    getCurrentUser: () => Promise<void>;
    updateProfile: (data: Partial<UserProfile>) => Promise<void>;

    // 状态管理
    setStatus: (status: AuthStatus) => void;
    setError: (error: AppError | null) => void;
    setUser: (user: User | null) => void;
    clearError: () => void;

    // UI操作
    showLogin: (redirectUrl?: string) => void;
    hideLogin: () => void;
    setRedirectUrl: (url: string | null) => void;

    // 权限检查
    hasPermission: (permission: string) => boolean;
    hasRole: (role: string) => boolean;
    hasAnyRole: (roles: string[]) => boolean;
    hasAllPermissions: (permissions: string[]) => boolean;

    // 会话管理
    updateSessionInfo: (info: Partial<AuthState['sessionInfo']>) => void;

    // 初始化
    initialize: () => Promise<void>;
    reset: () => void;
  };
}

/**
 * 初始状态
 */
const initialState: Omit<AuthState, 'actions'> = {
  status: AuthStatus.IDLE,
  user: null,
  error: null,
  isLoading: false,
  isInitialized: false,
  sessionInfo: {
    lastLoginAt: null,
    loginMethod: null,
    ipAddress: null,
    userAgent: null,
  },
  permissions: [],
  roles: [],
  showLoginModal: false,
  redirectUrl: null,
};

/**
 * 持久化配置
 */
const persistConfig = {
  name: 'auth-store',
  storage: createJSONStorage(() => localStorage),
  partialize: (state: AuthState) => ({
    sessionInfo: state.sessionInfo,
    redirectUrl: state.redirectUrl,
  }),
  version: 1,
  migrate: (persistedState: any, version: number) => {
    if (version < 1) {
      // 处理版本迁移
      return {
        ...persistedState,
        sessionInfo: initialState.sessionInfo,
      };
    }
    return persistedState;
  },
};

/**
 * 创建认证存储
 */
export const useAuthStore = create<AuthState>()(
  subscribeWithSelector(
    persist(
      immer((set, get) => ({
        ...initialState,

        actions: {
          /**
           * 邮箱密码登录
           */
          login: async (credentials: LoginRequest) => {
            try {
              set((state) => {
                state.isLoading = true;
                state.error = null;
                state.status = AuthStatus.LOADING;
              });

              const user = await authService.login(credentials);

              set((state) => {
                state.user = user;
                state.status = AuthStatus.AUTHENTICATED;
                state.isLoading = false;
                state.error = null;
                state.permissions = user.permissions || [];
                state.roles = [user.role];
                state.showLoginModal = false;
                state.sessionInfo.lastLoginAt = new Date().toISOString();
                state.sessionInfo.loginMethod = 'email';
                state.sessionInfo.userAgent = navigator.userAgent;
              });

              // 如果有重定向URL，跳转到该页面
              const { redirectUrl } = get();
              if (redirectUrl) {
                window.location.href = redirectUrl;
                get().actions.setRedirectUrl(null);
              }
            } catch (error) {
              const appError = handleError(error);
              set((state) => {
                state.error = appError;
                state.isLoading = false;
                state.status = AuthStatus.ERROR;
              });
              throw appError;
            }
          },

          /**
           * 钉钉OAuth登录
           */
          loginWithDingTalk: async (authData: DingTalkAuthRequest) => {
            try {
              set((state) => {
                state.isLoading = true;
                state.error = null;
                state.status = AuthStatus.LOADING;
              });

              const user = await authService.loginWithDingTalk(authData);

              set((state) => {
                state.user = user;
                state.status = AuthStatus.AUTHENTICATED;
                state.isLoading = false;
                state.error = null;
                state.permissions = user.permissions || [];
                state.roles = [user.role];
                state.showLoginModal = false;
                state.sessionInfo.lastLoginAt = new Date().toISOString();
                state.sessionInfo.loginMethod = 'dingtalk';
                state.sessionInfo.userAgent = navigator.userAgent;
              });

              // 如果有重定向URL，跳转到该页面
              const { redirectUrl } = get();
              if (redirectUrl) {
                window.location.href = redirectUrl;
                get().actions.setRedirectUrl(null);
              }
            } catch (error) {
              const appError = handleError(error);
              set((state) => {
                state.error = appError;
                state.isLoading = false;
                state.status = AuthStatus.ERROR;
              });
              throw appError;
            }
          },

          /**
           * 退出登录
           */
          logout: async () => {
            try {
              set((state) => {
                state.isLoading = true;
                state.error = null;
              });

              await authService.logout();

              set((state) => {
                state.user = null;
                state.status = AuthStatus.UNAUTHENTICATED;
                state.isLoading = false;
                state.error = null;
                state.permissions = [];
                state.roles = [];
                state.showLoginModal = false;
                state.sessionInfo = initialState.sessionInfo;
              });

              // 重定向到登录页
              window.location.href = '/login';
            } catch (error) {
              const appError = handleError(error);
              set((state) => {
                state.error = appError;
                state.isLoading = false;
              });
              // 即使退出登录失败，也要清除本地状态
              get().actions.reset();
            }
          },

          /**
           * 刷新令牌
           */
          refreshToken: async () => {
            try {
              await authService.refreshToken();
              // 令牌刷新成功，无需更新UI状态
            } catch (error) {
              const appError = handleError(error);
              set((state) => {
                state.error = appError;
                state.user = null;
                state.status = AuthStatus.UNAUTHENTICATED;
                state.permissions = [];
                state.roles = [];
              });
              throw appError;
            }
          },

          /**
           * 获取当前用户信息
           */
          getCurrentUser: async () => {
            try {
              set((state) => {
                state.isLoading = true;
                state.error = null;
              });

              const user = await authService.getCurrentUser();

              set((state) => {
                state.user = user;
                state.status = AuthStatus.AUTHENTICATED;
                state.isLoading = false;
                state.permissions = user.permissions || [];
                state.roles = [user.role];
              });
            } catch (error) {
              const appError = handleError(error);
              set((state) => {
                state.error = appError;
                state.isLoading = false;
                state.status = AuthStatus.ERROR;
              });
              throw appError;
            }
          },

          /**
           * 更新用户资料
           */
          updateProfile: async (data: Partial<UserProfile>) => {
            try {
              set((state) => {
                state.isLoading = true;
                state.error = null;
              });

              const updatedProfile = await authService.updateProfile(data);

              set((state) => {
                if (state.user) {
                  state.user = { ...state.user, ...updatedProfile };
                }
                state.isLoading = false;
              });
            } catch (error) {
              const appError = handleError(error);
              set((state) => {
                state.error = appError;
                state.isLoading = false;
              });
              throw appError;
            }
          },

          /**
           * 设置认证状态
           */
          setStatus: (status: AuthStatus) => {
            set((state) => {
              state.status = status;
            });
          },

          /**
           * 设置错误
           */
          setError: (error: AppError | null) => {
            set((state) => {
              state.error = error;
            });
          },

          /**
           * 设置用户
           */
          setUser: (user: User | null) => {
            set((state) => {
              state.user = user;
              if (user) {
                state.permissions = user.permissions || [];
                state.roles = [user.role];
                state.status = AuthStatus.AUTHENTICATED;
              } else {
                state.permissions = [];
                state.roles = [];
                state.status = AuthStatus.UNAUTHENTICATED;
              }
            });
          },

          /**
           * 清除错误
           */
          clearError: () => {
            set((state) => {
              state.error = null;
            });
          },

          /**
           * 显示登录模态框
           */
          showLogin: (redirectUrl?: string) => {
            set((state) => {
              state.showLoginModal = true;
              if (redirectUrl) {
                state.redirectUrl = redirectUrl;
              }
            });
          },

          /**
           * 隐藏登录模态框
           */
          hideLogin: () => {
            set((state) => {
              state.showLoginModal = false;
            });
          },

          /**
           * 设置重定向URL
           */
          setRedirectUrl: (url: string | null) => {
            set((state) => {
              state.redirectUrl = url;
            });
          },

          /**
           * 检查权限
           */
          hasPermission: (permission: string): boolean => {
            const { permissions } = get();
            return permissions.includes(permission);
          },

          /**
           * 检查角色
           */
          hasRole: (role: string): boolean => {
            const { roles } = get();
            return roles.includes(role);
          },

          /**
           * 检查是否拥有任一角色
           */
          hasAnyRole: (targetRoles: string[]): boolean => {
            const { roles } = get();
            return targetRoles.some(role => roles.includes(role));
          },

          /**
           * 检查是否拥有所有权限
           */
          hasAllPermissions: (targetPermissions: string[]): boolean => {
            const { permissions } = get();
            return targetPermissions.every(permission => permissions.includes(permission));
          },

          /**
           * 更新会话信息
           */
          updateSessionInfo: (info: Partial<AuthState['sessionInfo']>) => {
            set((state) => {
              state.sessionInfo = { ...state.sessionInfo, ...info };
            });
          },

          /**
           * 初始化认证状态
           */
          initialize: async () => {
            try {
              set((state) => {
                state.isLoading = true;
                state.status = AuthStatus.LOADING;
              });

              // 检查是否已有有效的认证信息
              if (authService.isAuthenticated()) {
                const user = await authService.getCurrentUser();
                set((state) => {
                  state.user = user;
                  state.status = AuthStatus.AUTHENTICATED;
                  state.permissions = user.permissions || [];
                  state.roles = [user.role];
                });
              } else {
                set((state) => {
                  state.status = AuthStatus.UNAUTHENTICATED;
                });
              }
            } catch (error) {
              set((state) => {
                state.error = handleError(error);
                state.status = AuthStatus.ERROR;
              });
            } finally {
              set((state) => {
                state.isLoading = false;
                state.isInitialized = true;
              });
            }
          },

          /**
           * 重置状态
           */
          reset: () => {
            set((state) => {
              Object.assign(state, initialState);
            });
          },
        },
      })),
      persistConfig
    )
  )
);

/**
 * 监听认证服务事件
 */
authService.addEventListener(AuthEventType.LOGIN, (data) => {
  useAuthStore.getState().actions.setUser(data.user!);
});

authService.addEventListener(AuthEventType.LOGOUT, () => {
  useAuthStore.getState().actions.setUser(null);
});

authService.addEventListener(AuthEventType.SESSION_EXPIRED, () => {
  useAuthStore.getState().actions.reset();
});

authService.addEventListener(AuthEventType.USER_UPDATE, (data) => {
  useAuthStore.getState().actions.setUser(data.user!);
});

/**
 * 订阅状态变化
 */
useAuthStore.subscribe(
  (state) => state.status,
  (status, previousStatus) => {
    // 状态变化时的副作用
    if (status === AuthStatus.AUTHENTICATED && previousStatus !== AuthStatus.AUTHENTICATED) {
      console.log('用户已登录');
    } else if (status === AuthStatus.UNAUTHENTICATED && previousStatus !== AuthStatus.UNAUTHENTICATED) {
      console.log('用户已退出登录');
    }
  }
);

/**
 * 选择器函数
 */
export const authSelectors = {
  // 基础状态
  status: (state: AuthState) => state.status,
  user: (state: AuthState) => state.user,
  error: (state: AuthState) => state.error,
  isLoading: (state: AuthState) => state.isLoading,
  isInitialized: (state: AuthState) => state.isInitialized,

  // 认证状态
  isAuthenticated: (state: AuthState) => state.status === AuthStatus.AUTHENTICATED,
  isUnauthenticated: (state: AuthState) => state.status === AuthStatus.UNAUTHENTICATED,

  // 用户信息
  userName: (state: AuthState) => state.user?.name || state.user?.email?.split('@')[0] || '未知用户',
  userEmail: (state: AuthState) => state.user?.email,
  userAvatar: (state: AuthState) => state.user?.avatar,
  userRole: (state: AuthState) => state.user?.role,

  // 权限
  permissions: (state: AuthState) => state.permissions,
  roles: (state: AuthState) => state.roles,

  // UI状态
  showLoginModal: (state: AuthState) => state.showLoginModal,
  redirectUrl: (state: AuthState) => state.redirectUrl,

  // 会话信息
  sessionInfo: (state: AuthState) => state.sessionInfo,
  lastLoginAt: (state: AuthState) => state.sessionInfo.lastLoginAt,
  loginMethod: (state: AuthState) => state.sessionInfo.loginMethod,

  // 动作
  actions: (state: AuthState) => state.actions,
};

/**
 * Hook 形式的选择器
 */
export const useAuth = () => useAuthStore(authSelectors.actions);
export const useAuthStatus = () => useAuthStore(authSelectors.status);
export const useUser = () => useAuthStore(authSelectors.user);
export const useAuthError = () => useAuthStore(authSelectors.error);
export const useIsAuthenticated = () => useAuthStore(authSelectors.isAuthenticated);
export const useIsLoading = () => useAuthStore(authSelectors.isLoading);
export const usePermissions = () => useAuthStore(authSelectors.permissions);
export const useUserName = () => useAuthStore(authSelectors.userName);

/**
 * 权限检查Hook
 */
export const useHasPermission = (permission: string) => {
  return useAuthStore((state) => state.actions.hasPermission(permission));
};

export const useHasRole = (role: string) => {
  return useAuthStore((state) => state.actions.hasRole(role));
};

export const useHasAnyRole = (roles: string[]) => {
  return useAuthStore((state) => state.actions.hasAnyRole(roles));
};

/**
 * 初始化Hook
 */
export const useAuthInit = () => {
  const initialize = useAuthStore((state) => state.actions.initialize);
  const isInitialized = useAuthStore(authSelectors.isInitialized);

  React.useEffect(() => {
    if (!isInitialized) {
      initialize();
    }
  }, [initialize, isInitialized]);

  return isInitialized;
};

// 添加React导入（如果需要）
import React from 'react';