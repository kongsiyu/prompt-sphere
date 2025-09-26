import { AxiosError } from 'axios';
import type { ApiError, ValidationError } from '../types/api';

/**
 * 错误类型枚举
 */
export enum ErrorType {
  NETWORK_ERROR = 'NETWORK_ERROR',
  AUTH_ERROR = 'AUTH_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  SERVER_ERROR = 'SERVER_ERROR',
  NOT_FOUND = 'NOT_FOUND',
  FORBIDDEN = 'FORBIDDEN',
  RATE_LIMIT = 'RATE_LIMIT',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR'
}

/**
 * 应用错误类
 */
export class AppError extends Error {
  public readonly type: ErrorType;
  public readonly statusCode?: number;
  public readonly details?: Record<string, any>;
  public readonly timestamp: string;

  constructor(
    message: string,
    type: ErrorType = ErrorType.UNKNOWN_ERROR,
    statusCode?: number,
    details?: Record<string, any>
  ) {
    super(message);
    this.name = 'AppError';
    this.type = type;
    this.statusCode = statusCode;
    this.details = details;
    this.timestamp = new Date().toISOString();

    // 确保原型链正确
    Object.setPrototypeOf(this, AppError.prototype);
  }
}

/**
 * 网络错误类
 */
export class NetworkError extends AppError {
  constructor(message: string = '网络连接失败，请检查网络设置') {
    super(message, ErrorType.NETWORK_ERROR);
    this.name = 'NetworkError';
  }
}

/**
 * 认证错误类
 */
export class AuthError extends AppError {
  constructor(message: string = '认证失败，请重新登录') {
    super(message, ErrorType.AUTH_ERROR, 401);
    this.name = 'AuthError';
  }
}

/**
 * 验证错误类
 */
export class ValidationError extends AppError {
  public readonly validationErrors: ValidationError[];

  constructor(message: string = '请求参数验证失败', errors: ValidationError[] = []) {
    super(message, ErrorType.VALIDATION_ERROR, 400);
    this.name = 'ValidationError';
    this.validationErrors = errors;
  }
}

/**
 * 服务器错误类
 */
export class ServerError extends AppError {
  constructor(message: string = '服务器内部错误，请稍后重试', statusCode: number = 500) {
    super(message, ErrorType.SERVER_ERROR, statusCode);
    this.name = 'ServerError';
  }
}

/**
 * 错误消息映射
 */
const ERROR_MESSAGES = {
  [ErrorType.NETWORK_ERROR]: '网络连接失败，请检查网络设置',
  [ErrorType.AUTH_ERROR]: '认证失败，请重新登录',
  [ErrorType.VALIDATION_ERROR]: '请求参数验证失败',
  [ErrorType.SERVER_ERROR]: '服务器内部错误，请稍后重试',
  [ErrorType.NOT_FOUND]: '请求的资源不存在',
  [ErrorType.FORBIDDEN]: '没有权限访问此资源',
  [ErrorType.RATE_LIMIT]: '请求过于频繁，请稍后重试',
  [ErrorType.UNKNOWN_ERROR]: '未知错误，请稍后重试'
} as const;

/**
 * 从HTTP状态码获取错误类型
 */
export function getErrorTypeFromStatus(status: number): ErrorType {
  switch (status) {
    case 400:
      return ErrorType.VALIDATION_ERROR;
    case 401:
      return ErrorType.AUTH_ERROR;
    case 403:
      return ErrorType.FORBIDDEN;
    case 404:
      return ErrorType.NOT_FOUND;
    case 429:
      return ErrorType.RATE_LIMIT;
    case 500:
    case 502:
    case 503:
    case 504:
      return ErrorType.SERVER_ERROR;
    default:
      return ErrorType.UNKNOWN_ERROR;
  }
}

/**
 * 解析API错误响应
 */
export function parseApiError(response: any): ApiError {
  return {
    code: response?.code || 'UNKNOWN_ERROR',
    message: response?.message || response?.error || '未知错误',
    details: response?.details || {},
    timestamp: response?.timestamp || new Date().toISOString(),
    path: response?.path || ''
  };
}

/**
 * 处理Axios错误
 */
export function handleAxiosError(error: AxiosError): AppError {
  // 网络错误
  if (!error.response) {
    return new NetworkError('网络连接失败，请检查网络设置');
  }

  const { status, data } = error.response;
  const errorType = getErrorTypeFromStatus(status);
  const apiError = parseApiError(data);

  // 根据错误类型创建对应的错误实例
  switch (errorType) {
    case ErrorType.AUTH_ERROR:
      return new AuthError(apiError.message);

    case ErrorType.VALIDATION_ERROR:
      const validationErrors = apiError.details?.validationErrors || [];
      return new ValidationError(apiError.message, validationErrors);

    case ErrorType.SERVER_ERROR:
      return new ServerError(apiError.message, status);

    default:
      return new AppError(
        apiError.message || ERROR_MESSAGES[errorType],
        errorType,
        status,
        apiError.details
      );
  }
}

