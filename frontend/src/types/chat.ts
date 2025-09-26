/**
 * 聊天相关类型定义
 * 支持 PE Engineer 和 PEQA 双 Agent 对话系统
 */

// Agent 类型
export type AgentType = 'pe_engineer' | 'peqa';

// 对话模式
export type ChatMode = 'create' | 'optimize' | 'quality_check';

// 消息类型
export type MessageType = 'user' | 'agent' | 'system' | 'error';

// 消息状态
export type MessageStatus = 'pending' | 'sending' | 'sent' | 'delivered' | 'failed';

// 连接状态
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

// 基础消息接口
export interface BaseMessage {
  id: string;
  content: string;
  timestamp: number;
  type: MessageType;
  status: MessageStatus;
}

// 用户消息
export interface UserMessage extends BaseMessage {
  type: 'user';
  mode?: ChatMode;
  attachments?: MessageAttachment[];
}

// Agent 消息
export interface AgentMessage extends BaseMessage {
  type: 'agent';
  agent: AgentType;
  mode: ChatMode;
  metadata?: AgentMetadata;
  suggestions?: string[];
}

// 系统消息
export interface SystemMessage extends BaseMessage {
  type: 'system';
  level: 'info' | 'warning' | 'error' | 'success';
}

// 错误消息
export interface ErrorMessage extends BaseMessage {
  type: 'error';
  code?: string;
  details?: string;
}

// 消息联合类型
export type ChatMessage = UserMessage | AgentMessage | SystemMessage | ErrorMessage;

// 消息附件
export interface MessageAttachment {
  id: string;
  name: string;
  type: 'file' | 'image' | 'prompt';
  url?: string;
  content?: string;
  size?: number;
}

// Agent 元数据
export interface AgentMetadata {
  processingTime?: number;
  confidence?: number;
  sources?: string[];
  reasoning?: string;
  version?: string;
}

// 聊天会话
export interface ChatSession {
  id: string;
  title: string;
  mode: ChatMode;
  agent: AgentType;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
  metadata?: {
    promptId?: string;
    context?: string;
    totalMessages: number;
    lastActivity: number;
  };
}

// 打字状态
export interface TypingState {
  isTyping: boolean;
  agent?: AgentType;
  startTime?: number;
}

// WebSocket 消息格式
export interface WebSocketMessage {
  type: 'user_message' | 'agent_response' | 'typing_start' | 'typing_stop' | 'error' | 'system';
  data: {
    message?: string;
    messageId?: string;
    agent?: AgentType;
    mode?: ChatMode;
    timestamp?: number;
    error?: string;
    metadata?: AgentMetadata;
    sessionId?: string;
  };
}

// Agent 请求
export interface AgentRequest {
  message: string;
  agent: AgentType;
  mode: ChatMode;
  context?: string;
  sessionId?: string;
  metadata?: {
    promptId?: string;
    currentPrompt?: string;
    history?: ChatMessage[];
  };
}

// Agent 响应
export interface AgentResponse {
  success: boolean;
  message?: string;
  agent: AgentType;
  mode: ChatMode;
  metadata?: AgentMetadata;
  suggestions?: string[];
  error?: {
    code: string;
    message: string;
    details?: string;
  };
}

// 聊天状态
export interface ChatState {
  // 当前会话
  currentSession: ChatSession | null;

  // 历史会话
  sessions: ChatSession[];

  // UI 状态
  isConnected: boolean;
  connectionStatus: ConnectionStatus;
  isTyping: boolean;
  typingAgent?: AgentType;

  // 配置
  currentAgent: AgentType;
  currentMode: ChatMode;

  // 性能状态
  messageLimit: number;
  isLoading: boolean;
  error?: string;
}

// 聊天配置
export interface ChatConfig {
  // Agent 配置
  agents: {
    pe_engineer: {
      name: string;
      description: string;
      avatar?: string;
      capabilities: string[];
    };
    peqa: {
      name: string;
      description: string;
      avatar?: string;
      capabilities: string[];
    };
  };

  // 模式配置
  modes: {
    create: {
      name: string;
      description: string;
      supportedAgents: AgentType[];
    };
    optimize: {
      name: string;
      description: string;
      supportedAgents: AgentType[];
    };
    quality_check: {
      name: string;
      description: string;
      supportedAgents: AgentType[];
    };
  };

  // 功能配置
  features: {
    markdown: boolean;
    codeHighlight: boolean;
    fileUpload: boolean;
    voiceInput: boolean;
    suggestions: boolean;
  };

  // 限制配置
  limits: {
    maxMessageLength: number;
    maxMessages: number;
    maxSessions: number;
    maxAttachmentSize: number;
  };
}

// Hook 返回类型
export interface UseChatReturn {
  // 状态
  state: ChatState;

  // 操作
  sendMessage: (message: string, options?: { mode?: ChatMode; agent?: AgentType }) => Promise<void>;
  switchAgent: (agent: AgentType) => void;
  switchMode: (mode: ChatMode) => void;
  createSession: (title?: string) => ChatSession;
  switchSession: (sessionId: string) => void;
  deleteSession: (sessionId: string) => void;
  clearMessages: () => void;

  // 消息操作
  retryMessage: (messageId: string) => Promise<void>;
  deleteMessage: (messageId: string) => void;
  copyMessage: (messageId: string) => void;

  // 工具函数
  isAgentSupported: (agent: AgentType, mode: ChatMode) => boolean;
  getMessageById: (messageId: string) => ChatMessage | undefined;
}

// WebSocket Hook 返回类型
export interface UseWebSocketReturn {
  // 连接状态
  isConnected: boolean;
  connectionStatus: ConnectionStatus;
  error?: string;

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