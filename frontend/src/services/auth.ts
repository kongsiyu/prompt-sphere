import { authApi, TokenManager } from './api';
import type {
  LoginRequest,
  LoginResponse,
  DingTalkAuthRequest,
  DingTalkAuthResponse,
  User,
  UserProfile,
} from '../types/api';
import { AppError, ErrorType } from '../utils/errorHandler';

/**
 * 认证状态枚举
 */
export enum AuthStatus {
  IDLE = 'idle',
  LOADING = 'loading',
  AUTHENTICATED = 'authenticated',
  UNAUTHENTICATED = 'unauthenticated',
  ERROR = 'error',
}

/**
 * 认证事件类型
 */
export enum AuthEventType {
  LOGIN = 'login',
  LOGOUT = 'logout',
  TOKEN_REFRESH = 'token_refresh',
  SESSION_EXPIRED = 'session_expired',
  USER_UPDATE = 'user_update',
}

/**
 * 认证事件数据
 */
export interface AuthEventData {
  type: AuthEventType;
  user?: User;
  error?: AppError;
  timestamp: number;
}

/**
 * 认证事件监听器
 */
export type AuthEventListener = (data: AuthEventData) => void;

/**
 * DingTalk OAuth 配置
 */
export interface DingTalkOAuthConfig {
  appId: string;
  redirectUri: string;
  scope: string;
  state?: string;
}

/**
 * 认证服务类
 */
class AuthService {
  private eventListeners: Map<AuthEventType, Set<AuthEventListener>> = new Map();
  private currentUser: User | null = null;
  private status: AuthStatus = AuthStatus.IDLE;

  /**
   * 初始化认证服务
   */
  init(): void {
    // 检查本地存储的token
    this.checkExistingToken();

    // 设置token自动刷新
    this.setupTokenRefresh();

    // 监听页面可见性变化
    this.setupVisibilityChangeListener();
  }

  /**
   * 检查现有token
   */
  private checkExistingToken(): void {
    const token = TokenManager.getAccessToken();
    if (token && !TokenManager.isTokenExpired()) {
      this.setStatus(AuthStatus.AUTHENTICATED);
      // 尝试获取用户信息
      this.getCurrentUser().catch(() => {
        // 如果获取用户信息失败，清除token
        this.logout();
      });
    } else {
      this.setStatus(AuthStatus.UNAUTHENTICATED);
      TokenManager.clearTokens();
    }
  }

  /**
   * 设置token自动刷新
   */
  private setupTokenRefresh(): void {
    // 每分钟检查一次token是否需要刷新
    setInterval(() => {
      if (this.status === AuthStatus.AUTHENTICATED && TokenManager.shouldRefreshToken()) {
        this.refreshToken().catch((error) => {
          console.error('自动刷新token失败:', error);
          this.handleSessionExpired();
        });
      }
    }, 60 * 1000); // 1分钟
  }

