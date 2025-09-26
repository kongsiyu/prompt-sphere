import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';
import type {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  DingTalkAuthRequest,
  DingTalkAuthResponse,
  User,
  UserProfile,
  Prompt,
  CreatePromptRequest,
  UpdatePromptRequest,
  PromptSearchParams,
  PaginatedResponse,
  Category,
  Tag,
  SystemHealth,
  FileUploadRequest,
  FileUploadResponse,
} from '../types/api';
import { handleAxiosError, withRetry, AppError } from '../utils/errorHandler';

/**
 * API 客户端配置
 */
export interface ApiClientConfig {
  baseURL: string;
  timeout: number;
  withCredentials: boolean;
  headers: Record<string, string>;
}

/**
 * 默认配置
 */
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Token 管理器
 */
class TokenManager {
  private static readonly ACCESS_TOKEN_KEY = 'access_token';
  private static readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private static readonly TOKEN_EXPIRES_AT_KEY = 'token_expires_at';

  static getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  static setAccessToken(token: string, expiresIn: number): void {
    localStorage.setItem(this.ACCESS_TOKEN_KEY, token);
    const expiresAt = new Date(Date.now() + expiresIn * 1000).getTime();
    localStorage.setItem(this.TOKEN_EXPIRES_AT_KEY, expiresAt.toString());
  }

  static getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  static setRefreshToken(token: string): void {
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
  }

  static clearTokens(): void {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.TOKEN_EXPIRES_AT_KEY);
  }

  static isTokenExpired(): boolean {
    const expiresAt = localStorage.getItem(this.TOKEN_EXPIRES_AT_KEY);
    if (!expiresAt) return true;

    const expirationTime = parseInt(expiresAt, 10);
    const currentTime = Date.now();
    // 提前5分钟认为token过期
    const bufferTime = 5 * 60 * 1000;

    return currentTime >= expirationTime - bufferTime;
  }

  static shouldRefreshToken(): boolean {
    return !!this.getRefreshToken() && this.isTokenExpired();
  }
}

/**
 * API 客户端类
 */
class ApiClient {
  private instance: AxiosInstance;
  private isRefreshingToken = false;
  private refreshTokenPromise: Promise<string> | null = null;

  constructor(config: Partial<ApiClientConfig> = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.instance = axios.create(finalConfig);
    this.setupInterceptors();
  }

  /**
   * 设置拦截器
   */
  private setupInterceptors(): void {
    // 请求拦截器
    this.instance.interceptors.request.use(
      this.handleRequest.bind(this),
      (error) => Promise.reject(handleAxiosError(error))
    );

    // 响应拦截器
    this.instance.interceptors.response.use(
      this.handleResponse.bind(this),
      this.handleResponseError.bind(this)
    );
  }

  /**
   * 处理请求
   */
  private async handleRequest(
    config: InternalAxiosRequestConfig
  ): Promise<InternalAxiosRequestConfig> {
    // 添加访问令牌
    const token = TokenManager.getAccessToken();
    if (token && !TokenManager.isTokenExpired()) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 添加请求标识
    config.headers['X-Request-ID'] = this.generateRequestId();

    // 添加时间戳
    config.headers['X-Request-Time'] = Date.now().toString();

    return config;
  }

  /**
   * 处理响应
   */
  private handleResponse(response: AxiosResponse): AxiosResponse {
    // 记录响应时间
    const requestTime = response.config.headers['X-Request-Time'] as string;
    if (requestTime) {
      const responseTime = Date.now() - parseInt(requestTime, 10);
      console.log(`[API] ${response.config.method?.toUpperCase()} ${response.config.url} - ${responseTime}ms`);
    }

    return response;
  }

