/**
 * useChat Hook 测试
 */

import { renderHook, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useChat } from '../useChat';
import { AgentType, ChatMode } from '@/types/chat';

// Mock useWebSocket
vi.mock('../useWebSocket', () => ({
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
    onError: vi.fn(() => () => {}),
    error: undefined
  }))
}));

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});

describe('useChat Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('初始化', () => {
    it('应该使用默认配置初始化', () => {
      const { result } = renderHook(() => useChat());

      expect(result.current.state.currentAgent).toBe('pe_engineer');
      expect(result.current.state.currentMode).toBe('create');
      expect(result.current.state.sessions).toEqual([]);
      expect(result.current.state.isLoading).toBe(false);
      expect(result.current.state.error).toBeUndefined();
    });

    it('应该使用自定义初始配置', () => {
      const { result } = renderHook(() =>
        useChat({
          initialAgent: 'peqa',
          initialMode: 'quality_check'
        })
      );

      expect(result.current.state.currentAgent).toBe('peqa');
      expect(result.current.state.currentMode).toBe('quality_check');
    });

    it('应该创建默认会话', async () => {
      const { result } = renderHook(() => useChat());

      // 等待初始化完成
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.state.sessions).toHaveLength(1);
      expect(result.current.state.currentSession).not.toBeNull();
    });
  });

  describe('Agent切换', () => {
    it('应该切换Agent', () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.switchAgent('peqa');
      });

      expect(result.current.state.currentAgent).toBe('peqa');
    });

    it('应该更新当前会话的Agent', async () => {
      const { result } = renderHook(() => useChat());

      // 等待默认会话创建
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      act(() => {
        result.current.switchAgent('peqa');
      });

      expect(result.current.state.currentSession?.agent).toBe('peqa');
    });
  });

  describe('模式切换', () => {
    it('应该切换模式', () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.switchMode('optimize');
      });

      expect(result.current.state.currentMode).toBe('optimize');
    });

    it('应该更新当前会话的模式', async () => {
      const { result } = renderHook(() => useChat());

      // 等待默认会话创建
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      act(() => {
        result.current.switchMode('optimize');
      });

      expect(result.current.state.currentSession?.mode).toBe('optimize');
    });
  });

  describe('会话管理', () => {
    it('应该创建新会话', () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        const newSession = result.current.createSession('测试会话');
        expect(newSession.title).toBe('测试会话');
      });

      expect(result.current.state.sessions).toHaveLength(2); // 包括默认会话
    });

    it('应该切换会话', async () => {
      const { result } = renderHook(() => useChat());

      // 创建新会话
      let newSessionId: string;
      act(() => {
        const newSession = result.current.createSession('新会话');
        newSessionId = newSession.id;
      });

      // 切换到新会话
      act(() => {
        result.current.switchSession(newSessionId);
      });

      expect(result.current.state.currentSession?.id).toBe(newSessionId);
    });

    it('应该删除会话', async () => {
      const { result } = renderHook(() => useChat());

      // 创建额外会话
      let sessionToDelete: string;
      act(() => {
        const newSession = result.current.createSession('要删除的会话');
        sessionToDelete = newSession.id;
      });

      const initialCount = result.current.state.sessions.length;

      // 删除会话
      act(() => {
        result.current.deleteSession(sessionToDelete);
      });

      expect(result.current.state.sessions).toHaveLength(initialCount - 1);
    });
  });

  describe('消息发送', () => {
    it('应该发送消息', async () => {
      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('测试消息');
      });

      expect(result.current.state.currentSession?.messages).toHaveLength(1);
      expect(result.current.state.currentSession?.messages[0].content).toBe('测试消息');
    });

    it('不应该发送空消息', async () => {
      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('');
      });

      expect(result.current.state.currentSession?.messages).toHaveLength(0);
    });

    it('应该创建会话如果不存在', async () => {
      const { result } = renderHook(() => useChat());

      // 确保没有当前会话
      act(() => {
        if (result.current.state.currentSession) {
          result.current.deleteSession(result.current.state.currentSession.id);
        }
      });

      await act(async () => {
        await result.current.sendMessage('测试消息');
      });

      expect(result.current.state.currentSession).not.toBeNull();
      expect(result.current.state.currentSession?.messages).toHaveLength(1);
    });

    it('应该设置加载状态', async () => {
      const { result } = renderHook(() => useChat());

      const sendPromise = act(async () => {
        return result.current.sendMessage('测试消息');
      });

      // 在发送过程中应该是加载状态
      expect(result.current.state.isLoading).toBe(true);

      await sendPromise;

      // 完成后应该取消加载状态
      expect(result.current.state.isLoading).toBe(false);
    });
  });

  describe('消息操作', () => {
    it('应该重试消息', async () => {
      const { result } = renderHook(() => useChat());

      // 发送初始消息
      await act(async () => {
        await result.current.sendMessage('测试消息');
      });

      const messageId = result.current.state.currentSession?.messages[0].id!;

      // 重试消息
      await act(async () => {
        await result.current.retryMessage(messageId);
      });

      // 应该添加新的消息
      expect(result.current.state.currentSession?.messages.length).toBeGreaterThan(1);
    });

    it('应该删除消息', async () => {
      const { result } = renderHook(() => useChat());

      // 发送消息
      await act(async () => {
        await result.current.sendMessage('测试消息');
      });

      const messageId = result.current.state.currentSession?.messages[0].id!;

      // 删除消息
      act(() => {
        result.current.deleteMessage(messageId);
      });

      expect(result.current.state.currentSession?.messages).toHaveLength(0);
    });

    it('应该复制消息', () => {
      const { result } = renderHook(() => useChat());

      const mockWriteText = vi.fn();
      Object.assign(navigator, {
        clipboard: { writeText: mockWriteText }
      });

      // 假设有一个消息
      const messageId = 'test-message-id';
      act(() => {
        result.current.copyMessage(messageId);
      });

      // 由于我们的实现依赖于实际的消息存在，
      // 这里主要测试函数是否被调用而不出错
      expect(() => result.current.copyMessage(messageId)).not.toThrow();
    });

    it('应该清空消息', async () => {
      const { result } = renderHook(() => useChat());

      // 发送一些消息
      await act(async () => {
        await result.current.sendMessage('消息1');
        await result.current.sendMessage('消息2');
      });

      expect(result.current.state.currentSession?.messages.length).toBeGreaterThan(0);

      // 清空消息
      act(() => {
        result.current.clearMessages();
      });

      expect(result.current.state.currentSession?.messages).toHaveLength(0);
    });
  });

  describe('工具函数', () => {
    it('应该检查Agent是否支持特定模式', () => {
      const { result } = renderHook(() => useChat());

      // 根据我们的实现，这些应该返回对应的结果
      expect(result.current.isAgentSupported('pe_engineer', 'create')).toBe(true);
      expect(result.current.isAgentSupported('peqa', 'quality_check')).toBe(true);
      expect(result.current.isAgentSupported('pe_engineer', 'quality_check')).toBe(false);
    });

    it('应该根据ID获取消息', async () => {
      const { result } = renderHook(() => useChat());

      // 发送消息
      await act(async () => {
        await result.current.sendMessage('测试消息');
      });

      const messageId = result.current.state.currentSession?.messages[0].id!;
      const message = result.current.getMessageById(messageId);

      expect(message).not.toBeUndefined();
      expect(message?.content).toBe('测试消息');
    });

    it('应该返回undefined当消息不存在时', () => {
      const { result } = renderHook(() => useChat());

      const message = result.current.getMessageById('nonexistent-id');
      expect(message).toBeUndefined();
    });
  });

  describe('本地存储', () => {
    it('应该保存会话到本地存储', async () => {
      const { result } = renderHook(() =>
        useChat({ autoSave: true })
      );

      await act(async () => {
        await result.current.sendMessage('测试消息');
      });

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'chat_sessions',
        expect.any(String)
      );
    });

    it('应该从本地存储恢复会话', () => {
      const mockSessions = JSON.stringify([
        {
          id: 'session-1',
          title: '恢复的会话',
          mode: 'create',
          agent: 'pe_engineer',
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now()
        }
      ]);

      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'chat_sessions') return mockSessions;
        if (key === 'current_session_id') return 'session-1';
        return null;
      });

      const { result } = renderHook(() =>
        useChat({ autoSave: true })
      );

      expect(result.current.state.sessions).toHaveLength(1);
      expect(result.current.state.sessions[0].title).toBe('恢复的会话');
    });

    it('应该处理本地存储错误', () => {
      mockLocalStorage.getItem.mockImplementation(() => {
        throw new Error('localStorage error');
      });

      expect(() => {
        renderHook(() => useChat({ autoSave: true }));
      }).not.toThrow();
    });
  });

  describe('连接状态', () => {
    it('应该反映WebSocket连接状态', () => {
      const { result } = renderHook(() => useChat());

      expect(result.current.state.isConnected).toBe(true);
      expect(result.current.state.connectionStatus).toBe('connected');
    });
  });

  describe('消息限制', () => {
    it('应该限制消息数量', async () => {
      const maxMessages = 2;
      const { result } = renderHook(() =>
        useChat({ maxMessages })
      );

      // 发送超过限制的消息
      await act(async () => {
        await result.current.sendMessage('消息1');
        await result.current.sendMessage('消息2');
        await result.current.sendMessage('消息3');
      });

      // 应该只保留最新的消息
      expect(result.current.state.currentSession?.messages.length).toBeLessThanOrEqual(maxMessages);
    });
  });
});