  /**
   * 设置页面可见性变化监听器
   */
  private setupVisibilityChangeListener(): void {
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && this.status === AuthStatus.AUTHENTICATED) {
        // 页面变为可见时，检查token是否过期
        if (TokenManager.isTokenExpired()) {
          this.refreshToken().catch(() => {
            this.handleSessionExpired();
          });
        }
      }
    });
  }

  /**
   * 设置认证状态
   */
  private setStatus(status: AuthStatus): void {
    this.status = status;
  }

  /**
   * 获取当前认证状态
   */
  getStatus(): AuthStatus {
    return this.status;
  }

  /**
   * 获取当前用户
   */
  getCurrentUser(): Promise<User> {
    if (this.currentUser) {
      return Promise.resolve(this.currentUser);
    }

    return authApi.getCurrentUser().then((user) => {
      this.currentUser = user;
      return user;
    });
  }

  /**
   * 邮箱密码登录
   */
  async login(credentials: LoginRequest): Promise<User> {
    try {
      this.setStatus(AuthStatus.LOADING);

      const response: LoginResponse = await authApi.login(credentials);

      // 保存token
      TokenManager.setAccessToken(response.accessToken, response.expiresIn);
      TokenManager.setRefreshToken(response.refreshToken);

      // 设置当前用户
      this.currentUser = response.user;
      this.setStatus(AuthStatus.AUTHENTICATED);

      // 触发登录事件
      this.emitEvent(AuthEventType.LOGIN, { user: response.user });

      return response.user;
    } catch (error) {
      this.setStatus(AuthStatus.ERROR);
      throw error;
    }
  }

  /**
   * 钉钉OAuth登录
   */
  async loginWithDingTalk(authData: DingTalkAuthRequest): Promise<User> {
    try {
      this.setStatus(AuthStatus.LOADING);

      const response: DingTalkAuthResponse = await authApi.loginWithDingTalk(authData);

      // 保存token
      TokenManager.setAccessToken(response.accessToken, response.expiresIn);
      TokenManager.setRefreshToken(response.refreshToken);

      // 设置当前用户
      this.currentUser = response.user;
      this.setStatus(AuthStatus.AUTHENTICATED);

      // 触发登录事件
      this.emitEvent(AuthEventType.LOGIN, { user: response.user });

      return response.user;
    } catch (error) {
      this.setStatus(AuthStatus.ERROR);
      throw error;
    }
  }

  /**
   * 退出登录
   */
  async logout(): Promise<void> {
    try {
      // 调用API退出登录
      if (TokenManager.getAccessToken()) {
        await authApi.logout().catch(() => {
          // 忽略退出登录API的错误
        });
      }
    } finally {
      // 清除本地数据
      TokenManager.clearTokens();
      this.currentUser = null;
      this.setStatus(AuthStatus.UNAUTHENTICATED);

      // 触发退出登录事件
      this.emitEvent(AuthEventType.LOGOUT);
    }
  }

  /**
   * 刷新token
   */
  async refreshToken(): Promise<void> {
    const refreshToken = TokenManager.getRefreshToken();
    if (!refreshToken) {
      throw new AppError('没有刷新令牌', ErrorType.AUTH_ERROR);
    }

    try {
      const response = await authApi.refreshToken({ refreshToken });

      TokenManager.setAccessToken(response.accessToken, response.expiresIn);
      TokenManager.setRefreshToken(response.refreshToken);

      // 触发token刷新事件
      this.emitEvent(AuthEventType.TOKEN_REFRESH);
    } catch (error) {
      // 刷新失败，清除所有token
      TokenManager.clearTokens();
      this.handleSessionExpired();
      throw error;
    }
  }

  /**
   * 更新用户资料
   */
  async updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
    const updatedProfile = await authApi.updateProfile(data);

    // 更新当前用户信息
    if (this.currentUser) {
      this.currentUser = { ...this.currentUser, ...updatedProfile };
    }

    // 触发用户更新事件
    this.emitEvent(AuthEventType.USER_UPDATE, { user: this.currentUser! });

    return updatedProfile;
  }

  /**
   * 检查是否已认证
   */
  isAuthenticated(): boolean {
    return this.status === AuthStatus.AUTHENTICATED && !!TokenManager.getAccessToken();
  }

  /**
   * 检查是否正在加载
   */
  isLoading(): boolean {
    return this.status === AuthStatus.LOADING;
  }

  /**
   * 获取用户权限
   */
  getUserPermissions(): string[] {
    return this.currentUser?.permissions || [];
  }

  /**
   * 检查用户是否有特定权限
   */
  hasPermission(permission: string): boolean {
    return this.getUserPermissions().includes(permission);
  }

  /**
   * 检查用户角色
   */
  hasRole(role: string): boolean {
    return this.currentUser?.role === role;
  }

  /**
   * 处理会话过期
   */
  private handleSessionExpired(): void {
    this.currentUser = null;
    this.setStatus(AuthStatus.UNAUTHENTICATED);

    // 触发会话过期事件
    this.emitEvent(AuthEventType.SESSION_EXPIRED);

    // 重定向到登录页
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  /**
   * 添加事件监听器
   */
  addEventListener(type: AuthEventType, listener: AuthEventListener): void {
    if (!this.eventListeners.has(type)) {
      this.eventListeners.set(type, new Set());
    }
    this.eventListeners.get(type)!.add(listener);
  }

  /**
   * 移除事件监听器
   */
  removeEventListener(type: AuthEventType, listener: AuthEventListener): void {
    const listeners = this.eventListeners.get(type);
    if (listeners) {
      listeners.delete(listener);
    }
  }

  /**
   * 触发事件
   */
  private emitEvent(type: AuthEventType, data: Partial<AuthEventData> = {}): void {
    const eventData: AuthEventData = {
      type,
      user: data.user,
      error: data.error,
      timestamp: Date.now(),
    };

    const listeners = this.eventListeners.get(type);
    if (listeners) {
      listeners.forEach((listener) => {
        try {
          listener(eventData);
        } catch (error) {
          console.error('认证事件监听器错误:', error);
        }
      });
    }
  }

  /**
   * 生成钉钉OAuth授权URL
   */
  generateDingTalkOAuthUrl(config: DingTalkOAuthConfig): string {
    const params = new URLSearchParams({
      response_type: 'code',
      client_id: config.appId,
      redirect_uri: config.redirectUri,
      scope: config.scope,
      state: config.state || this.generateState(),
    });

    return `https://oapi.dingtalk.com/connect/oauth2/sns_authorize?${params.toString()}`;
  }

  /**
   * 处理钉钉OAuth回调
   */
  async handleDingTalkCallback(code: string, state?: string): Promise<User> {
    // 验证state参数
    const savedState = sessionStorage.getItem('dingtalk_oauth_state');
    if (state && savedState && state !== savedState) {
      throw new AppError('无效的OAuth状态参数', ErrorType.AUTH_ERROR);
    }

    // 清除保存的state
    sessionStorage.removeItem('dingtalk_oauth_state');

    return this.loginWithDingTalk({ code, state });
  }

  /**
   * 生成OAuth state参数
   */
  private generateState(): string {
    const state = Math.random().toString(36).substring(2, 15) +
                  Math.random().toString(36).substring(2, 15);

    // 保存state到sessionStorage
    sessionStorage.setItem('dingtalk_oauth_state', state);

    return state;
  }

  /**
   * 清除所有事件监听器
   */
  clearEventListeners(): void {
    this.eventListeners.clear();
  }

  /**
   * 销毁认证服务
   */
  destroy(): void {
    this.clearEventListeners();
    this.currentUser = null;
    this.setStatus(AuthStatus.IDLE);
  }
}

