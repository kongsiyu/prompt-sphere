/**
 * AppLayout 布局组件
 * 使用新的 AppLayout 组件的布局容器
 */

import React from 'react';
import { AppLayout as AppLayoutComponent } from '../components/layout/AppLayout';

interface AppLayoutProps {
  children: React.ReactNode;
}

/**
 * 应用程序布局容器
 */
const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  return (
    <AppLayoutComponent
      showSidebar={true}
      showHeader={true}
      showFooter={false}
      showBreadcrumb={true}
      layout="full-width"
      maxWidth="full"
      simpleFooter={true}
    >
      {children}
    </AppLayoutComponent>
  );
};

export default AppLayout;