/**
 * 处理通用错误
 */
export function handleError(error: unknown): AppError {
  // 如果已经是AppError，直接返回
  if (error instanceof AppError) {
    return error;
  }

  // 如果是AxiosError，使用专门的处理函数
  if (error && typeof error === 'object' && 'isAxiosError' in error) {
    return handleAxiosError(error as AxiosError);
  }

  // 如果是普通的Error
  if (error instanceof Error) {
    return new AppError(error.message, ErrorType.UNKNOWN_ERROR);
  }

  // 其他类型的错误
  return new AppError(
    typeof error === 'string' ? error : '未知错误',
    ErrorType.UNKNOWN_ERROR
  );
}

/**
 * 获取用户友好的错误消息
 */
export function getUserFriendlyMessage(error: AppError): string {
  // 如果错误有自定义消息，优先使用
  if (error.message && error.message !== error.type) {
    return error.message;
  }

  // 使用默认错误消息
  return ERROR_MESSAGES[error.type] || ERROR_MESSAGES[ErrorType.UNKNOWN_ERROR];
}

/**
 * 记录错误日志
 */
export function logError(error: AppError, context?: Record<string, any>): void {
  const logData = {
    error: {
      name: error.name,
      type: error.type,
      message: error.message,
      statusCode: error.statusCode,
      details: error.details,
      timestamp: error.timestamp,
      stack: error.stack
    },
    context,
    userAgent: navigator.userAgent,
    url: window.location.href
  };

  // 在开发环境下输出到控制台
  if (process.env.NODE_ENV === 'development') {
    console.error('App Error:', logData);
  }

  // 在生产环境下，可以发送到错误监控服务
  if (process.env.NODE_ENV === 'production') {
    // TODO: 集成错误监控服务 (Sentry, LogRocket 等)
    // sendToErrorService(logData);
  }
}

/**
 * 错误边界使用的错误处理函数
 */
export function handleErrorBoundary(error: Error, errorInfo: any): void {
  const appError = handleError(error);
  logError(appError, { componentStack: errorInfo.componentStack });
}

/**
 * Promise rejection 全局错误处理
 */
export function setupGlobalErrorHandling(): void {
  // 处理未捕获的Promise rejection
  window.addEventListener('unhandledrejection', (event) => {
    const error = handleError(event.reason);
    logError(error, { type: 'unhandledrejection' });

    // 阻止浏览器默认的错误提示
    event.preventDefault();
  });

  // 处理未捕获的JavaScript错误
  window.addEventListener('error', (event) => {
    const error = handleError(event.error || event.message);
    logError(error, {
      type: 'javascript-error',
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno
    });
  });
}

/**
 * 重试机制配置
 */
export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffFactor: number;
  retryableErrors: ErrorType[];
}

/**
 * 默认重试配置
 */
export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  backoffFactor: 2,
  retryableErrors: [
    ErrorType.NETWORK_ERROR,
    ErrorType.SERVER_ERROR,
    ErrorType.RATE_LIMIT
  ]
};

/**
 * 检查错误是否可重试
 */
export function isRetryableError(error: AppError, config: RetryConfig = DEFAULT_RETRY_CONFIG): boolean {
  return config.retryableErrors.includes(error.type);
}

/**
 * 计算重试延迟
 */
export function calculateRetryDelay(attempt: number, config: RetryConfig = DEFAULT_RETRY_CONFIG): number {
  const delay = config.baseDelay * Math.pow(config.backoffFactor, attempt - 1);
  return Math.min(delay, config.maxDelay);
}

/**
 * 带重试的异步操作包装器
 */
export async function withRetry<T>(
  operation: () => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): Promise<T> {
  let lastError: AppError;

  for (let attempt = 1; attempt <= config.maxRetries + 1; attempt++) {
    try {
      return await operation();
    } catch (error) {
      const appError = handleError(error);
      lastError = appError;

      // 如果是最后一次尝试，或者错误不可重试，直接抛出
      if (attempt > config.maxRetries || !isRetryableError(appError, config)) {
        throw appError;
      }

      // 计算延迟并等待
      const delay = calculateRetryDelay(attempt, config);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError!;
}