// 创建全局认证服务实例
export const authService = new AuthService();

// 在应用启动时初始化
if (typeof window !== 'undefined') {
  authService.init();
}

/**
 * 认证状态工具函数
 */
export const authUtils = {
  /**
   * 检查token是否即将过期
   */
  isTokenExpiringSoon: (bufferMinutes: number = 5): boolean => {
    const expiresAt = localStorage.getItem('token_expires_at');
    if (!expiresAt) return true;

    const expirationTime = parseInt(expiresAt, 10);
    const currentTime = Date.now();
    const bufferTime = bufferMinutes * 60 * 1000;

    return currentTime >= expirationTime - bufferTime;
  },

  /**
   * 格式化用户显示名称
   */
  formatUserName: (user?: User | null): string => {
    if (!user) return '未知用户';
    return user.name || user.email.split('@')[0];
  },

  /**
   * 获取用户头像URL
   */
  getUserAvatarUrl: (user?: User | null): string => {
    if (!user?.avatar) {
      // 返回默认头像URL
      return `https://ui-avatars.com/api/?name=${encodeURIComponent(authUtils.formatUserName(user))}&background=6366f1&color=fff&size=128`;
    }
    return user.avatar;
  },

  /**
   * 检查用户是否为管理员
   */
  isAdmin: (user?: User | null): boolean => {
    return user?.role === 'admin';
  },

  /**
   * 检查是否为首次登录
   */
  isFirstTimeUser: (user?: User | null): boolean => {
    if (!user) return false;
    // 可以基于用户创建时间或其他标识来判断
    const createdAt = new Date(user.createdAt);
    const now = new Date();
    const timeDiff = now.getTime() - createdAt.getTime();
    const hoursDiff = timeDiff / (1000 * 3600);

    return hoursDiff < 24; // 24小时内注册的用户视为新用户
  },
};

/**
 * 权限检查装饰器
 */
export function requireAuth<T extends any[]>(
  target: any,
  propertyName: string,
  descriptor: TypedPropertyDescriptor<(...args: T) => any>
): void {
  const method = descriptor.value!;

  descriptor.value = function (...args: T) {
    if (!authService.isAuthenticated()) {
      throw new AppError('需要登录才能执行此操作', ErrorType.AUTH_ERROR);
    }
    return method.apply(this, args);
  };
}

/**
 * 权限检查装饰器工厂
 */
export function requirePermission(permission: string) {
  return function <T extends any[]>(
    target: any,
    propertyName: string,
    descriptor: TypedPropertyDescriptor<(...args: T) => any>
  ): void {
    const method = descriptor.value!;

    descriptor.value = function (...args: T) {
      if (!authService.hasPermission(permission)) {
        throw new AppError(
          `缺少必要的权限: ${permission}`,
          ErrorType.FORBIDDEN
        );
      }
      return method.apply(this, args);
    };
  };
}

export default authService;