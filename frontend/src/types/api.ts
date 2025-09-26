/**
 * API相关的类型定义
 */

// 基础API响应结构
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  code?: number;
}

// 分页相关类型
export interface PaginationParams {
  page?: number;
  limit?: number;
  offset?: number;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export interface PaginatedResponse<T = any> {
  data: T[];
  meta: PaginationMeta;
}

// 用户相关类型
export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'admin' | 'user';
  permissions: string[];
  createdAt: string;
  updatedAt: string;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  bio?: string;
  preferences: UserPreferences;
}

export interface UserPreferences {
  language: 'zh' | 'en';
  theme: 'light' | 'dark' | 'system';
  notifications: {
    email: boolean;
    push: boolean;
    inApp: boolean;
  };
}

// 认证相关类型
export interface LoginRequest {
  email: string;
  password: string;
  remember?: boolean;
}

export interface LoginResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface RefreshTokenRequest {
  refreshToken: string;
}

export interface RefreshTokenResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

// 钉钉OAuth相关类型
export interface DingTalkAuthRequest {
  code: string;
  state?: string;
}

export interface DingTalkAuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

// 提示词相关类型
export interface Prompt {
  id: string;
  title: string;
  description?: string;
  content: string;
  category: string;
  tags: string[];
  isPublic: boolean;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  version: number;
  usage: number;
  rating: number;
  favorites: number;
}

export interface CreatePromptRequest {
  title: string;
  description?: string;
  content: string;
  category: string;
  tags: string[];
  isPublic: boolean;
}

export interface UpdatePromptRequest extends Partial<CreatePromptRequest> {
  version?: number;
}

export interface PromptSearchParams extends PaginationParams {
  query?: string;
  category?: string;
  tags?: string[];
  isPublic?: boolean;
  createdBy?: string;
  sortBy?: 'createdAt' | 'updatedAt' | 'usage' | 'rating';
  sortOrder?: 'asc' | 'desc';
}

// 分类相关类型
export interface Category {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  parentId?: string;
  children?: Category[];
  promptCount: number;
}

// 标签相关类型
export interface Tag {
  id: string;
  name: string;
  color?: string;
  promptCount: number;
}

// 收藏相关类型
export interface Favorite {
  id: string;
  userId: string;
  promptId: string;
  createdAt: string;
}

// 评价相关类型
export interface Rating {
  id: string;
  userId: string;
  promptId: string;
  score: number; // 1-5分
  comment?: string;
  createdAt: string;
  updatedAt: string;
}

// 使用统计相关类型
export interface Usage {
  id: string;
  userId: string;
  promptId: string;
  createdAt: string;
}

export interface UsageStats {
  totalUsage: number;
  dailyUsage: { date: string; count: number }[];
  topPrompts: { promptId: string; title: string; count: number }[];
  topCategories: { category: string; count: number }[];
}

// 系统相关类型
export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down';
  version: string;
  uptime: number;
  services: {
    database: 'up' | 'down';
    redis: 'up' | 'down';
    auth: 'up' | 'down';
  };
  metrics: {
    requestsPerSecond: number;
    responseTime: number;
    errorRate: number;
  };
}

// 文件上传相关类型
export interface FileUploadRequest {
  file: File;
  category?: string;
}

export interface FileUploadResponse {
  id: string;
  filename: string;
  originalName: string;
  size: number;
  mimeType: string;
  url: string;
  createdAt: string;
}

// 错误相关类型
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
  path: string;
}

export interface ValidationError {
  field: string;
  message: string;
  value?: any;
}

// HTTP相关类型
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface RequestConfig {
  method: HttpMethod;
  url: string;
  params?: Record<string, any>;
  data?: any;
  headers?: Record<string, string>;
  timeout?: number;
  withCredentials?: boolean;
}

// WebSocket相关类型
export interface WebSocketMessage<T = any> {
  type: string;
  payload: T;
  timestamp: string;
  id: string;
}

export interface NotificationMessage {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  data?: any;
  createdAt: string;
  read: boolean;
}

// 应用状态相关类型
export interface AppConfig {
  name: string;
  version: string;
  environment: 'development' | 'staging' | 'production';
  apiBaseUrl: string;
  websocketUrl: string;
  features: {
    enableDingTalkAuth: boolean;
    enableNotifications: boolean;
    enableAnalytics: boolean;
    enableOfflineMode: boolean;
  };
  limits: {
    maxPromptLength: number;
    maxFileSize: number;
    rateLimits: {
      requestsPerMinute: number;
      requestsPerHour: number;
    };
  };
}