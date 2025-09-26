import { ReactNode } from 'react';

/**
 * 路由配置接口
 */
export interface RouteConfig {
  /** 路由路径 */
  path: string;
  /** 路由元信息 */
  meta: RouteMeta;
  /** 页面组件 */
  component?: React.LazyExoticComponent<React.ComponentType<any>>;
  /** 子路由配置 */
  children?: RouteConfig[];
  /** 重定向路径 */
  redirect?: string;
  /** 是否精确匹配 */
  exact?: boolean;
}

/**
 * 路由元信息接口
 */
export interface RouteMeta {
  /** 页面标题 */
  title: string;
  /** 是否需要认证 */
  requiresAuth?: boolean;
  /** 页面图标 */
  icon?: string;
  /** 是否在导航中隐藏 */
  hideInNav?: boolean;
  /** 面包屑导航配置 */
  breadcrumb?: BreadcrumbItem[];
  /** 页面布局组件 */
  layout?: 'default' | 'auth' | 'minimal';
  /** 权限角色 */
  roles?: string[];
}

/**
 * 面包屑导航项接口
 */
export interface BreadcrumbItem {
  /** 显示文本 */
  label: string;
  /** 跳转路径 */
  path?: string;
  /** 是否为当前页面 */
  isActive?: boolean;
}

/**
 * 导航菜单项接口
 */
export interface NavigationItem {
  /** 唯一标识 */
  key: string;
  /** 显示文本 */
  label: string;
  /** 图标 */
  icon?: ReactNode;
  /** 路由路径 */
  path?: string;
  /** 子菜单项 */
  children?: NavigationItem[];
  /** 是否禁用 */
  disabled?: boolean;
}

/**
 * 路由守卫上下文接口
 */
export interface RouteGuardContext {
  /** 目标路由路径 */
  to: string;
  /** 来源路由路径 */
  from: string;
  /** 路由元信息 */
  meta: RouteMeta;
}

/**
 * 路由守卫返回类型
 */
export type RouteGuardResult = boolean | string | void;

/**
 * 路由守卫函数类型
 */
export type RouteGuard = (context: RouteGuardContext) => RouteGuardResult | Promise<RouteGuardResult>;