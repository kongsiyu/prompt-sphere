/**
 * Message 组件测试
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import Message from '../Message';
import { ChatMessage, UserMessage, AgentMessage, SystemMessage, ErrorMessage } from '@/types/chat';

// Mock navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn(),
  },
});

describe('Message Component', () => {
  const mockOnCopy = vi.fn();
  const mockOnRetry = vi.fn();
  const mockOnDelete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('User Message', () => {
    const userMessage: UserMessage = {
      id: 'msg-1',
      content: '这是用户消息',
      timestamp: Date.now(),
      type: 'user',
      status: 'sent'
    };

    it('应该正确渲染用户消息', () => {
      render(<Message message={userMessage} />);

      expect(screen.getByText('这是用户消息')).toBeInTheDocument();
      expect(screen.getByText('你')).toBeInTheDocument();
    });

    it('应该显示用户头像', () => {
      render(<Message message={userMessage} showAvatar={true} />);

      const avatar = screen.getByRole('generic', { name: /user/i });
      expect(avatar).toBeInTheDocument();
    });

    it('应该在右侧显示用户消息', () => {
      const { container } = render(<Message message={userMessage} />);

      const messageContainer = container.querySelector('.justify-end');
      expect(messageContainer).toBeInTheDocument();
    });
  });

  describe('Agent Message', () => {
    const agentMessage: AgentMessage = {
      id: 'msg-2',
      content: '这是AI回复',
      timestamp: Date.now(),
      type: 'agent',
      status: 'delivered',
      agent: 'pe_engineer',
      mode: 'create',
      metadata: {
        processingTime: 1500,
        confidence: 0.9
      },
      suggestions: ['建议1', '建议2']
    };

    it('应该正确渲染Agent消息', () => {
      render(<Message message={agentMessage} />);

      expect(screen.getByText('这是AI回复')).toBeInTheDocument();
      expect(screen.getByText('PE Engineer')).toBeInTheDocument();
    });

    it('应该显示建议操作', () => {
      render(<Message message={agentMessage} />);

      expect(screen.getByText('建议操作：')).toBeInTheDocument();
      expect(screen.getByText('建议1')).toBeInTheDocument();
      expect(screen.getByText('建议2')).toBeInTheDocument();
    });

    it('应该显示/隐藏元数据', () => {
      render(<Message message={agentMessage} />);

      const detailsButton = screen.getByText('详情');
      expect(detailsButton).toBeInTheDocument();

      // 点击显示详情
      fireEvent.click(detailsButton);
      expect(screen.getByText(/处理时间: 1500ms/)).toBeInTheDocument();
      expect(screen.getByText(/置信度: 90.0%/)).toBeInTheDocument();

      // 再次点击隐藏详情
      fireEvent.click(detailsButton);
      expect(screen.queryByText(/处理时间: 1500ms/)).not.toBeInTheDocument();
    });

    it('应该在左侧显示Agent消息', () => {
      const { container } = render(<Message message={agentMessage} />);

      const messageContainer = container.querySelector('.justify-start');
      expect(messageContainer).toBeInTheDocument();
    });
  });

  describe('System Message', () => {
    const systemMessage: SystemMessage = {
      id: 'msg-3',
      content: '系统消息',
      timestamp: Date.now(),
      type: 'system',
      status: 'delivered',
      level: 'info'
    };

    it('应该正确渲染系统消息', () => {
      render(<Message message={systemMessage} />);

      expect(screen.getByText('系统消息')).toBeInTheDocument();
    });

    it('应该居中显示系统消息', () => {
      const { container } = render(<Message message={systemMessage} />);

      const messageContainer = container.querySelector('.justify-center');
      expect(messageContainer).toBeInTheDocument();
    });
  });

  describe('Error Message', () => {
    const errorMessage: ErrorMessage = {
      id: 'msg-4',
      content: '错误消息',
      timestamp: Date.now(),
      type: 'error',
      status: 'delivered',
      code: 'ERROR_CODE'
    };

    it('应该正确渲染错误消息', () => {
      render(<Message message={errorMessage} />);

      expect(screen.getByText('错误消息')).toBeInTheDocument();
    });

    it('应该应用错误样式', () => {
      const { container } = render(<Message message={errorMessage} />);

      const errorElement = container.querySelector('.text-red-600');
      expect(errorElement).toBeInTheDocument();
    });
  });

  describe('Message Actions', () => {
    const testMessage: UserMessage = {
      id: 'msg-5',
      content: '测试消息',
      timestamp: Date.now(),
      type: 'user',
      status: 'sent'
    };

    it('应该显示复制按钮并调用复制函数', () => {
      const { container } = render(
        <Message
          message={testMessage}
          onCopy={mockOnCopy}
          enableActions={true}
        />
      );

      // 模拟鼠标悬停显示操作按钮
      const messageContainer = container.querySelector('.group');
      fireEvent.mouseEnter(messageContainer!);

      const copyButton = screen.getByTitle('复制消息');
      expect(copyButton).toBeInTheDocument();

      fireEvent.click(copyButton);
      expect(mockOnCopy).toHaveBeenCalledWith('测试消息');
    });

    it('应该显示重试按钮当消息失败时', () => {
      const failedMessage: UserMessage = {
        ...testMessage,
        status: 'failed'
      };

      const { container } = render(
        <Message
          message={failedMessage}
          onRetry={mockOnRetry}
          enableActions={true}
        />
      );

      const retryButton = screen.getByTitle('重试');
      expect(retryButton).toBeInTheDocument();

      fireEvent.click(retryButton);
      expect(mockOnRetry).toHaveBeenCalledWith('msg-5');
    });

    it('应该显示删除按钮', () => {
      const { container } = render(
        <Message
          message={testMessage}
          onDelete={mockOnDelete}
          enableActions={true}
        />
      );

      // 模拟鼠标悬停
      const messageContainer = container.querySelector('.group');
      fireEvent.mouseEnter(messageContainer!);

      const deleteButton = screen.getByTitle('删除消息');
      expect(deleteButton).toBeInTheDocument();

      fireEvent.click(deleteButton);
      expect(mockOnDelete).toHaveBeenCalledWith('msg-5');
    });
  });

  describe('Message Status', () => {
    it('应该显示消息状态图标', () => {
      const pendingMessage: UserMessage = {
        id: 'msg-6',
        content: '等待中',
        timestamp: Date.now(),
        type: 'user',
        status: 'pending'
      };

      render(<Message message={pendingMessage} />);

      // 查找时钟图标（pending状态）
      const statusIcon = screen.getByRole('generic');
      expect(statusIcon).toBeInTheDocument();
    });

    it('应该显示发送中状态的动画', () => {
      const sendingMessage: UserMessage = {
        id: 'msg-7',
        content: '发送中',
        timestamp: Date.now(),
        type: 'user',
        status: 'sending'
      };

      const { container } = render(<Message message={sendingMessage} />);

      // 查找旋转动画的元素
      const animatedIcon = container.querySelector('.animate-spin');
      expect(animatedIcon).toBeInTheDocument();
    });
  });

  describe('Code Blocks', () => {
    const messageWithCode: AgentMessage = {
      id: 'msg-8',
      content: '这是代码示例：\n```javascript\nconsole.log("Hello World");\n```',
      timestamp: Date.now(),
      type: 'agent',
      status: 'delivered',
      agent: 'pe_engineer',
      mode: 'create'
    };

    it('应该正确渲染代码块', () => {
      render(<Message message={messageWithCode} />);

      expect(screen.getByText('javascript')).toBeInTheDocument();
      expect(screen.getByText('console.log("Hello World");')).toBeInTheDocument();
    });

    it('应该显示代码复制按钮', () => {
      render(<Message message={messageWithCode} />);

      const codeBlocks = screen.getAllByRole('button');
      const copyButtons = codeBlocks.filter(btn =>
        btn.querySelector('svg') !== null
      );
      expect(copyButtons.length).toBeGreaterThan(0);
    });
  });

  describe('Timestamps', () => {
    it('应该显示时间戳', () => {
      const now = Date.now();
      const message: UserMessage = {
        id: 'msg-9',
        content: '测试时间',
        timestamp: now,
        type: 'user',
        status: 'sent'
      };

      render(<Message message={message} showTimestamp={true} />);

      // 应该显示"刚刚"（因为是当前时间）
      expect(screen.getByText('刚刚')).toBeInTheDocument();
    });

    it('应该隐藏时间戳当设置为false时', () => {
      const message: UserMessage = {
        id: 'msg-10',
        content: '测试时间',
        timestamp: Date.now(),
        type: 'user',
        status: 'sent'
      };

      render(<Message message={message} showTimestamp={false} />);

      // 不应该显示时间戳
      expect(screen.queryByText('刚刚')).not.toBeInTheDocument();
    });
  });
});