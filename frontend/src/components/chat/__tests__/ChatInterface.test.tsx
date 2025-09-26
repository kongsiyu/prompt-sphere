/**
 * ChatInterface 组件测试
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ChatInterface } from '../ChatInterface';
import { AgentType, ChatMode } from '@/types/chat';

// Mock hooks
vi.mock('@/hooks/useChat', () => ({
  useChat: vi.fn(() => ({
    state: {
      currentSession: null,
      sessions: [],
      isConnected: true,
      connectionStatus: 'connected',
      isTyping: false,
      typingAgent: undefined,
      currentAgent: 'pe_engineer',
      currentMode: 'create',
      messageLimit: 100,
      isLoading: false,
      error: undefined
    },
    sendMessage: vi.fn(),
    switchAgent: vi.fn(),
    switchMode: vi.fn(),
    createSession: vi.fn(),
    switchSession: vi.fn(),
    deleteSession: vi.fn(),
    clearMessages: vi.fn(),
    retryMessage: vi.fn(),
    deleteMessage: vi.fn(),
    copyMessage: vi.fn()
  }))
}));

vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: vi.fn(() => ({
    isConnected: true,
    connectionStatus: 'connected',
    sendMessage: vi.fn(),
    onMessage: vi.fn(() => () => {}),
    connect: vi.fn(),
    disconnect: vi.fn(),
    reconnect: vi.fn(),
    onConnect: vi.fn(() => () => {}),
    onDisconnect: vi.fn(() => () => {}),
    onError: vi.fn(() => () => {})
  }))
}));

describe('ChatInterface Component', () => {
  const mockOnAgentChange = vi.fn();
  const mockOnModeChange = vi.fn();
  const mockOnClose = vi.fn();
  const mockOnPromptUpdate = vi.fn();

  const defaultProps = {
    onAgentChange: mockOnAgentChange,
    onModeChange: mockOnModeChange,
    onClose: mockOnClose,
    onPromptUpdate: mockOnPromptUpdate
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('基础渲染', () => {
    it('应该渲染聊天界面', () => {
      render(<ChatInterface {...defaultProps} />);

      expect(screen.getByText('聊天助手')).toBeInTheDocument();
      expect(screen.getByText('已连接到聊天服务')).toBeInTheDocument();
    });

    it('应该显示Agent选择器', () => {
      render(<ChatInterface {...defaultProps} showAgentSelector={true} />);

      expect(screen.getByText('Agent:')).toBeInTheDocument();
      expect(screen.getByText('PE Engineer')).toBeInTheDocument();
      expect(screen.getByText('PEQA')).toBeInTheDocument();
    });

    it('应该显示模式选择器', () => {
      render(<ChatInterface {...defaultProps} showModeSelector={true} />);

      expect(screen.getByText('模式:')).toBeInTheDocument();
      expect(screen.getByText('创建模式')).toBeInTheDocument();
      expect(screen.getByText('优化模式')).toBeInTheDocument();
      expect(screen.getByText('质量检查')).toBeInTheDocument();
    });

    it('应该隐藏Agent选择器当设置为false时', () => {
      render(<ChatInterface {...defaultProps} showAgentSelector={false} />);

      expect(screen.queryByText('Agent:')).not.toBeInTheDocument();
    });

    it('应该隐藏模式选择器当设置为false时', () => {
      render(<ChatInterface {...defaultProps} showModeSelector={false} />);

      expect(screen.queryByText('模式:')).not.toBeInTheDocument();
    });
  });

  describe('Agent切换', () => {
    it('应该切换到PEQA agent', async () => {
      const user = userEvent.setup();
      render(<ChatInterface {...defaultProps} showAgentSelector={true} />);

      const peqaButton = screen.getByRole('button', { name: /PEQA/ });
      await user.click(peqaButton);

      expect(mockOnAgentChange).toHaveBeenCalledWith('peqa');
    });

    it('应该高亮显示当前选中的Agent', () => {
      render(
        <ChatInterface
          {...defaultProps}
          defaultAgent="peqa"
          showAgentSelector={true}
        />
      );

      const peqaButton = screen.getByRole('button', { name: /PEQA/ });
      expect(peqaButton).toHaveClass('bg-primary'); // 或者其他表示选中的样式类
    });
  });

  describe('模式切换', () => {
    it('应该切换到优化模式', async () => {
      const user = userEvent.setup();
      render(<ChatInterface {...defaultProps} showModeSelector={true} />);

      const optimizeButton = screen.getByRole('button', { name: /优化模式/ });
      await user.click(optimizeButton);

      expect(mockOnModeChange).toHaveBeenCalledWith('optimize');
    });

    it('应该切换到质量检查模式', async () => {
      const user = userEvent.setup();
      render(<ChatInterface {...defaultProps} showModeSelector={true} />);

      const qualityCheckButton = screen.getByRole('button', { name: /质量检查/ });
      await user.click(qualityCheckButton);

      expect(mockOnModeChange).toHaveBeenCalledWith('quality_check');
    });

    it('应该高亮显示当前选中的模式', () => {
      render(
        <ChatInterface
          {...defaultProps}
          defaultMode="optimize"
          showModeSelector={true}
        />
      );

      const optimizeButton = screen.getByRole('button', { name: /优化模式/ });
      expect(optimizeButton).toHaveClass('bg-primary'); // 或者其他表示选中的样式类
    });
  });

  describe('消息发送', () => {
    it('应该发送消息', async () => {
      const user = userEvent.setup();
      render(<ChatInterface {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/与.*对话.../);
      const sendButton = screen.getByTitle('发送消息 (Enter)');

      await user.type(textarea, '测试消息');
      await user.click(sendButton);

      // 验证消息被发送（通过useChat mock）
      await waitFor(() => {
        expect(textarea).toHaveValue('');
      });
    });

    it('应该包含提示词上下文', async () => {
      const user = userEvent.setup();
      const promptContext = '当前提示词内容';

      render(
        <ChatInterface
          {...defaultProps}
          promptContext={promptContext}
          defaultMode="optimize"
        />
      );

      const textarea = screen.getByPlaceholderText(/与.*对话.../);
      const sendButton = screen.getByTitle('发送消息 (Enter)');

      await user.type(textarea, '请优化这个提示词');
      await user.click(sendButton);

      // 在优化模式下，应该包含提示词上下文
      // 这里需要通过mock验证实际调用的参数
    });
  });

  describe('连接状态', () => {
    it('应该显示连接状态', () => {
      render(<ChatInterface {...defaultProps} />);

      expect(screen.getByText('已连接到聊天服务')).toBeInTheDocument();
    });

    it('应该显示断开连接状态', () => {
      // 这里需要mock useChat返回断开状态
      vi.mocked(require('@/hooks/useChat').useChat).mockReturnValue({
        state: {
          currentSession: null,
          sessions: [],
          isConnected: false,
          connectionStatus: 'disconnected',
          isTyping: false,
          typingAgent: undefined,
          currentAgent: 'pe_engineer',
          currentMode: 'create',
          messageLimit: 100,
          isLoading: false,
          error: undefined
        },
        sendMessage: vi.fn(),
        switchAgent: vi.fn(),
        switchMode: vi.fn(),
        createSession: vi.fn(),
        switchSession: vi.fn(),
        deleteSession: vi.fn(),
        clearMessages: vi.fn(),
        retryMessage: vi.fn(),
        deleteMessage: vi.fn(),
        copyMessage: vi.fn()
      });

      render(<ChatInterface {...defaultProps} />);

      expect(screen.getByText(/已断开/)).toBeInTheDocument();
    });
  });

  describe('错误处理', () => {
    it('应该显示错误消息', () => {
      vi.mocked(require('@/hooks/useChat').useChat).mockReturnValue({
        state: {
          currentSession: null,
          sessions: [],
          isConnected: true,
          connectionStatus: 'connected',
          isTyping: false,
          typingAgent: undefined,
          currentAgent: 'pe_engineer',
          currentMode: 'create',
          messageLimit: 100,
          isLoading: false,
          error: '发生了一个错误'
        },
        sendMessage: vi.fn(),
        switchAgent: vi.fn(),
        switchMode: vi.fn(),
        createSession: vi.fn(),
        switchSession: vi.fn(),
        deleteSession: vi.fn(),
        clearMessages: vi.fn(),
        retryMessage: vi.fn(),
        deleteMessage: vi.fn(),
        copyMessage: vi.fn()
      });

      render(<ChatInterface {...defaultProps} />);

      expect(screen.getByText('错误: 发生了一个错误')).toBeInTheDocument();
    });
  });

  describe('打字指示器', () => {
    it('应该显示打字指示器', () => {
      vi.mocked(require('@/hooks/useChat').useChat).mockReturnValue({
        state: {
          currentSession: null,
          sessions: [],
          isConnected: true,
          connectionStatus: 'connected',
          isTyping: true,
          typingAgent: 'pe_engineer',
          currentAgent: 'pe_engineer',
          currentMode: 'create',
          messageLimit: 100,
          isLoading: false,
          error: undefined
        },
        sendMessage: vi.fn(),
        switchAgent: vi.fn(),
        switchMode: vi.fn(),
        createSession: vi.fn(),
        switchSession: vi.fn(),
        deleteSession: vi.fn(),
        clearMessages: vi.fn(),
        retryMessage: vi.fn(),
        deleteMessage: vi.fn(),
        copyMessage: vi.fn()
      });

      render(<ChatInterface {...defaultProps} />);

      expect(screen.getByText('PE Engineer 正在回复...')).toBeInTheDocument();
    });
  });

  describe('工具栏功能', () => {
    it('应该显示关闭按钮', () => {
      render(<ChatInterface {...defaultProps} onClose={mockOnClose} />);

      const closeButton = screen.getByTitle('关闭');
      expect(closeButton).toBeInTheDocument();
    });

    it('应该调用关闭回调', async () => {
      const user = userEvent.setup();
      render(<ChatInterface {...defaultProps} onClose={mockOnClose} />);

      const closeButton = screen.getByTitle('关闭');
      await user.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('应该显示设置按钮', () => {
      render(<ChatInterface {...defaultProps} />);

      const settingsButton = screen.getByTitle('设置');
      expect(settingsButton).toBeInTheDocument();
    });

    it('应该显示全屏按钮当启用时', () => {
      render(<ChatInterface {...defaultProps} enableFullscreen={true} />);

      const fullscreenButton = screen.getByTitle('全屏显示');
      expect(fullscreenButton).toBeInTheDocument();
    });

    it('应该隐藏全屏按钮当禁用时', () => {
      render(<ChatInterface {...defaultProps} enableFullscreen={false} />);

      expect(screen.queryByTitle('全屏显示')).not.toBeInTheDocument();
    });
  });

  describe('空状态', () => {
    it('应该显示欢迎消息当没有消息时', () => {
      render(<ChatInterface {...defaultProps} />);

      expect(screen.getByText('开始对话')).toBeInTheDocument();
      expect(screen.getByText('选择一个 Agent 和模式，然后发送你的第一条消息吧！')).toBeInTheDocument();
    });
  });

  describe('布局模式', () => {
    it('应该应用嵌入式布局类名', () => {
      const { container } = render(
        <ChatInterface {...defaultProps} layout="embedded" />
      );

      const chatContainer = container.firstChild;
      expect(chatContainer).toHaveClass('h-[600px]');
    });

    it('应该应用全屏布局类名', () => {
      const { container } = render(
        <ChatInterface {...defaultProps} layout="fullscreen" />
      );

      const chatContainer = container.firstChild;
      expect(chatContainer).toHaveClass('h-full');
    });
  });

  describe('响应式设计', () => {
    it('应该在移动端隐藏某些功能', () => {
      // 这里需要mock window.innerWidth或使用其他方式模拟移动端
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });

      render(<ChatInterface {...defaultProps} />);

      // 在移动端可能会有不同的布局
      // 具体测试需要根据实际实现调整
    });
  });
});