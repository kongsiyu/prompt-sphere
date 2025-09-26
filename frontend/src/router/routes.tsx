import { lazy } from 'react';
import { RouteConfig } from '../types/router';

// 懒加载页面组件
const HomePage = lazy(() => import('../pages/Home'));
const LoginPage = lazy(() => import('../pages/auth/Login'));
const PromptsPage = lazy(() => import('../pages/prompts/Prompts'));
const CreatePromptPage = lazy(() => import('../pages/prompts/CreatePrompt'));
const EditPromptPage = lazy(() => import('../pages/prompts/EditPrompt'));
const PromptEditorPage = lazy(() => import('../pages/PromptEditor'));
const TemplatesPage = lazy(() => import('../pages/templates/Templates'));
const SettingsPage = lazy(() => import('../pages/settings/Settings'));
const NotFoundPage = lazy(() => import('../pages/NotFound'));

/**
 * 路由配置定义
 */
export const routes: RouteConfig[] = [
  {
    path: '/',
    component: HomePage,
    meta: {
      title: '首页',
      icon: 'Home',
      breadcrumb: [{ label: '首页', path: '/', isActive: true }]
    }
  },
  {
    path: '/auth/login',
    component: LoginPage,
    meta: {
      title: '登录',
      layout: 'auth',
      hideInNav: true,
      breadcrumb: [
        { label: '首页', path: '/' },
        { label: '登录', isActive: true }
      ]
    }
  },
  {
    path: '/prompts',
    component: PromptsPage,
    meta: {
      title: '提示词管理',
      icon: 'MessageSquare',
      requiresAuth: true,
      breadcrumb: [
        { label: '首页', path: '/' },
        { label: '提示词管理', path: '/prompts', isActive: true }
      ]
    }
  },
  {
    path: '/prompts/create',
    component: CreatePromptPage,
    meta: {
      title: '创建提示词',
      requiresAuth: true,
      hideInNav: true,
      breadcrumb: [
        { label: '首页', path: '/' },
        { label: '提示词管理', path: '/prompts' },
        { label: '创建提示词', isActive: true }
      ]
    }
  },
  {
    path: '/prompts/:id/edit',
    component: EditPromptPage,
    meta: {
      title: '编辑提示词',
      requiresAuth: true,
      hideInNav: true,
      breadcrumb: [
        { label: '首页', path: '/' },
        { label: '提示词管理', path: '/prompts' },
        { label: '编辑提示词', isActive: true }
      ]
    }
  },
  {
    path: '/prompt-editor/create',
    component: PromptEditorPage,
    meta: {
      title: '统一提示词创建界面',
      requiresAuth: true,
      hideInNav: true,
      breadcrumb: [
        { label: '首页', path: '/' },
        { label: '提示词管理', path: '/prompts' },
        { label: '创建提示词', isActive: true }
      ]
    }
  },
  {
    path: '/prompt-editor/:id/edit',
    component: PromptEditorPage,
    meta: {
      title: '统一提示词编辑界面',
      requiresAuth: true,
      hideInNav: true,
      breadcrumb: [
        { label: '首页', path: '/' },
        { label: '提示词管理', path: '/prompts' },
        { label: '编辑提示词', isActive: true }
      ]
    }
  },
  {
    path: '/templates',
    component: TemplatesPage,
    meta: {
      title: '模板库',
      icon: 'FileTemplate',
      requiresAuth: true,
      breadcrumb: [
        { label: '首页', path: '/' },
        { label: '模板库', path: '/templates', isActive: true }
      ]
    }
  },
  {
    path: '/settings',
    component: SettingsPage,
    meta: {
      title: '用户设置',
      icon: 'Settings',
      requiresAuth: true,
      breadcrumb: [
        { label: '首页', path: '/' },
        { label: '用户设置', path: '/settings', isActive: true }
      ]
    }
  },
  {
    path: '*',
    component: NotFoundPage,
    meta: {
      title: '页面未找到',
      hideInNav: true,
      breadcrumb: [
        { label: '首页', path: '/' },
        { label: '页面未找到', isActive: true }
      ]
    }
  }
];

/**
 * 导航菜单配置 - 从路由配置中提取导航项
 */
export const navigationItems = routes
  .filter(route => !route.meta.hideInNav && route.path !== '*')
  .map(route => ({
    key: route.path,
    label: route.meta.title,
    icon: route.meta.icon,
    path: route.path,
    requiresAuth: route.meta.requiresAuth
  }));

/**
 * 根据路径查找路由配置
 */
export const findRouteByPath = (path: string): RouteConfig | undefined => {
  return routes.find(route => {
    if (route.path === path) return true;
    // 处理动态路由参数
    if (route.path.includes(':')) {
      const routePattern = route.path.replace(/:\w+/g, '[^/]+');
      const regex = new RegExp(`^${routePattern}$`);
      return regex.test(path);
    }
    return false;
  });
};

/**
 * 获取路由面包屑导航
 */
export const getBreadcrumb = (path: string): import('../types/router').BreadcrumbItem[] => {
  const route = findRouteByPath(path);
  return route?.meta.breadcrumb || [{ label: '首页', path: '/', isActive: true }];
};