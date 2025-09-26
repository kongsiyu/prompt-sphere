/**
 * Chat 组件导出文件
 */

export { default as ChatInterface, SimpleChatInterface } from './ChatInterface';
export { default as Message } from './Message';
export { default as MessageList } from './MessageList';
export { default as MessageInput } from './MessageInput';
export {
  default as TypingIndicator,
  SimpleTypingIndicator,
  FloatingTypingIndicator,
  MultiAgentTypingIndicator
} from './TypingIndicator';

// 导出类型
export type { ChatMessage, ChatSession, AgentType, ChatMode } from '@/types/chat';