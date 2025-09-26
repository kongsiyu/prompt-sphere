import { useLocation, useNavigate } from 'react-router-dom';
import { useMemo } from 'react';
import { navigationItems, findRouteByPath, getBreadcrumb } from '../router/routes';
import { NavigationItem, BreadcrumbItem, RouteMeta } from '../types/router';

/**
 * 导航相关的自定义Hook
 */
export const useNavigation = () => {
  const location = useLocation();
  const navigate = useNavigate();

  /**
   * 当前路径信息
   */
  const currentPath = location.pathname;
  const currentRoute = useMemo(() => findRouteByPath(currentPath), [currentPath]);

  /**
   * 面包屑导航
   */
  const breadcrumb = useMemo(() => getBreadcrumb(currentPath), [currentPath]);

  /**
   * 当前页面元信息
   */
  const currentMeta: RouteMeta | null = currentRoute?.meta || null;

  /**
   * 页面标题
   */
  const pageTitle = currentMeta?.title || '页面未找到';

  /**
   * 是否需要认证
   */
  const requiresAuth = currentMeta?.requiresAuth || false;

  /**
   * 获取过滤后的导航菜单项（根据认证状态）
   */
  const getFilteredNavigationItems = (): NavigationItem[] => {
    const isAuthenticated = !!localStorage.getItem('authToken');

    return navigationItems.filter(item => {
      if (item.requiresAuth && !isAuthenticated) {
        return false;
      }
      return true;
    }).map(item => ({
      ...item,
      icon: undefined // 在hook中不处理图标，由组件处理
    }));
  };

  /**
   * 检查当前路径是否为活跃状态
   */
  const isActiveRoute = (path: string): boolean => {
    if (path === '/' && currentPath === '/') {
      return true;
    }
    if (path !== '/' && currentPath.startsWith(path)) {
      return true;
    }
    return false;
  };

  /**
   * 导航到指定路径
   */
  const navigateTo = (path: string, options?: { replace?: boolean; state?: any }) => {
    navigate(path, options);
  };

  /**
   * 返回上一页
   */
  const goBack = () => {
    navigate(-1);
  };

  /**
   * 前进到下一页
   */
  const goForward = () => {
    navigate(1);
  };

  /**
   * 获取查询参数
   */
  const getSearchParams = () => {
    return new URLSearchParams(location.search);
  };

  /**
   * 获取特定查询参数的值
   */
  const getSearchParam = (key: string): string | null => {
    return getSearchParams().get(key);
  };

  /**
   * 更新查询参数
   */
  const updateSearchParams = (params: Record<string, string | null>) => {
    const searchParams = getSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value === null) {
        searchParams.delete(key);
      } else {
        searchParams.set(key, value);
      }
    });

    const newSearch = searchParams.toString();
    const newPath = `${location.pathname}${newSearch ? `?${newSearch}` : ''}`;
    navigate(newPath, { replace: true });
  };

  /**
   * 检查是否在指定路径的子路径中
   */
  const isInSection = (basePath: string): boolean => {
    return currentPath.startsWith(basePath);
  };

  return {
    // 路径信息
    currentPath,
    currentRoute,
    currentMeta,
    pageTitle,
    requiresAuth,

    // 导航数据
    breadcrumb,
    navigationItems: getFilteredNavigationItems(),

    // 状态检查
    isActiveRoute,
    isInSection,

    // 导航方法
    navigateTo,
    goBack,
    goForward,

    // 查询参数
    getSearchParams,
    getSearchParam,
    updateSearchParams,

    // 原始对象（需要时使用）
    location,
    navigate
  };
};

/**
 * 页面标题Hook - 用于设置文档标题
 */
export const usePageTitle = (title?: string) => {
  const { pageTitle } = useNavigation();
  const finalTitle = title || pageTitle;

  // 设置文档标题
  document.title = `${finalTitle} - AI System Prompt Generator`;
};

/**
 * 面包屑Hook - 专门用于面包屑组件
 */
export const useBreadcrumb = (): BreadcrumbItem[] => {
  const { breadcrumb } = useNavigation();
  return breadcrumb;
};