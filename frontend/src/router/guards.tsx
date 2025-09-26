import { Navigate } from 'react-router-dom';
import { RouteGuard, RouteGuardContext } from '../types/router';

/**
 * 认证状态检查 - 这里是简化版本，实际应该从状态管理获取
 * TODO: 集成实际的认证状态管理
 */
const isAuthenticated = (): boolean => {
  const token = localStorage.getItem('authToken');
  return !!token;
};

/**
 * 用户角色检查 - 简化版本
 * TODO: 集成实际的用户角色系统
 */
const hasRole = (requiredRoles?: string[]): boolean => {
  if (!requiredRoles || requiredRoles.length === 0) return true;

  const userRoles = JSON.parse(localStorage.getItem('userRoles') || '[]');
  return requiredRoles.some(role => userRoles.includes(role));
};

/**
 * 认证守卫 - 检查用户是否已登录
 */
export const authGuard: RouteGuard = async (context: RouteGuardContext) => {
  const { meta, to } = context;

  if (meta.requiresAuth && !isAuthenticated()) {
    // 重定向到登录页面，并保存目标路径
    return `/auth/login?redirect=${encodeURIComponent(to)}`;
  }

  return true;
};

/**
 * 角色守卫 - 检查用户权限
 */
export const roleGuard: RouteGuard = async (context: RouteGuardContext) => {
  const { meta } = context;

  if (meta.requiresAuth && !hasRole(meta.roles)) {
    // 权限不足，重定向到首页或403页面
    return '/';
  }

  return true;
};

/**
 * 路由守卫组件 - 包装需要守卫的路由
 */
export interface RouteGuardProps {
  children: React.ReactNode;
  meta: import('../types/router').RouteMeta;
  path: string;
}

export const RouteGuardComponent: React.FC<RouteGuardProps> = ({
  children,
  meta,
  path
}) => {
  const from = window.location.pathname;

  const context: RouteGuardContext = {
    to: path,
    from,
    meta
  };

  // 执行认证守卫
  if (meta.requiresAuth && !isAuthenticated()) {
    return <Navigate to={`/auth/login?redirect=${encodeURIComponent(path)}`} replace />;
  }

  // 执行角色守卫
  if (meta.requiresAuth && !hasRole(meta.roles)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

/**
 * 应用所有路由守卫
 */
export const applyGuards = async (context: RouteGuardContext): Promise<string | boolean> => {
  const guards = [authGuard, roleGuard];

  for (const guard of guards) {
    const result = await guard(context);

    if (result === false) {
      return '/'; // 默认重定向到首页
    }

    if (typeof result === 'string') {
      return result; // 重定向路径
    }
  }

  return true; // 通过所有守卫
};