  /**
   * 处理响应错误
   */
  private async handleResponseError(error: any): Promise<never> {
    const originalRequest = error.config;

    // 如果是401错误且有refresh token，尝试刷新token
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      TokenManager.getRefreshToken() &&
      !originalRequest.url?.includes('/auth/refresh')
    ) {
      originalRequest._retry = true;

      try {
        const newAccessToken = await this.refreshAccessToken();
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return this.instance(originalRequest);
      } catch (refreshError) {
        // 刷新失败，清除所有token并重定向到登录页
        TokenManager.clearTokens();
        window.location.href = '/login';
        throw handleAxiosError(refreshError as any);
      }
    }

    throw handleAxiosError(error);
  }

  /**
   * 刷新访问令牌
   */
  private async refreshAccessToken(): Promise<string> {
    if (this.isRefreshingToken && this.refreshTokenPromise) {
      return this.refreshTokenPromise;
    }

    this.isRefreshingToken = true;
    this.refreshTokenPromise = this.performTokenRefresh();

    try {
      const token = await this.refreshTokenPromise;
      return token;
    } finally {
      this.isRefreshingToken = false;
      this.refreshTokenPromise = null;
    }
  }

  /**
   * 执行token刷新
   */
  private async performTokenRefresh(): Promise<string> {
    const refreshToken = TokenManager.getRefreshToken();
    if (!refreshToken) {
      throw new AppError('没有刷新令牌');
    }

    const response = await this.instance.post<ApiResponse<RefreshTokenResponse>>(
      '/auth/refresh',
      { refreshToken }
    );

    const { accessToken, refreshToken: newRefreshToken, expiresIn } = response.data.data!;

    TokenManager.setAccessToken(accessToken, expiresIn);
    TokenManager.setRefreshToken(newRefreshToken);

    return accessToken;
  }

  /**
   * 生成请求ID
   */
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }

  /**
   * 通用请求方法
   */
  async request<T = any>(config: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.request<ApiResponse<T>>(config);

    if (!response.data.success) {
      throw new AppError(response.data.message || '请求失败');
    }

    return response.data.data!;
  }

  /**
   * GET 请求
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'GET', url });
  }

  /**
   * POST 请求
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'POST', url, data });
  }

  /**
   * PUT 请求
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'PUT', url, data });
  }

  /**
   * PATCH 请求
   */
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'PATCH', url, data });
  }

  /**
   * DELETE 请求
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'DELETE', url });
  }

  /**
   * 上传文件
   */
  async upload<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<T>({
      method: 'POST',
      url,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
  }

  /**
   * 带重试的请求
   */
  async requestWithRetry<T = any>(config: AxiosRequestConfig): Promise<T> {
    return withRetry(() => this.request<T>(config));
  }
}

// 创建全局API客户端实例
export const apiClient = new ApiClient();

/**
 * 认证 API
 */
export const authApi = {
  /**
   * 邮箱密码登录
   */
  login: (data: LoginRequest): Promise<LoginResponse> =>
    apiClient.post<LoginResponse>('/auth/login', data),

  /**
   * 钉钉OAuth登录
   */
  loginWithDingTalk: (data: DingTalkAuthRequest): Promise<DingTalkAuthResponse> =>
    apiClient.post<DingTalkAuthResponse>('/auth/dingtalk', data),

  /**
   * 刷新令牌
   */
  refreshToken: (data: RefreshTokenRequest): Promise<RefreshTokenResponse> =>
    apiClient.post<RefreshTokenResponse>('/auth/refresh', data),

  /**
   * 退出登录
   */
  logout: (): Promise<void> =>
    apiClient.post<void>('/auth/logout'),

  /**
   * 获取当前用户信息
   */
  getCurrentUser: (): Promise<User> =>
    apiClient.get<User>('/auth/me'),

  /**
   * 更新用户资料
   */
  updateProfile: (data: Partial<UserProfile>): Promise<UserProfile> =>
    apiClient.patch<UserProfile>('/auth/profile', data),
};

/**
 * 提示词 API
 */
