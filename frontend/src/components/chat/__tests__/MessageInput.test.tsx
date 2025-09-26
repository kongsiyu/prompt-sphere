/**
 * MessageInput 组件测试
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import MessageInput from '../MessageInput';
import { AgentType, ChatMode } from '@/types/chat';

describe('MessageInput Component', () => {
  const mockOnSendMessage = vi.fn();
  const mockOnSuggestionClick = vi.fn();

  const defaultProps = {
    onSendMessage: mockOnSendMessage,
    currentAgent: 'pe_engineer' as AgentType,
    currentMode: 'create' as ChatMode
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('基础渲染', () => {
    it('应该渲染输入框', () => {
      render(<MessageInput {...defaultProps} />);

      const textarea = screen.getByPlaceholderText('输入消息...');
      expect(textarea).toBeInTheDocument();
    });

    it('应该显示当前Agent和模式', () => {
      render(<MessageInput {...defaultProps} />);

      expect(screen.getByText('当前: PE Engineer')).toBeInTheDocument();
      expect(screen.getByText('创建模式')).toBeInTheDocument();
    });

    it('应该显示发送按钮', () => {
      render(<MessageInput {...defaultProps} />);

      const sendButton = screen.getByTitle('发送消息 (Enter)');
      expect(sendButton).toBeInTheDocument();
    });
  });

  describe('消息输入', () => {
    it('应该允许输入文本', async () => {
      const user = userEvent.setup();
      render(<MessageInput {...defaultProps} />);

      const textarea = screen.getByPlaceholderText('输入消息...');
      await user.type(textarea, '测试消息');

      expect(textarea).toHaveValue('测试消息');
    });

    it('应该限制最大字符数', async () => {
      const user = userEvent.setup();
      render(<MessageInput {...defaultProps} maxLength={10} />);

      const textarea = screen.getByPlaceholderText('输入消息...');
      await user.type(textarea, '这是一条超过十个字符的长消息');

      // 应该被截断到10个字符
      expect(textarea.value.length).toBeLessThanOrEqual(10);
    });

    it('应该显示字符计数', () => {
      render(<MessageInput {...defaultProps} showCharacterCount={true} />);

      expect(screen.getByText('0 / 2000')).toBeInTheDocument();
    });

    it('应该在字符接近限制时显示警告', async () => {
      const user = userEvent.setup();
      render(<MessageInput {...defaultProps} maxLength={100} />);

      const textarea = screen.getByPlaceholderText('输入消息...');
      // 输入超过80%的字符
      const longText = 'a'.repeat(85);
      await user.type(textarea, longText);

      expect(screen.getByText('字符较多')).toBeInTheDocument();
    });
  });

  describe('消息发送', () => {
    it('应该在点击发送按钮时发送消息', async () => {
      const user = userEvent.setup();
      render(<MessageInput {...defaultProps} />);

      const textarea = screen.getByPlaceholderText('输入消息...');
      const sendButton = screen.getByTitle('发送消息 (Enter)');

      await user.type(textarea, '测试消息');
      await user.click(sendButton);

      expect(mockOnSendMessage).toHaveBeenCalledWith('测试消息', {
        attachments: undefined
      });
    });

    it('应该在按Enter键时发送消息', async () => {
      const user = userEvent.setup();
      render(<MessageInput {...defaultProps} />);

      const textarea = screen.getByPlaceholderText('输入消息...');
      await user.type(textarea, '测试消息');
      await user.keyboard('{Enter}');

      expect(mockOnSendMessage).toHaveBeenCalledWith('测试消息', {
        attachments: undefined
      });
    });

    it('应该在Shift+Enter时换行而不发送', async () => {
      const user = userEvent.setup();
      render(<MessageInput {...defaultProps} />);

      const textarea = screen.getByPlaceholderText('输入消息...');
      await user.type(textarea, '第一行');
      await user.keyboard('{Shift>}{Enter}{/Shift}');
      await user.type(textarea, '第二行');

      expect(textarea.value).toContain('\n');
      expect(mockOnSendMessage).not.toHaveBeenCalled();
    });

    it('应该在Ctrl+Enter时发送消息', async () => {
      const user = userEvent.setup();
      render(<MessageInput {...defaultProps} />);

      const textarea = screen.getByPlaceholderText('输入消息...');
      await user.type(textarea, '测试消息');
      await user.keyboard('{Control>}{Enter}{/Control}');

      expect(mockOnSendMessage).toHaveBeenCalledWith('测试消息', {
        attachments: undefined
      });
    });

    it('不应该发送空消息', async () => {
      const user = userEvent.setup();
      render(<MessageInput {...defaultProps} />);

      const sendButton = screen.getByTitle('发送消息 (Enter)');
      await user.click(sendButton);

      expect(mockOnSendMessage).not.toHaveBeenCalled();
    });

    it('应该在发送后清空输入框', async () => {
      const user = userEvent.setup();
      render(<MessageInput {...defaultProps} />);

      const textarea = screen.getByPlaceholderText('输入消息...');
      const sendButton = screen.getByTitle('发送消息 (Enter)');

      await user.type(textarea, '测试消息');
      await user.click(sendButton);

      await waitFor(() => {
        expect(textarea).toHaveValue('');
      });
    });
  });

  describe('自动调整高度', () => {
    it('应该根据内容调整textarea高度', async () => {
      const user = userEvent.setup();
      render(<MessageInput {...defaultProps} />);

      const textarea = screen.getByPlaceholderText('输入消息...');
      const initialHeight = textarea.style.height;

      // 输入多行文本
      await user.type(textarea, '第一行\n第二行\n第三行\n第四行');

      await waitFor(() => {
        expect(textarea.style.height).not.toBe(initialHeight);
      });
    });
  });

  describe('建议功能', () => {
    const suggestions = ['建议1', '建议2', '建议3'];

    it('应该显示建议列表', () => {
      render(<MessageInput {...defaultProps} suggestions={suggestions} />);

      // 聚焦输入框以显示建议
      const textarea = screen.getByPlaceholderText('输入消息...');
      fireEvent.focus(textarea);

      expect(screen.getByText('建议：')).toBeInTheDocument();
      expect(screen.getByText('建议1')).toBeInTheDocument();
      expect(screen.getByText('建议2')).toBeInTheDocument();
      expect(screen.getByText('建议3')).toBeInTheDocument();
    });

    it('应该在点击建议时调用回调', async () => {
      const user = userEvent.setup();
      render(
        <MessageInput
          {...defaultProps}
          suggestions={suggestions}
          onSuggestionClick={mockOnSuggestionClick}
        />
      );

      // 聚焦以显示建议
      const textarea = screen.getByPlaceholderText('输入消息...');
      fireEvent.focus(textarea);

      const suggestionButton = screen.getByText('建议1');
      await user.click(suggestionButton);

      expect(mockOnSuggestionClick).toHaveBeenCalledWith('建议1');
      expect(textarea).toHaveValue('建议1');
    });

    it('应该限制显示的建议数量', () => {
      const manySuggestions = Array.from({ length: 10 }, (_, i) => `建议${i + 1}`);
      render(<MessageInput {...defaultProps} suggestions={manySuggestions} />);

      const textarea = screen.getByPlaceholderText('输入消息...');
      fireEvent.focus(textarea);

      // 应该最多显示5个建议
      expect(screen.getByText('建议1')).toBeInTheDocument();
      expect(screen.getByText('建议5')).toBeInTheDocument();
      expect(screen.queryByText('建议6')).not.toBeInTheDocument();
    });
  });

  describe('禁用状态', () => {
    it('应该在禁用时禁用所有控件', () => {
      render(<MessageInput {...defaultProps} disabled={true} />);

      const textarea = screen.getByPlaceholderText('输入消息...');
      const sendButton = screen.getByTitle('发送消息 (Enter)');

      expect(textarea).toBeDisabled();
      expect(sendButton).toBeDisabled();
    });

    it('应该在加载时禁用发送按钮', () => {
      render(<MessageInput {...defaultProps} loading={true} />);

      const sendButton = screen.getByTitle('发送消息 (Enter)');
      expect(sendButton).toBeDisabled();
    });

    it('应该在加载时显示加载状态', () => {
      render(<MessageInput {...defaultProps} loading={true} />);

      // 查找加载图标
      const loadingIcon = screen.getByRole('button', { name: /发送消息/ });
      expect(loadingIcon).toHaveClass('opacity-50'); // 或者其他加载状态的样式
    });
  });

  describe('键盘快捷键', () => {
    it('应该在Esc键时清空输入', async () => {
      const user = userEvent.setup();
      render(<MessageInput {...defaultProps} />);

      const textarea = screen.getByPlaceholderText('输入消息...');
      await user.type(textarea, '测试消息');
      await user.keyboard('{Escape}');

      expect(textarea).toHaveValue('');
    });
  });

  describe('Agent和模式显示', () => {
    it('应该显示PEQA agent', () => {
      render(
        <MessageInput
          {...defaultProps}
          currentAgent="peqa"
          currentMode="quality_check"
        />
      );

      expect(screen.getByText('当前: PEQA')).toBeInTheDocument();
      expect(screen.getByText('质量检查模式')).toBeInTheDocument();
    });

    it('应该显示优化模式', () => {
      render(
        <MessageInput
          {...defaultProps}
          currentMode="optimize"
        />
      );

      expect(screen.getByText('优化模式')).toBeInTheDocument();
    });
  });

  describe('快捷键提示', () => {
    it('应该显示快捷键提示', () => {
      render(<MessageInput {...defaultProps} />);

      expect(screen.getByText('Enter 发送，Shift+Enter 换行')).toBeInTheDocument();
    });
  });
});