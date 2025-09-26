/**
 * useWebSocket Hook
 * WebSocket 连接管理，支持自动重连、连接状态管理、消息发送和接收
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { ConnectionStatus, WebSocketMessage } from '@/types/chat';

interface UseWebSocketOptions {
  url?: string;
  enabled?: boolean;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
  onMessage?: (message: WebSocketMessage) => void;
}

interface UseWebSocketReturn {
  // 连接状态
  isConnected: boolean;
  connectionStatus: ConnectionStatus;
  error?: string;
  reconnectAttempts: number;

  // 操作
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
  sendMessage: (message: WebSocketMessage) => void;

  // 事件监听
  onMessage: (callback: (message: WebSocketMessage) => void) => () => void;
  onConnect: (callback: () => void) => () => void;
  onDisconnect: (callback: () => void) => () => void;
  onError: (callback: (error: Error) => void) => () => void;
}

/**
 * WebSocket Hook - 暂时使用模拟实现
 * 在实际项目中会连接到真实的 WebSocket 服务器
 */
export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    url = 'ws://localhost:3001/chat',
    enabled = true,
    reconnectDelay = 5000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000,
    onConnect,
    onDisconnect,
    onError,
    onMessage
  } = options;

  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [error, setError] = useState<string>();
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // 使用 ref 存储回调函数和状态
  const wsRef = useRef<WebSocket | null>(null);
  const connectCallbacksRef = useRef<(() => void)[]>([]);
  const disconnectCallbacksRef = useRef<(() => void)[]>([]);
  const errorCallbacksRef = useRef<((error: Error) => void)[]>([]);
  const messageCallbacksRef = useRef<((message: WebSocketMessage) => void)[]>([]);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout>();
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  // 模拟消息队列
  const messageQueueRef = useRef<WebSocketMessage[]>([]);

  // 清理函数
  const cleanup = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // 发送心跳
  const sendHeartbeat = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }));
    }
  }, []);

  // 处理消息
  const handleMessage = useCallback((message: WebSocketMessage) => {
    messageCallbacksRef.current.forEach(callback => callback(message));
    onMessage?.(message);
  }, [onMessage]);

  // 连接 WebSocket
  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');
    setError(undefined);

    // 在实际实现中，这里会创建真实的 WebSocket 连接
    // 现在使用模拟实现
    try {
      // 模拟连接延迟
      setTimeout(() => {
        setConnectionStatus('connected');
        setReconnectAttempts(0);

        // 触发连接回调
        connectCallbacksRef.current.forEach(callback => callback());
        onConnect?.();

        // 启动心跳
        heartbeatIntervalRef.current = setInterval(sendHeartbeat, heartbeatInterval);

        // 模拟收到欢迎消息
        setTimeout(() => {
          const welcomeMessage: WebSocketMessage = {
            type: 'system',
            data: {
              message: '已连接到聊天服务器',
              timestamp: Date.now()
            }
          };
          handleMessage(welcomeMessage);
        }, 500);

      }, 1000 + Math.random() * 1000); // 模拟网络延迟

    } catch (err) {
      const error = err instanceof Error ? err : new Error('连接失败');
      setError(error.message);
      setConnectionStatus('error');
      errorCallbacksRef.current.forEach(callback => callback(error));
      onError?.(error);
    }
  }, [heartbeatInterval, sendHeartbeat, handleMessage, onConnect, onError]);

  // 断开连接
  const disconnect = useCallback(() => {
    cleanup();
    setConnectionStatus('disconnected');

    // 触发断开连接回调
    disconnectCallbacksRef.current.forEach(callback => callback());
    onDisconnect?.();
  }, [cleanup, onDisconnect]);

  // 重连
  const reconnect = useCallback(() => {
    if (reconnectAttempts >= maxReconnectAttempts) {
      setError('达到最大重连次数，连接失败');
      setConnectionStatus('error');
      return;
    }

    setReconnectAttempts(prev => prev + 1);

    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, reconnectDelay);
  }, [reconnectAttempts, maxReconnectAttempts, reconnectDelay, connect]);

  // 发送消息
  const sendMessage = useCallback((message: WebSocketMessage) => {
    // 在模拟实现中，我们直接处理消息
    if (connectionStatus !== 'connected') {
      console.warn('WebSocket 未连接，消息已加入队列');
      messageQueueRef.current.push(message);
      return;
    }

    // 模拟发送延迟
    setTimeout(() => {
      // 如果是用户消息，模拟 Agent 回复
      if (message.type === 'user_message') {
        setTimeout(() => {
          const response: WebSocketMessage = {
            type: 'agent_response',
            data: {
              message: `这是对 "${message.data.message}" 的模拟回复。`,
              agent: message.data.agent || 'pe_engineer',
              mode: message.data.mode || 'create',
              timestamp: Date.now(),
              metadata: {
                processingTime: 1500 + Math.random() * 1000,
                confidence: 0.85 + Math.random() * 0.1
              }
            }
          };
          handleMessage(response);
        }, 2000 + Math.random() * 3000); // 模拟处理时间
      }
    }, 100);

  }, [connectionStatus, handleMessage]);

  // 事件监听器管理
  const onMessageCallback = useCallback((callback: (message: WebSocketMessage) => void) => {
    messageCallbacksRef.current.push(callback);
    return () => {
      messageCallbacksRef.current = messageCallbacksRef.current.filter(cb => cb !== callback);
    };
  }, []);

  const onConnectCallback = useCallback((callback: () => void) => {
    connectCallbacksRef.current.push(callback);
    return () => {
      connectCallbacksRef.current = connectCallbacksRef.current.filter(cb => cb !== callback);
    };
  }, []);

  const onDisconnectCallback = useCallback((callback: () => void) => {
    disconnectCallbacksRef.current.push(callback);
    return () => {
      disconnectCallbacksRef.current = disconnectCallbacksRef.current.filter(cb => cb !== callback);
    };
  }, []);

  const onErrorCallback = useCallback((callback: (error: Error) => void) => {
    errorCallbacksRef.current.push(callback);
    return () => {
      errorCallbacksRef.current = errorCallbacksRef.current.filter(cb => cb !== callback);
    };
  }, []);

  // 自动连接
  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      cleanup();
    };
  }, [enabled, connect, cleanup]);

  // 清理
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  // 处理消息队列
  useEffect(() => {
    if (connectionStatus === 'connected' && messageQueueRef.current.length > 0) {
      const queuedMessages = [...messageQueueRef.current];
      messageQueueRef.current = [];

      queuedMessages.forEach(message => {
        sendMessage(message);
      });
    }
  }, [connectionStatus, sendMessage]);

  return {
    isConnected: connectionStatus === 'connected',
    connectionStatus,
    error,
    reconnectAttempts,
    connect,
    disconnect,
    reconnect,
    sendMessage,
    onMessage: onMessageCallback,
    onConnect: onConnectCallback,
    onDisconnect: onDisconnectCallback,
    onError: onErrorCallback
  };
};