export const promptsApi = {
  /**
   * 获取提示词列表
   */
  getPrompts: (params?: PromptSearchParams): Promise<PaginatedResponse<Prompt>> =>
    apiClient.get<PaginatedResponse<Prompt>>('/prompts', { params }),

  /**
   * 获取提示词详情
   */
  getPrompt: (id: string): Promise<Prompt> =>
    apiClient.get<Prompt>(`/prompts/${id}`),

  /**
   * 创建提示词
   */
  createPrompt: (data: CreatePromptRequest): Promise<Prompt> =>
    apiClient.post<Prompt>('/prompts', data),

  /**
   * 更新提示词
   */
  updatePrompt: (id: string, data: UpdatePromptRequest): Promise<Prompt> =>
    apiClient.patch<Prompt>(`/prompts/${id}`, data),

  /**
   * 删除提示词
   */
  deletePrompt: (id: string): Promise<void> =>
    apiClient.delete<void>(`/prompts/${id}`),

  /**
   * 搜索提示词
   */
  searchPrompts: (query: string, params?: PromptSearchParams): Promise<PaginatedResponse<Prompt>> =>
    apiClient.get<PaginatedResponse<Prompt>>('/prompts/search', {
      params: { ...params, query }
    }),

  /**
   * 获取热门提示词
   */
  getPopularPrompts: (limit: number = 10): Promise<Prompt[]> =>
    apiClient.get<Prompt[]>('/prompts/popular', { params: { limit } }),

  /**
   * 获取最新提示词
   */
  getLatestPrompts: (limit: number = 10): Promise<Prompt[]> =>
    apiClient.get<Prompt[]>('/prompts/latest', { params: { limit } }),
};

/**
 * 分类 API
 */
export const categoriesApi = {
  /**
   * 获取分类列表
   */
  getCategories: (): Promise<Category[]> =>
    apiClient.get<Category[]>('/categories'),

  /**
   * 获取分类详情
   */
  getCategory: (id: string): Promise<Category> =>
    apiClient.get<Category>(`/categories/${id}`),
};

/**
 * 标签 API
 */
export const tagsApi = {
  /**
   * 获取标签列表
   */
  getTags: (): Promise<Tag[]> =>
    apiClient.get<Tag[]>('/tags'),

  /**
   * 获取热门标签
   */
  getPopularTags: (limit: number = 20): Promise<Tag[]> =>
    apiClient.get<Tag[]>('/tags/popular', { params: { limit } }),
};

/**
 * 收藏 API
 */
export const favoritesApi = {
  /**
   * 获取收藏列表
   */
  getFavorites: (): Promise<Prompt[]> =>
    apiClient.get<Prompt[]>('/favorites'),

  /**
   * 添加收藏
   */
  addFavorite: (promptId: string): Promise<void> =>
    apiClient.post<void>(`/favorites/${promptId}`),

  /**
   * 取消收藏
   */
  removeFavorite: (promptId: string): Promise<void> =>
    apiClient.delete<void>(`/favorites/${promptId}`),

  /**
   * 检查是否已收藏
   */
  isFavorited: (promptId: string): Promise<boolean> =>
    apiClient.get<boolean>(`/favorites/${promptId}/check`),
};

/**
 * 文件上传 API
 */
export const filesApi = {
  /**
   * 上传文件
   */
  uploadFile: (file: File, onProgress?: (progress: number) => void): Promise<FileUploadResponse> =>
    apiClient.upload<FileUploadResponse>('/files/upload', file, onProgress),

  /**
   * 删除文件
   */
  deleteFile: (id: string): Promise<void> =>
    apiClient.delete<void>(`/files/${id}`),
};

/**
 * 系统 API
 */
export const systemApi = {
  /**
   * 获取系统健康状态
   */
  getHealth: (): Promise<SystemHealth> =>
    apiClient.get<SystemHealth>('/system/health'),

  /**
   * 获取系统配置
   */
  getConfig: (): Promise<any> =>
    apiClient.get<any>('/system/config'),
};

/**
 * 导出TokenManager供外部使用
 */
export { TokenManager };

/**
 * 导出默认配置
 */
export { DEFAULT_CONFIG };