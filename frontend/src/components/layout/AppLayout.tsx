/**
 * AppLayout 组件
 * 主应用程序布局组件，整合头部、侧边栏、底部等组件
 * 为整个应用提供统一的布局结构
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Layout } from './Layout';
import { Header } from './Header';
import { Footer } from './Footer';
import Sidebar from '../navigation/Sidebar';
import Breadcrumb from '../navigation/Breadcrumb';
import { cn } from '@/utils/cn';
import {
  Home,
  MessageSquare,
  File,
  Settings,
  Plus
} from 'lucide-react';

export interface AppLayoutProps {
  /** 子组件 */
  children: React.ReactNode;
  /** 自定义类名 */
  className?: string;
  /** 是否显示侧边栏 */
  showSidebar?: boolean;
  /** 是否显示头部 */
  showHeader?: boolean;
  /** 是否显示底部 */
  showFooter?: boolean;
  /** 是否显示面包屑导航 */
  showBreadcrumb?: boolean;
  /** 布局类型 */
  layout?: 'default' | 'centered' | 'full-width' | 'sidebar-left';
  /** 主内容区域的最大宽度 */
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | '6xl' | '7xl' | 'full';
  /** 是否使用简化底部 */
  simpleFooter?: boolean;
  /** 内容区域布局模式 */
  contentLayout?: 'contained' | 'full-width';
}

/**
 * AppLayout 组件
 *
 * @example
 * ```tsx
 * // 基础应用布局
 * <AppLayout>
 *   <Dashboard />
 * </AppLayout>
 *
 * // 带侧边栏的应用布局
 * <AppLayout showSidebar layout="sidebar-left">
 *   <MainContent />
 * </AppLayout>
 *
 * // 全宽布局
 * <AppLayout layout="full-width" showSidebar={false}>
 *   <FullWidthContent />
 * </AppLayout>
 * ```
 */
export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  className,
  showSidebar = true,
  showHeader = true,
  showFooter = false,
  showBreadcrumb = true,
  layout = 'sidebar-left',
  maxWidth = 'full',
  simpleFooter = true,
  contentLayout = 'contained',
}) => {
  return (
    <Layout
      className={cn('bg-gray-50 min-h-screen', className)}
      showHeader={showHeader}
      showFooter={showFooter}
      showSidebar={showSidebar}
      layout={layout}
      maxWidth={maxWidth}
      sidebar={<AppSidebar />}
      headerProps={{
        title: 'AI System Prompt Generator',
        showMenuButton: showSidebar,
        showThemeToggle: true,
        showUserMenu: true,
      }}
      footerProps={{
        showDetails: !simpleFooter,
        copyrightYear: new Date().getFullYear(),
        copyrightOwner: 'AI System Prompt Generator',
        version: '1.0.0',
      }}
    >
      <div className="h-full flex flex-col">
        {/* 面包屑导航 */}
        {showBreadcrumb && (
          <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
            <Breadcrumb />
          </div>
        )}

        {/* 主要内容 */}
        <div className="flex-1">
          {contentLayout === 'full-width' ? (
            // 全宽模式：提示词编辑等需要更多空间的页面
            <div className="px-6 py-6 h-full">
              {children}
            </div>
          ) : (
            // 容器模式：常规页面，更好的可读性
            <div className="max-w-7xl mx-auto px-6 py-6">
              {children}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

/**
 * AppSidebar 组件
 * 应用程序侧边栏内容
 */
const AppSidebar: React.FC = () => {
  const location = useLocation();
  const isAuthenticated = !!localStorage.getItem('authToken');

  // 导航项
  const navItems = [
    { key: '/', label: '首页', icon: 'Home', path: '/', requiresAuth: false },
    { key: '/dashboard', label: '工作台', icon: 'Home', path: '/dashboard', requiresAuth: true },
    { key: '/prompts', label: '提示词管理', icon: 'MessageSquare', path: '/prompts', requiresAuth: true },
    { key: '/templates', label: '模板库', icon: 'File', path: '/templates', requiresAuth: true },
    { key: '/settings', label: '用户设置', icon: 'Settings', path: '/settings', requiresAuth: true },
  ];

  // 图标映射
  const iconMap: Record<string, React.ReactNode> = {
    Home: <Home className="h-5 w-5" />,
    MessageSquare: <MessageSquare className="h-5 w-5" />,
    File: <File className="h-5 w-5" />,
    Settings: <Settings className="h-5 w-5" />
  };

  // 过滤需要认证的菜单项
  const filteredNavItems = navItems.filter(
    item => !item.requiresAuth || isAuthenticated
  );

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white">
      {/* 导航菜单 */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {filteredNavItems.map(item => (
          <Link
            key={item.key}
            to={item.path}
            className={`
              flex items-center px-3 py-3 rounded-lg text-sm font-medium transition-all duration-200
              ${location.pathname === item.path
                ? 'bg-blue-600 text-white shadow-lg'
                : 'text-gray-300 hover:text-white hover:bg-gray-800'
              }
            `}
          >
            <span className="flex-shrink-0">{iconMap[item.icon || 'Home']}</span>
            <span className="ml-3">{item.label}</span>
          </Link>
        ))}

        {/* 快速操作按钮 */}
        {isAuthenticated && (
          <div className="pt-6 border-t border-gray-700">
            <Link
              to="/prompt-editor/create"
              className="flex items-center px-3 py-3 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 transition-all duration-200 shadow-lg w-full justify-center"
            >
              <Plus className="h-4 w-4 flex-shrink-0" />
              <span className="ml-2">创建提示词</span>
            </Link>
          </div>
        )}
      </nav>

      {/* 侧边栏底部信息 */}
      <div className="p-4 border-t border-gray-700">
        <div className="text-xs text-gray-400 text-center">
          <p>AI System Prompt Generator</p>
          <p className="mt-1">v1.0.0</p>
        </div>
      </div>
    </div>
  );
};

export default AppLayout;