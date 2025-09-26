import { useCallback, useEffect, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  useAuthStore,
  useAuth as useAuthActions,
  useAuthStatus,
  useUser,
  useIsAuthenticated,
  useIsLoading,
  useAuthError,
  usePermissions,
  useUserName,
  authSelectors
} from '../stores/authStore';
import { useAppStore } from '../stores/appStore';
import type { LoginRequest, DingTalkAuthRequest, UserProfile } from '../types/api';
import { AuthStatus, authService } from '../services/auth';
import { handleError } from '../utils/errorHandler';

/**
 * 认证Hook的返回类型
 */
export interface UseAuthReturn {
  // 状态
  status: AuthStatus;
  user: ReturnType<typeof useUser>;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: ReturnType<typeof useAuthError>;
  userName: string;
  permissions: string[];

  // 操作方法
  login: (credentials: LoginRequest) => Promise<void>;
  loginWithDingTalk: (authData: DingTalkAuthRequest) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (data: Partial<UserProfile>) => Promise<void>;
  clearError: () => void;

  // 权限检查
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;

  // 导航相关
  requireAuth: () => void;
  redirectToLogin: (returnUrl?: string) => void;
  redirectAfterLogin: () => void;

  // 实用工具
  getUserDisplayName: () => string;
  getUserAvatarUrl: () => string;
  isFirstTimeUser: () => boolean;
  getSessionInfo: () => any;
}

/**
 * 主要的认证Hook
 */
