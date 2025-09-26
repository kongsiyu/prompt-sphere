/**
 * useChat Hook
 * 聊天状态管理，包括消息历史、Agent 切换、对话模式管理等
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import {
  ChatMessage,
  ChatSession,
  ChatState,
  AgentType,
  ChatMode,
  UserMessage,
  AgentMessage,
  SystemMessage,
  ErrorMessage,
  UseChatReturn,
  WebSocketMessage
} from '@/types/chat';

interface UseChatOptions {
  initialAgent?: AgentType;
  initialMode?: ChatMode;
  sessionId?: string;
  maxMessages?: number;
  enableWebSocket?: boolean;
  autoSave?: boolean;
}

/**
 * 生成消息 ID
 */
const generateMessageId = (): string => {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * 生成会话 ID
 */
const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * 创建默认会话
 */
const createDefaultSession = (agent: AgentType, mode: ChatMode): ChatSession => ({
  id: generateSessionId(),
  title: '新对话',
  mode,
  agent,
  messages: [],
  createdAt: Date.now(),
  updatedAt: Date.now(),
  metadata: {
    totalMessages: 0,
    lastActivity: Date.now()
  }
});

/**
 * 本地存储键
 */
const STORAGE_KEYS = {
  SESSIONS: 'chat_sessions',
  CURRENT_SESSION: 'current_session_id',
  SETTINGS: 'chat_settings'
};

/**
 * useChat Hook
 */
export const useChat = (options: UseChatOptions = {}): UseChatReturn => {
  const {
    initialAgent = 'pe_engineer',
    initialMode = 'create',
    sessionId,
    maxMessages = 100,
    enableWebSocket = true,
    autoSave = true
  } = options;

  // 状态管理
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>(sessionId || '');
  const [currentAgent, setCurrentAgent] = useState<AgentType>(initialAgent);
  const [currentMode, setCurrentMode] = useState<ChatMode>(initialMode);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [isTyping, setIsTyping] = useState(false);
  const [typingAgent, setTypingAgent] = useState<AgentType>();

  const pendingMessagesRef = useRef<Map<string, UserMessage>>(new Map());

  // WebSocket 连接
  const {
    isConnected,
    connectionStatus,
    sendMessage: sendWebSocketMessage,
    onMessage: onWebSocketMessage,
    error: wsError
  } = useWebSocket({
    enabled: enableWebSocket
  });

  // 获取当前会话
  const currentSession = sessions.find(s => s.id === currentSessionId) || null;

  // 创建新会话
  const createSession = useCallback((title?: string): ChatSession => {
    const session = createDefaultSession(currentAgent, currentMode);
    if (title) {
      session.title = title;
    }

    setSessions(prev => [session, ...prev]);
    setCurrentSessionId(session.id);
    setError(undefined);

    return session;
  }, [currentAgent, currentMode]);

  // 切换会话
  const switchSession = useCallback((sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      setCurrentSessionId(sessionId);
      setCurrentAgent(session.agent);
      setCurrentMode(session.mode);
      setError(undefined);
    }
  }, [sessions]);

  // 删除会话
  const deleteSession = useCallback((sessionId: string) => {
    setSessions(prev => prev.filter(s => s.id !== sessionId));

    if (currentSessionId === sessionId) {
      const remaining = sessions.filter(s => s.id !== sessionId);
      if (remaining.length > 0) {
        switchSession(remaining[0].id);
      } else {
        // 创建新会话
        createSession();
      }
    }
  }, [currentSessionId, sessions, switchSession, createSession]);

  // 切换 Agent
  const switchAgent = useCallback((agent: AgentType) => {
    setCurrentAgent(agent);

    // 更新当前会话的 agent
    if (currentSession) {
      setSessions(prev =>
        prev.map(s =>
          s.id === currentSessionId
            ? { ...s, agent, updatedAt: Date.now() }
            : s
        )
      );
    }
  }, [currentSession, currentSessionId]);

  // 切换模式
  const switchMode = useCallback((mode: ChatMode) => {
    setCurrentMode(mode);

    // 更新当前会话的模式
    if (currentSession) {
      setSessions(prev =>
        prev.map(s =>
          s.id === currentSessionId
            ? { ...s, mode, updatedAt: Date.now() }
            : s
        )
      );
    }
  }, [currentSession, currentSessionId]);

  // 添加消息到会话
  const addMessageToSession = useCallback((sessionId: string, message: ChatMessage) => {
    setSessions(prev =>
      prev.map(session => {
        if (session.id !== sessionId) return session;

        const newMessages = [...session.messages, message];

        // 限制消息数量
        if (newMessages.length > maxMessages) {
          newMessages.splice(0, newMessages.length - maxMessages);
        }

        return {
          ...session,
          messages: newMessages,
          updatedAt: Date.now(),
          metadata: {
            ...session.metadata,
            totalMessages: newMessages.length,
            lastActivity: Date.now()
          }
        };
      })
    );
  }, [maxMessages]);

  // 更新消息状态
  const updateMessageStatus = useCallback((messageId: string, status: ChatMessage['status']) => {
    setSessions(prev =>
      prev.map(session => ({
        ...session,
        messages: session.messages.map(msg =>
          msg.id === messageId ? { ...msg, status } : msg
        )
      }))
    );
  }, []);

  // 发送消息
  const sendMessage = useCallback(async (content: string, options?: { mode?: ChatMode; agent?: AgentType }) => {
    if (!content.trim()) return;

    const messageMode = options?.mode || currentMode;
    const messageAgent = options?.agent || currentAgent;

    // 确保有当前会话
    let targetSessionId = currentSessionId;
    if (!currentSession) {
      const newSession = createSession();
      targetSessionId = newSession.id;
    }

    // 创建用户消息
    const userMessage: UserMessage = {
      id: generateMessageId(),
      content: content.trim(),
      timestamp: Date.now(),
      type: 'user',
      status: 'pending',
      mode: messageMode
    };

    // 添加到会话
    addMessageToSession(targetSessionId, userMessage);

    // 更新会话标题（如果是第一条消息）
    if (currentSession && currentSession.messages.length === 0) {
      const title = content.length > 30 ? content.slice(0, 30) + '...' : content;
      setSessions(prev =>
        prev.map(s =>
          s.id === targetSessionId
            ? { ...s, title, updatedAt: Date.now() }
            : s
        )
      );
    }

    try {
      setIsLoading(true);
      setError(undefined);

      // 更新消息状态为发送中
      updateMessageStatus(userMessage.id, 'sending');

      // 通过 WebSocket 发送消息
      if (enableWebSocket && isConnected) {
        const wsMessage: WebSocketMessage = {
          type: 'user_message',
          data: {
            message: content,
            agent: messageAgent,
            mode: messageMode,
            timestamp: Date.now(),
            sessionId: targetSessionId
          }
        };

        sendWebSocketMessage(wsMessage);

        // 设置打字状态
        setIsTyping(true);
        setTypingAgent(messageAgent);

        // 存储待处理消息
        pendingMessagesRef.current.set(userMessage.id, userMessage);

      } else {
        // 模拟 API 调用
        await new Promise(resolve => setTimeout(resolve, 1000));

        // 模拟 Agent 响应
        const agentMessage: AgentMessage = {
          id: generateMessageId(),
          content: `这是 ${messageAgent === 'pe_engineer' ? 'PE Engineer' : 'PEQA'} 对 "${content}" 的模拟回复。在 ${messageMode} 模式下，我可以帮助您处理提示词相关的任务。`,
          timestamp: Date.now(),
          type: 'agent',
          status: 'delivered',
          agent: messageAgent,
          mode: messageMode,
          metadata: {
            processingTime: 1500,
            confidence: 0.9,
            version: '1.0.0'
          }
        };

        addMessageToSession(targetSessionId, agentMessage);
      }

      // 更新消息状态为已发送
      updateMessageStatus(userMessage.id, 'sent');

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '发送消息失败';
      setError(errorMessage);

      // 更新消息状态为失败
      updateMessageStatus(userMessage.id, 'failed');

      // 添加错误消息
      const errorMsg: ErrorMessage = {
        id: generateMessageId(),
        content: `发送失败：${errorMessage}`,
        timestamp: Date.now(),
        type: 'error',
        status: 'delivered',
        code: 'SEND_FAILED'
      };

      addMessageToSession(targetSessionId, errorMsg);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
      setTypingAgent(undefined);
    }
  }, [currentMode, currentAgent, currentSessionId, currentSession, createSession, addMessageToSession, updateMessageStatus, enableWebSocket, isConnected, sendWebSocketMessage]);

  // 重试消息
  const retryMessage = useCallback(async (messageId: string) => {
    const session = sessions.find(s => s.messages.some(m => m.id === messageId));
    if (!session) return;

    const message = session.messages.find(m => m.id === messageId);
    if (!message || message.type !== 'user') return;

    await sendMessage(message.content, {
      mode: 'mode' in message ? message.mode : currentMode,
      agent: currentAgent
    });
  }, [sessions, sendMessage, currentMode, currentAgent]);

  // 删除消息
  const deleteMessage = useCallback((messageId: string) => {
    setSessions(prev =>
      prev.map(session => ({
        ...session,
        messages: session.messages.filter(msg => msg.id !== messageId)
      }))
    );
  }, []);

  // 复制消息
  const copyMessage = useCallback((messageId: string) => {
    const message = currentSession?.messages.find(m => m.id === messageId);
    if (message) {
      navigator.clipboard.writeText(message.content);
    }
  }, [currentSession]);

  // 清除消息
  const clearMessages = useCallback(() => {
    if (currentSession) {
      setSessions(prev =>
        prev.map(s =>
          s.id === currentSessionId
            ? { ...s, messages: [], updatedAt: Date.now() }
            : s
        )
      );
    }
  }, [currentSession, currentSessionId]);

  // 工具函数
  const isAgentSupported = useCallback((agent: AgentType, mode: ChatMode): boolean => {
    // 这里可以根据实际配置来判断
    const supportMatrix = {
      pe_engineer: ['create', 'optimize'],
      peqa: ['quality_check', 'optimize']
    };

    return supportMatrix[agent]?.includes(mode) ?? false;
  }, []);

  const getMessageById = useCallback((messageId: string): ChatMessage | undefined => {
    return currentSession?.messages.find(m => m.id === messageId);
  }, [currentSession]);

  // 处理 WebSocket 消息
  const handleWebSocketMessage = useCallback((wsMessage: WebSocketMessage) => {
    switch (wsMessage.type) {
      case 'agent_response':
        setIsTyping(false);
        setTypingAgent(undefined);

        if (wsMessage.data.message && wsMessage.data.agent) {
          const agentMessage: AgentMessage = {
            id: generateMessageId(),
            content: wsMessage.data.message,
            timestamp: wsMessage.data.timestamp || Date.now(),
            type: 'agent',
            status: 'delivered',
            agent: wsMessage.data.agent,
            mode: wsMessage.data.mode || currentMode,
            metadata: wsMessage.data.metadata
          };

          addMessageToSession(currentSessionId, agentMessage);
        }
        break;

      case 'typing_start':
        setIsTyping(true);
        setTypingAgent(wsMessage.data.agent);
        break;

      case 'typing_stop':
        setIsTyping(false);
        setTypingAgent(undefined);
        break;

      case 'error':
        setError(wsMessage.data.error);
        setIsTyping(false);
        setTypingAgent(undefined);
        break;

      case 'system':
        if (wsMessage.data.message) {
          const systemMessage: SystemMessage = {
            id: generateMessageId(),
            content: wsMessage.data.message,
            timestamp: wsMessage.data.timestamp || Date.now(),
            type: 'system',
            status: 'delivered',
            level: 'info'
          };

          addMessageToSession(currentSessionId, systemMessage);
        }
        break;
    }
  }, [currentMode, currentSessionId, addMessageToSession]);

  // 监听 WebSocket 消息
  useEffect(() => {
    if (enableWebSocket) {
      const unsubscribe = onWebSocketMessage(handleWebSocketMessage);
      return unsubscribe;
    }
  }, [enableWebSocket, onWebSocketMessage, handleWebSocketMessage]);

  // 初始化：创建默认会话
  useEffect(() => {
    if (sessions.length === 0 && !currentSessionId) {
      createSession();
    }
  }, [sessions.length, currentSessionId, createSession]);

  // 本地存储同步
  useEffect(() => {
    if (autoSave) {
      localStorage.setItem(STORAGE_KEYS.SESSIONS, JSON.stringify(sessions));
      localStorage.setItem(STORAGE_KEYS.CURRENT_SESSION, currentSessionId);
    }
  }, [sessions, currentSessionId, autoSave]);

  // 从本地存储恢复数据
  useEffect(() => {
    if (autoSave) {
      try {
        const savedSessions = localStorage.getItem(STORAGE_KEYS.SESSIONS);
        const savedCurrentSession = localStorage.getItem(STORAGE_KEYS.CURRENT_SESSION);

        if (savedSessions) {
          const parsedSessions = JSON.parse(savedSessions) as ChatSession[];
          setSessions(parsedSessions);

          if (savedCurrentSession && parsedSessions.some(s => s.id === savedCurrentSession)) {
            setCurrentSessionId(savedCurrentSession);
          }
        }
      } catch (error) {
        console.warn('Failed to restore chat sessions from localStorage:', error);
      }
    }
  }, [autoSave]);

  // 构建状态对象
  const state: ChatState = {
    currentSession,
    sessions,
    isConnected,
    connectionStatus,
    isTyping,
    typingAgent,
    currentAgent,
    currentMode,
    messageLimit: maxMessages,
    isLoading,
    error: error || wsError
  };

  return {
    state,
    sendMessage,
    switchAgent,
    switchMode,
    createSession,
    switchSession,
    deleteSession,
    clearMessages,
    retryMessage,
    deleteMessage,
    copyMessage,
    isAgentSupported,
    getMessageById
  };
};