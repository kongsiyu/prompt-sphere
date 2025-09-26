/**
 * Layout 组件
 * 应用主布局组件，包含头部、主内容区域、侧边栏、底部等
 */

import React, { useState } from 'react';
import { cn } from '@/utils/cn';
import { Header } from './Header';
import { Footer } from './Footer';

export interface LayoutProps {
  /** 子组件 */
  children: React.ReactNode;
  /** 自定义类名 */
  className?: string;
  /** 是否显示头部 */
  showHeader?: boolean;
  /** 是否显示底部 */
  showFooter?: boolean;
  /** 是否显示侧边栏 */
  showSidebar?: boolean;
  /** 侧边栏内容 */
  sidebar?: React.ReactNode;
  /** 头部配置 */
  headerProps?: Partial<React.ComponentProps<typeof Header>>;
  /** 底部配置 */
  footerProps?: Partial<React.ComponentProps<typeof Footer>>;
  /** 布局类型 */
  layout?: 'default' | 'centered' | 'full-width' | 'sidebar-left' | 'sidebar-right';
  /** 主内容区域的最大宽度 */
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | '6xl' | '7xl' | 'full';
  /** 是否固定侧边栏 */
  fixedSidebar?: boolean;
  /** 侧边栏初始状态（移动端） */
  defaultSidebarOpen?: boolean;
}

/**
 * Layout 组件
 *
 * @example
 * ```tsx
 * // 基础布局
 * <Layout>
 *   <div>页面内容</div>
 * </Layout>
 *
 * // 带侧边栏的布局
 * <Layout
 *   layout="sidebar-left"
 *   showSidebar
 *   sidebar={<Sidebar />}
 * >
 *   <div>主要内容</div>
 * </Layout>
 *
 * // 居中布局
 * <Layout layout="centered" maxWidth="2xl">
 *   <div>居中内容</div>
 * </Layout>
 * ```
 */
export const Layout: React.FC<LayoutProps> = ({
  children,
  className,
  showHeader = true,
  showFooter = true,
  showSidebar = false,
  sidebar,
  headerProps = {},
  footerProps = {},
  layout = 'default',
  maxWidth = '7xl',
  fixedSidebar = true,
  defaultSidebarOpen = false,
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(defaultSidebarOpen);

  // 最大宽度类映射
  const maxWidthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    '3xl': 'max-w-3xl',
    '4xl': 'max-w-4xl',
    '5xl': 'max-w-5xl',
    '6xl': 'max-w-6xl',
    '7xl': 'max-w-7xl',
    full: 'max-w-full',
  };

  // 处理菜单点击
  const handleMenuClick = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // 渲染侧边栏覆盖层（移动端）
  const renderSidebarOverlay = () => {
    if (!showSidebar || !sidebarOpen) return null;

    return (
      <div
        className="fixed inset-0 z-40 bg-black/50 lg:hidden"
        onClick={() => setSidebarOpen(false)}
        aria-hidden="true"
      />
    );
  };

  // 渲染侧边栏
  const renderSidebar = () => {
    if (!showSidebar || !sidebar) return null;

    return (
      <aside
        className={cn(
          'bg-background border-r transition-all duration-300 ease-in-out',
          {
            // 移动端样式
            'fixed inset-y-0 left-0 z-50 w-64 transform lg:relative lg:translate-x-0':
              layout === 'sidebar-left',
            'fixed inset-y-0 right-0 z-50 w-64 transform lg:relative lg:translate-x-0':
              layout === 'sidebar-right',
            // 桌面端样式
            'lg:sticky lg:top-16 lg:h-[calc(100vh-4rem)]': fixedSidebar,
            'lg:w-64 lg:flex-shrink-0': true,
            // 移动端显示/隐藏
            '-translate-x-full': layout === 'sidebar-left' && !sidebarOpen,
            'translate-x-full': layout === 'sidebar-right' && !sidebarOpen,
            'translate-x-0': sidebarOpen,
          }
        )}
      >
        <div className="h-full overflow-y-auto p-4">
          {sidebar}
        </div>
      </aside>
    );
  };

  // 渲染主内容
  const renderMainContent = () => {
    const containerClasses = cn(
      'flex-1 min-h-0',
      {
        // 基础布局
        'container mx-auto px-4': layout === 'default',
        // 居中布局
        'container mx-auto px-4 flex items-center justify-center min-h-[60vh]':
          layout === 'centered',
        // 全宽布局
        'w-full': layout === 'full-width',
        // 侧边栏布局
        'flex-1': layout === 'sidebar-left' || layout === 'sidebar-right',
      },
      layout !== 'full-width' && layout !== 'sidebar-left' && layout !== 'sidebar-right'
        ? maxWidthClasses[maxWidth]
        : ''
    );

    if (layout === 'centered') {
      return (
        <main className={containerClasses}>
          <div className={cn('w-full', maxWidthClasses[maxWidth])}>
            {children}
          </div>
        </main>
      );
    }

    return (
      <main className={containerClasses}>
        <div className="py-6">
          {children}
        </div>
      </main>
    );
  };

  return (
    <div className={cn('min-h-screen flex flex-col', className)}>
      {/* 头部 */}
      {showHeader && (
        <Header
          showMenuButton={showSidebar}
          onMenuClick={handleMenuClick}
          {...headerProps}
        />
      )}

      {/* 主体区域 */}
      <div className="flex-1 flex">
        {/* 侧边栏覆盖层 */}
        {renderSidebarOverlay()}

        {/* 左侧边栏 */}
        {layout === 'sidebar-left' && renderSidebar()}

        {/* 主内容区域 */}
        {renderMainContent()}

        {/* 右侧边栏 */}
        {layout === 'sidebar-right' && renderSidebar()}
      </div>

      {/* 底部 */}
      {showFooter && <Footer {...footerProps} />}
    </div>
  );
};