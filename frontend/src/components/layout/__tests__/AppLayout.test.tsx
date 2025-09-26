/**
 * AppLayout 组件测试
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AppLayout } from '../AppLayout';

// Mock child components
jest.mock('../Layout', () => ({
  Layout: ({ children, ...props }: any) => (
    <div data-testid="layout" data-layout-props={JSON.stringify(props)}>
      {children}
    </div>
  ),
}));

jest.mock('../Header', () => ({
  Header: () => <div data-testid="header">Header</div>,
}));

jest.mock('../Footer', () => ({
  Footer: () => <div data-testid="footer">Footer</div>,
}));

jest.mock('../../navigation/Sidebar', () => ({
  __esModule: true,
  default: () => <div data-testid="sidebar">Sidebar</div>,
}));

jest.mock('../../navigation/Breadcrumb', () => ({
  __esModule: true,
  default: () => <div data-testid="breadcrumb">Breadcrumb</div>,
}));

// Mock hooks and utilities
jest.mock('@/utils/cn', () => ({
  cn: (...classes: string[]) => classes.join(' '),
}));

const renderAppLayout = (props = {}) => {
  return render(
    <BrowserRouter>
      <AppLayout {...props}>
        <div data-testid="content">Test Content</div>
      </AppLayout>
    </BrowserRouter>
  );
};

describe('AppLayout', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('基础渲染', () => {
    it('应该正确渲染默认配置的AppLayout', () => {
      renderAppLayout();

      expect(screen.getByTestId('layout')).toBeInTheDocument();
      expect(screen.getByTestId('breadcrumb')).toBeInTheDocument();
      expect(screen.getByTestId('content')).toBeInTheDocument();
    });

    it('应该渲染子组件内容', () => {
      renderAppLayout();

      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('应该应用自定义类名', () => {
      renderAppLayout({ className: 'custom-class' });

      const layout = screen.getByTestId('layout');
      const layoutProps = JSON.parse(layout.getAttribute('data-layout-props') || '{}');
      expect(layoutProps.className).toContain('custom-class');
    });
  });

  describe('布局配置', () => {
    it('应该支持隐藏侧边栏', () => {
      renderAppLayout({ showSidebar: false });

      const layout = screen.getByTestId('layout');
      const layoutProps = JSON.parse(layout.getAttribute('data-layout-props') || '{}');
      expect(layoutProps.showSidebar).toBe(false);
    });

    it('应该支持隐藏头部', () => {
      renderAppLayout({ showHeader: false });

      const layout = screen.getByTestId('layout');
      const layoutProps = JSON.parse(layout.getAttribute('data-layout-props') || '{}');
      expect(layoutProps.showHeader).toBe(false);
    });

    it('应该支持隐藏底部', () => {
      renderAppLayout({ showFooter: false });

      const layout = screen.getByTestId('layout');
      const layoutProps = JSON.parse(layout.getAttribute('data-layout-props') || '{}');
      expect(layoutProps.showFooter).toBe(false);
    });

    it('应该支持隐藏面包屑导航', () => {
      renderAppLayout({ showBreadcrumb: false });

      expect(screen.queryByTestId('breadcrumb')).not.toBeInTheDocument();
    });

    it('应该支持不同的布局类型', () => {
      renderAppLayout({ layout: 'full-width' });

      const layout = screen.getByTestId('layout');
      const layoutProps = JSON.parse(layout.getAttribute('data-layout-props') || '{}');
      expect(layoutProps.layout).toBe('full-width');
    });

    it('应该支持不同的最大宽度设置', () => {
      renderAppLayout({ maxWidth: '2xl' });

      const layout = screen.getByTestId('layout');
      const layoutProps = JSON.parse(layout.getAttribute('data-layout-props') || '{}');
      expect(layoutProps.maxWidth).toBe('2xl');
    });

    it('应该支持简化底部模式', () => {
      renderAppLayout({ simpleFooter: false });

      const layout = screen.getByTestId('layout');
      const layoutProps = JSON.parse(layout.getAttribute('data-layout-props') || '{}');
      expect(layoutProps.footerProps.showDetails).toBe(true);
    });
  });

  describe('默认配置', () => {
    it('应该使用正确的默认值', () => {
      renderAppLayout();

      const layout = screen.getByTestId('layout');
      const layoutProps = JSON.parse(layout.getAttribute('data-layout-props') || '{}');

      expect(layoutProps.showSidebar).toBe(true);
      expect(layoutProps.showHeader).toBe(true);
      expect(layoutProps.showFooter).toBe(true);
      expect(layoutProps.layout).toBe('sidebar-left');
      expect(layoutProps.maxWidth).toBe('7xl');
    });

    it('应该设置正确的头部配置', () => {
      renderAppLayout();

      const layout = screen.getByTestId('layout');
      const layoutProps = JSON.parse(layout.getAttribute('data-layout-props') || '{}');

      expect(layoutProps.headerProps.title).toBe('AI System Prompt Generator');
      expect(layoutProps.headerProps.showThemeToggle).toBe(true);
      expect(layoutProps.headerProps.showUserMenu).toBe(true);
    });

    it('应该设置正确的底部配置', () => {
      renderAppLayout();

      const layout = screen.getByTestId('layout');
      const layoutProps = JSON.parse(layout.getAttribute('data-layout-props') || '{}');

      expect(layoutProps.footerProps.copyrightOwner).toBe('AI System Prompt Generator');
      expect(layoutProps.footerProps.version).toBe('1.0.0');
      expect(layoutProps.footerProps.showDetails).toBe(false);
    });
  });

  describe('响应式行为', () => {
    it('应该在不同布局下正确显示内容', () => {
      const layouts = ['default', 'centered', 'full-width', 'sidebar-left'] as const;

      layouts.forEach(layout => {
        const { unmount } = renderAppLayout({ layout });

        expect(screen.getByTestId('content')).toBeInTheDocument();

        unmount();
      });
    });
  });

  describe('内容结构', () => {
    it('应该包含正确的内容结构', () => {
      renderAppLayout();

      // 检查是否有面包屑容器
      const breadcrumbContainer = screen.getByTestId('breadcrumb').parentElement;
      expect(breadcrumbContainer).toHaveClass('bg-white', 'rounded-lg', 'border', 'p-4');

      // 检查主要内容容器
      const content = screen.getByTestId('content');
      expect(content.parentElement).toHaveClass('min-h-[calc(100vh-16rem)]');
    });

    it('应该在隐藏面包屑时仍然显示主要内容', () => {
      renderAppLayout({ showBreadcrumb: false });

      expect(screen.queryByTestId('breadcrumb')).not.toBeInTheDocument();
      expect(screen.getByTestId('content')).toBeInTheDocument();
    });
  });

  describe('边缘情况', () => {
    it('应该处理空子组件', () => {
      render(
        <BrowserRouter>
          <AppLayout />
        </BrowserRouter>
      );

      expect(screen.getByTestId('layout')).toBeInTheDocument();
    });

    it('应该处理多个子组件', () => {
      render(
        <BrowserRouter>
          <AppLayout>
            <div data-testid="child1">Child 1</div>
            <div data-testid="child2">Child 2</div>
          </AppLayout>
        </BrowserRouter>
      );

      expect(screen.getByTestId('child1')).toBeInTheDocument();
      expect(screen.getByTestId('child2')).toBeInTheDocument();
    });
  });
});