export function useAuth(): UseAuthReturn {
  const navigate = useNavigate();
  const location = useLocation();

  // 从store获取状态
  const status = useAuthStatus();
  const user = useUser();
  const isAuthenticated = useIsAuthenticated();
  const isLoading = useIsLoading();
  const error = useAuthError();
  const userName = useUserName();
  const permissions = usePermissions();
  const actions = useAuthActions();

  // 从app store获取通知功能
  const addNotification = useAppStore(state => state.actions.addNotification);

  // 登录
  const login = useCallback(async (credentials: LoginRequest) => {
    try {
      await actions.login(credentials);

      addNotification({
        type: 'success',
        title: '登录成功',
        message: `欢迎回来，${getUserDisplayName()}！`,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: '登录失败',
        message: '请检查您的登录信息',
      });
      throw error;
    }
  }, [actions, addNotification]);

  // 钉钉登录
  const loginWithDingTalk = useCallback(async (authData: DingTalkAuthRequest) => {
    try {
      await actions.loginWithDingTalk(authData);

      addNotification({
        type: 'success',
        title: '登录成功',
        message: `欢迎使用钉钉登录，${getUserDisplayName()}！`,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: '钉钉登录失败',
        message: '钉钉授权失败，请重试',
      });
      throw error;
    }
  }, [actions, addNotification]);

  // 退出登录
  const logout = useCallback(async () => {
    try {
      await actions.logout();

      addNotification({
        type: 'info',
        title: '已退出登录',
        message: '感谢使用，期待您的再次访问',
      });
    } catch (error) {
      // 即使退出登录失败，也显示成功消息
      addNotification({
        type: 'info',
        title: '已退出登录',
        message: '感谢使用，期待您的再次访问',
      });
    }
  }, [actions, addNotification]);

  // 更新资料
  const updateProfile = useCallback(async (data: Partial<UserProfile>) => {
    try {
      await actions.updateProfile(data);

      addNotification({
        type: 'success',
        title: '资料已更新',
        message: '您的个人资料已成功更新',
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: '更新失败',
        message: '更新个人资料时发生错误',
      });
      throw error;
    }
  }, [actions, addNotification]);

  // 清除错误
  const clearError = useCallback(() => {
    actions.clearError();
  }, [actions]);

  // 权限检查
  const hasPermission = useCallback((permission: string) => {
    return actions.hasPermission(permission);
  }, [actions]);

  const hasRole = useCallback((role: string) => {
    return actions.hasRole(role);
  }, [actions]);

  const hasAnyRole = useCallback((roles: string[]) => {
    return actions.hasAnyRole(roles);
  }, [actions]);

  const hasAllPermissions = useCallback((targetPermissions: string[]) => {
    return actions.hasAllPermissions(targetPermissions);
  }, [actions]);

  // 导航相关
  const requireAuth = useCallback(() => {
    if (!isAuthenticated) {
      redirectToLogin(location.pathname + location.search);
    }
  }, [isAuthenticated, location]);

  const redirectToLogin = useCallback((returnUrl?: string) => {
    const loginUrl = returnUrl
      ? `/login?returnUrl=${encodeURIComponent(returnUrl)}`
      : '/login';
    navigate(loginUrl);
  }, [navigate]);

  const redirectAfterLogin = useCallback(() => {
    const params = new URLSearchParams(location.search);
    const returnUrl = params.get('returnUrl') || '/dashboard';
    navigate(returnUrl);
  }, [navigate, location]);

  // 实用工具
  const getUserDisplayName = useCallback(() => {
    if (!user) return '未知用户';
    return user.name || user.email?.split('@')[0] || '未知用户';
  }, [user]);

  const getUserAvatarUrl = useCallback(() => {
    if (user?.avatar) return user.avatar;

    const displayName = getUserDisplayName();
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}&background=6366f1&color=fff&size=128`;
  }, [user, getUserDisplayName]);

  const isFirstTimeUser = useCallback(() => {
    if (!user) return false;

    const createdAt = new Date(user.createdAt);
    const now = new Date();
    const timeDiff = now.getTime() - createdAt.getTime();
    const hoursDiff = timeDiff / (1000 * 3600);

    return hoursDiff < 24; // 24小时内注册视为新用户
  }, [user]);

  const getSessionInfo = useCallback(() => {
    return useAuthStore.getState().sessionInfo;
  }, []);

  return {
    // 状态
    status,
    user,
    isAuthenticated,
    isLoading,
    error,
    userName,
    permissions,

    // 操作方法
    login,
    loginWithDingTalk,
    logout,
    updateProfile,
    clearError,

    // 权限检查
    hasPermission,
    hasRole,
    hasAnyRole,
    hasAllPermissions,

    // 导航相关
    requireAuth,
    redirectToLogin,
    redirectAfterLogin,

    // 实用工具
    getUserDisplayName,
    getUserAvatarUrl,
    isFirstTimeUser,
    getSessionInfo,
  };
}

/**
 * 需要认证的路由Guard Hook
 */
export function useAuthGuard(requiredPermissions?: string[], requiredRoles?: string[]) {
  const auth = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // 如果未认证，重定向到登录页
    if (!auth.isAuthenticated && auth.status !== AuthStatus.LOADING) {
      const returnUrl = location.pathname + location.search;
      navigate(`/login?returnUrl=${encodeURIComponent(returnUrl)}`);
      return;
    }

    // 检查权限
    if (auth.isAuthenticated) {
      if (requiredPermissions && !auth.hasAllPermissions(requiredPermissions)) {
        navigate('/unauthorized');
        return;
      }

      if (requiredRoles && !auth.hasAnyRole(requiredRoles)) {
        navigate('/unauthorized');
        return;
      }
    }
  }, [auth.isAuthenticated, auth.status, requiredPermissions, requiredRoles, navigate, location]);

  return {
    isAuthorized: auth.isAuthenticated &&
      (!requiredPermissions || auth.hasAllPermissions(requiredPermissions)) &&
      (!requiredRoles || auth.hasAnyRole(requiredRoles)),
    isLoading: auth.isLoading || auth.status === AuthStatus.LOADING,
  };
}

/**
 * 钉钉OAuth Hook
 */
export function useDingTalkAuth() {
  const auth = useAuth();
  const location = useLocation();

  // 生成钉钉OAuth URL
  const generateAuthUrl = useCallback((config: {
    appId: string;
    redirectUri: string;
    scope?: string;
    state?: string;
  }) => {
    return authService.generateDingTalkOAuthUrl({
      scope: 'openid',
      ...config,
    });
  }, []);

  // 处理OAuth回调
  const handleCallback = useCallback(async () => {
    const params = new URLSearchParams(location.search);
    const code = params.get('code');
    const state = params.get('state');

    if (!code) {
      throw new Error('授权码不存在');
    }

    return auth.loginWithDingTalk({ code, state: state || undefined });
  }, [location, auth]);

  // 启动OAuth流程
  const startAuth = useCallback((config: {
    appId: string;
    redirectUri: string;
    scope?: string;
  }) => {
    const authUrl = generateAuthUrl(config);
    window.location.href = authUrl;
  }, [generateAuthUrl]);

  return {
    generateAuthUrl,
    handleCallback,
    startAuth,
    isLoading: auth.isLoading,
    error: auth.error,
  };
}

/**
 * 用户权限Hook
 */
export function usePermissions() {
  const permissions = useAuthStore(authSelectors.permissions);
  const user = useUser();

  const permissionUtils = useMemo(() => ({
    // 基础权限检查
    has: (permission: string) => permissions.includes(permission),
    hasAny: (perms: string[]) => perms.some(p => permissions.includes(p)),
    hasAll: (perms: string[]) => perms.every(p => permissions.includes(p)),

    // 角色检查
    isAdmin: () => user?.role === 'admin',
    isUser: () => user?.role === 'user',

    // 资源权限检查
    canRead: (resource: string) => permissions.includes(`${resource}:read`),
    canWrite: (resource: string) => permissions.includes(`${resource}:write`),
    canDelete: (resource: string) => permissions.includes(`${resource}:delete`),
    canManage: (resource: string) => permissions.includes(`${resource}:manage`),

    // 批量检查
    getResourcePermissions: (resource: string) => {
      const resourcePerms = permissions.filter(p => p.startsWith(`${resource}:`));
      return {
        read: resourcePerms.includes(`${resource}:read`),
        write: resourcePerms.includes(`${resource}:write`),
        delete: resourcePerms.includes(`${resource}:delete`),
        manage: resourcePerms.includes(`${resource}:manage`),
      };
    },
  }), [permissions, user]);

  return {
    permissions,
    ...permissionUtils,
  };
}

/**
 * 会话管理Hook
 */
export function useSession() {
  const sessionInfo = useAuthStore(state => state.sessionInfo);
  const updateSessionInfo = useAuthStore(state => state.actions.updateSessionInfo);
  const refreshToken = useAuthStore(state => state.actions.refreshToken);

  const sessionUtils = useMemo(() => ({
    // 会话信息
    lastLoginAt: sessionInfo.lastLoginAt,
    loginMethod: sessionInfo.loginMethod,
    ipAddress: sessionInfo.ipAddress,
    userAgent: sessionInfo.userAgent,

    // 格式化显示
    getLoginTimeDisplay: () => {
      if (!sessionInfo.lastLoginAt) return '未知';
      return new Date(sessionInfo.lastLoginAt).toLocaleString('zh-CN');
    },

    getLoginMethodDisplay: () => {
      const methods = {
        email: '邮箱登录',
        dingtalk: '钉钉登录',
      };
      return methods[sessionInfo.loginMethod as keyof typeof methods] || '未知';
    },

    // 会话操作
    updateSession: (info: Partial<typeof sessionInfo>) => {
      updateSessionInfo(info);
    },

    // token管理
    refreshSession: async () => {
      try {
        await refreshToken();
        return true;
      } catch (error) {
        console.error('刷新会话失败:', error);
        return false;
      }
    },
  }), [sessionInfo, updateSessionInfo, refreshToken]);

  return sessionUtils;
}

export default useAuth;