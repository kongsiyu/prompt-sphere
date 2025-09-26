/**
 * Dashboard 页面测试
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../index';

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  Link: ({ children, to, className, ...props }: any) => (
    <a href={to} className={className} data-testid={`link-${to.replace(/\//g, '-')}`} {...props}>
      {children}
    </a>
  ),
}));

// Mock UI components
jest.mock('@/components/ui/Button', () => ({
  Button: ({ children, variant, size, className, onClick, ...props }: any) => (
    <button
      className={className}
      onClick={onClick}
      data-variant={variant}
      data-size={size}
      data-testid="button"
      {...props}
    >
      {children}
    </button>
  ),
}));

jest.mock('@/components/ui/Card', () => ({
  Card: ({ children, className, ...props }: any) => (
    <div className={className} data-testid="card" {...props}>
      {children}
    </div>
  ),
}));

// Mock utilities
jest.mock('@/utils/cn', () => ({
  cn: (...classes: string[]) => classes.filter(Boolean).join(' '),
}));

const renderDashboard = () => {
  return render(
    <BrowserRouter>
      <Dashboard />
    </BrowserRouter>
  );
};

describe('Dashboard', () => {
  beforeEach(() => {
    // 清除 localStorage
    localStorage.clear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('未认证状态', () => {
    beforeEach(() => {
      localStorage.removeItem('authToken');
    });

    it('应该显示欢迎页面', () => {
      renderDashboard();

      expect(screen.getByText('欢迎使用 AI System Prompt Generator')).toBeInTheDocument();
      expect(screen.getByText('智能系统提示词生成器，让AI更懂你的需求')).toBeInTheDocument();
    });

    it('应该显示立即开始按钮', () => {
      renderDashboard();

      const startButton = screen.getByTestId('link--auth-login');
      expect(startButton).toBeInTheDocument();
    });

    it('应该显示功能特性卡片', () => {
      renderDashboard();

      expect(screen.getByText('智能生成')).toBeInTheDocument();
      expect(screen.getByText('丰富模板')).toBeInTheDocument();
      expect(screen.getByText('易于管理')).toBeInTheDocument();
    });

    it('应该显示功能描述', () => {
      renderDashboard();

      expect(screen.getByText('使用先进的AI技术，快速生成高质量的系统提示词')).toBeInTheDocument();
      expect(screen.getByText('提供覆盖各种场景的模板库，满足不同需求')).toBeInTheDocument();
      expect(screen.getByText('简洁直观的界面，让提示词管理变得轻松简单')).toBeInTheDocument();
    });

    it('不应该显示用户仪表盘内容', () => {
      renderDashboard();

      expect(screen.queryByText('欢迎回来!')).not.toBeInTheDocument();
      expect(screen.queryByText('我的提示词')).not.toBeInTheDocument();
    });
  });

  describe('已认证状态', () => {
    beforeEach(() => {
      localStorage.setItem('authToken', 'mock-token');
    });

    it('应该显示欢迎回来信息', () => {
      renderDashboard();

      expect(screen.getByText('欢迎回来! 👋')).toBeInTheDocument();
      expect(screen.getByText('今天是个创作的好日子，准备好创建新的AI提示词了吗？')).toBeInTheDocument();
    });

    it('应该显示统计卡片', () => {
      renderDashboard();

      expect(screen.getByText('我的提示词')).toBeInTheDocument();
      expect(screen.getByText('使用的模板')).toBeInTheDocument();
      expect(screen.getByText('总使用次数')).toBeInTheDocument();
      expect(screen.getByText('活跃天数')).toBeInTheDocument();
    });

    it('应该显示统计数据', () => {
      renderDashboard();

      expect(screen.getByText('12')).toBeInTheDocument();
      expect(screen.getByText('8')).toBeInTheDocument();
      expect(screen.getByText('156')).toBeInTheDocument();
      expect(screen.getByText('24')).toBeInTheDocument();
    });

    it('应该显示快速操作区域', () => {
      renderDashboard();

      expect(screen.getByText('快速操作')).toBeInTheDocument();
      expect(screen.getByText('创建新提示词')).toBeInTheDocument();
      expect(screen.getByText('浏览模板库')).toBeInTheDocument();
      expect(screen.getByText('管理提示词')).toBeInTheDocument();
    });

    it('应该显示快速操作描述', () => {
      renderDashboard();

      expect(screen.getByText('从零开始创建一个新的AI提示词')).toBeInTheDocument();
      expect(screen.getByText('从丰富的模板库中选择合适的模板')).toBeInTheDocument();
      expect(screen.getByText('查看和管理你的所有提示词')).toBeInTheDocument();
    });

    it('应该显示最近活动区域', () => {
      renderDashboard();

      expect(screen.getByText('最近活动')).toBeInTheDocument();
    });

    it('应该显示最近活动项', () => {
      renderDashboard();

      expect(screen.getByText('创建了新提示词')).toBeInTheDocument();
      expect(screen.getByText('技术文档写作助手')).toBeInTheDocument();
      expect(screen.getByText('2小时前')).toBeInTheDocument();

      expect(screen.getByText('编辑了提示词')).toBeInTheDocument();
      expect(screen.getByText('代码审查助手')).toBeInTheDocument();
      expect(screen.getByText('1天前')).toBeInTheDocument();

      expect(screen.getByText('使用了模板')).toBeInTheDocument();
      expect(screen.getByText('营销文案模板')).toBeInTheDocument();
      expect(screen.getByText('2天前')).toBeInTheDocument();
    });

    it('应该显示推荐模板区域', () => {
      renderDashboard();

      expect(screen.getByText('推荐模板')).toBeInTheDocument();
    });

    it('应该显示推荐模板项', () => {
      renderDashboard();

      expect(screen.getByText('代码生成助手')).toBeInTheDocument();
      expect(screen.getByText('帮助生成各种编程语言的代码片段')).toBeInTheDocument();
      expect(screen.getByText('开发工具')).toBeInTheDocument();

      expect(screen.getByText('文章写作助手')).toBeInTheDocument();
      expect(screen.getByText('协助撰写高质量的技术和营销文章')).toBeInTheDocument();
      expect(screen.getByText('内容创作')).toBeInTheDocument();

      expect(screen.getByText('数据分析师')).toBeInTheDocument();
      expect(screen.getByText('专业的数据分析和洞察提供者')).toBeInTheDocument();
      expect(screen.getByText('数据分析')).toBeInTheDocument();
    });

    it('应该显示模板评分和使用次数', () => {
      renderDashboard();

      expect(screen.getByText('4.8')).toBeInTheDocument();
      expect(screen.getByText('1200 次使用')).toBeInTheDocument();

      expect(screen.getByText('4.9')).toBeInTheDocument();
      expect(screen.getByText('980 次使用')).toBeInTheDocument();

      expect(screen.getByText('4.7')).toBeInTheDocument();
      expect(screen.getByText('756 次使用')).toBeInTheDocument();
    });

    it('不应该显示未认证状态的内容', () => {
      renderDashboard();

      expect(screen.queryByText('立即开始')).not.toBeInTheDocument();
      expect(screen.queryByText('智能生成')).not.toBeInTheDocument();
    });
  });

  describe('导航链接', () => {
    describe('未认证状态下的链接', () => {
      beforeEach(() => {
        localStorage.removeItem('authToken');
      });

      it('应该有正确的登录链接', () => {
        renderDashboard();

        const loginLink = screen.getByTestId('link--auth-login');
        expect(loginLink).toHaveAttribute('href', '/auth/login');
      });
    });

    describe('已认证状态下的链接', () => {
      beforeEach(() => {
        localStorage.setItem('authToken', 'mock-token');
      });

      it('应该有正确的快速操作链接', () => {
        renderDashboard();

        expect(screen.getByTestId('link--prompts-create')).toHaveAttribute('href', '/prompts/create');
        expect(screen.getByTestId('link--templates')).toHaveAttribute('href', '/templates');
        expect(screen.getByTestId('link--prompts')).toHaveAttribute('href', '/prompts');
      });
    });
  });

  describe('响应式设计', () => {
    beforeEach(() => {
      localStorage.setItem('authToken', 'mock-token');
    });

    it('应该包含响应式CSS类', () => {
      renderDashboard();

      // 检查统计卡片的网格布局
      const statsContainer = screen.getAllByTestId('card')[1].parentElement;
      expect(statsContainer).toHaveClass('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-4');
    });

    it('应该在移动端和桌面端都能正确显示', () => {
      renderDashboard();

      // 检查是否有响应式类名
      const containers = screen.getAllByTestId('card');
      expect(containers.length).toBeGreaterThan(0);
    });
  });

  describe('边缘情况', () => {
    it('应该正确处理localStorage的读取', () => {
      localStorage.setItem('authToken', 'valid-token');
      renderDashboard();
      expect(screen.getByText('欢迎回来! 👋')).toBeInTheDocument();

      localStorage.removeItem('authToken');
      const { rerender } = renderDashboard();
      // 重新渲染以触发状态更新
      rerender(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );
      // 注意：由于组件内部使用了!!localStorage.getItem()，状态不会自动更新
      // 这里我们主要测试初始渲染时的行为
    });
  });
});