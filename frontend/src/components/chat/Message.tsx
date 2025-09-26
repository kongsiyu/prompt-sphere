/**
 * Message 组件
 * 单个聊天消息展示组件，支持用户、Agent、系统消息等不同类型
 */

import React, { useState } from 'react';
import { cn } from '@/utils/cn';
import { Button } from '@/components/ui/Button';
import {
  Copy,
  RotateCcw,
  User,
  Bot,
  AlertCircle,
  CheckCircle2,
  Clock,
  Trash2,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { ChatMessage, AgentType } from '@/types/chat';

// Agent 头像配置
const AGENT_AVATARS: Record<AgentType, { name: string; color: string; icon: React.ReactNode }> = {
  pe_engineer: {
    name: 'PE Engineer',
    color: 'bg-blue-500',
    icon: <Bot className="h-4 w-4" />
  },
  peqa: {
    name: 'PEQA',
    color: 'bg-green-500',
    icon: <Bot className="h-4 w-4" />
  }
};

// 消息状态图标
const STATUS_ICONS = {
  pending: <Clock className="h-3 w-3 text-gray-400" />,
  sending: <Clock className="h-3 w-3 text-blue-400 animate-spin" />,
  sent: <CheckCircle2 className="h-3 w-3 text-green-400" />,
  delivered: <CheckCircle2 className="h-3 w-3 text-green-500" />,
  failed: <AlertCircle className="h-3 w-3 text-red-500" />
};

interface MessageProps {
  message: ChatMessage;
  isLoading?: boolean;
  showAvatar?: boolean;
  showTimestamp?: boolean;
  enableActions?: boolean;
  onCopy?: (content: string) => void;
  onRetry?: (messageId: string) => void;
  onDelete?: (messageId: string) => void;
  className?: string;
}

/**
 * 格式化时间戳
 */
const formatTimestamp = (timestamp: number): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  // 小于1分钟
  if (diff < 60000) {
    return '刚刚';
  }

  // 小于1小时
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`;
  }

  // 小于1天
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`;
  }

  // 今年
  if (date.getFullYear() === now.getFullYear()) {
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  // 其他年份
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

/**
 * 渲染消息内容 - 支持 Markdown 基本语法
 */
const MessageContent: React.FC<{ content: string; type: ChatMessage['type'] }> = ({
  content,
  type
}) => {
  // 简单的 Markdown 渲染 - 可以后续集成更复杂的 Markdown 解析器
  const renderContent = (text: string) => {
    // 代码块处理
    const codeBlockRegex = /```(\w+)?\n?([\s\S]*?)```/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(text)) !== null) {
      // 添加代码块前的文本
      if (match.index > lastIndex) {
        parts.push(
          <span key={`text-${lastIndex}`}>
            {text.slice(lastIndex, match.index)}
          </span>
        );
      }

      // 添加代码块
      const language = match[1] || 'text';
      const code = match[2].trim();
      parts.push(
        <div key={`code-${match.index}`} className="my-2">
          <div className="bg-gray-100 dark:bg-gray-800 rounded-md overflow-hidden">
            <div className="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-xs text-gray-600 dark:text-gray-300 flex justify-between items-center">
              <span>{language}</span>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => navigator.clipboard.writeText(code)}
                className="h-6 px-2 text-xs"
              >
                <Copy className="h-3 w-3" />
              </Button>
            </div>
            <pre className="p-3 text-sm overflow-x-auto">
              <code className="text-gray-800 dark:text-gray-200">{code}</code>
            </pre>
          </div>
        </div>
      );

      lastIndex = codeBlockRegex.lastIndex;
    }

    // 添加剩余文本
    if (lastIndex < text.length) {
      parts.push(
        <span key={`text-${lastIndex}`}>
          {text.slice(lastIndex)}
        </span>
      );
    }

    return parts.length > 0 ? parts : text;
  };

  return (
    <div className={cn(
      "prose prose-sm max-w-none",
      type === 'error' && "text-red-600 dark:text-red-400",
      type === 'system' && "text-gray-600 dark:text-gray-400"
    )}>
      {typeof content === 'string' ? renderContent(content) : content}
    </div>
  );
};

/**
 * Message 组件
 */
export const Message: React.FC<MessageProps> = ({
  message,
  isLoading = false,
  showAvatar = true,
  showTimestamp = true,
  enableActions = true,
  onCopy,
  onRetry,
  onDelete,
  className
}) => {
  const [showMetadata, setShowMetadata] = useState(false);
  const [showActions, setShowActions] = useState(false);

  // 确定消息布局
  const isUserMessage = message.type === 'user';
  const isSystemMessage = message.type === 'system' || message.type === 'error';
  const isAgentMessage = message.type === 'agent';

  // 处理操作
  const handleCopy = () => {
    onCopy?.(message.content);
    navigator.clipboard.writeText(message.content);
  };

  const handleRetry = () => {
    onRetry?.(message.id);
  };

  const handleDelete = () => {
    onDelete?.(message.id);
  };

  // 系统消息样式
  if (isSystemMessage) {
    return (
      <div className={cn("flex justify-center my-4", className)}>
        <div className={cn(
          "px-3 py-2 rounded-full text-sm max-w-md text-center",
          message.type === 'error'
            ? "bg-red-50 text-red-600 border border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800"
            : "bg-gray-50 text-gray-600 border border-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700"
        )}>
          <MessageContent content={message.content} type={message.type} />
          {showTimestamp && (
            <div className="text-xs mt-1 opacity-70">
              {formatTimestamp(message.timestamp)}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "group flex gap-3 p-4 transition-colors duration-200",
        isUserMessage ? "justify-end" : "justify-start",
        showActions && "bg-gray-50 dark:bg-gray-800",
        className
      )}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      {/* 头像区域 - 仅非用户消息显示 */}
      {!isUserMessage && showAvatar && (
        <div className="flex-shrink-0">
          {isAgentMessage && message.agent ? (
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center text-white",
              AGENT_AVATARS[message.agent].color
            )}>
              {AGENT_AVATARS[message.agent].icon}
            </div>
          ) : (
            <div className="w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
              <Bot className="h-4 w-4 text-gray-600 dark:text-gray-300" />
            </div>
          )}
        </div>
      )}

      {/* 消息内容区域 */}
      <div className={cn(
        "flex-1 max-w-2xl",
        isUserMessage ? "flex flex-col items-end" : "flex flex-col items-start"
      )}>
        {/* 消息头部 - Agent名称和时间 */}
        {(!isUserMessage || showTimestamp) && (
          <div className={cn(
            "flex items-center gap-2 mb-2 text-sm text-gray-500",
            isUserMessage && "flex-row-reverse"
          )}>
            {isAgentMessage && message.agent && (
              <span className="font-medium">
                {AGENT_AVATARS[message.agent].name}
              </span>
            )}
            {isUserMessage && <span className="font-medium">你</span>}
            {showTimestamp && (
              <span className="text-xs">
                {formatTimestamp(message.timestamp)}
              </span>
            )}
            {message.status && STATUS_ICONS[message.status]}
          </div>
        )}

        {/* 消息气泡 */}
        <div
          className={cn(
            "relative rounded-2xl px-4 py-3 shadow-sm border transition-all duration-200",
            isUserMessage
              ? "bg-blue-500 text-white border-blue-500"
              : "bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-200 dark:border-gray-600",
            isLoading && "animate-pulse opacity-70"
          )}
        >
          <MessageContent content={message.content} type={message.type} />

          {/* Agent 消息的建议 */}
          {isAgentMessage && message.suggestions && message.suggestions.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
              <p className="text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                建议操作：
              </p>
              <div className="flex flex-wrap gap-2">
                {message.suggestions.map((suggestion, index) => (
                  <Button
                    key={index}
                    size="sm"
                    variant="outline"
                    className="text-xs"
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Agent 元数据 */}
          {isAgentMessage && message.metadata && (
            <div className="mt-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setShowMetadata(!showMetadata)}
                className="text-xs text-gray-500 p-1 h-auto"
              >
                {showMetadata ? (
                  <ChevronUp className="h-3 w-3 mr-1" />
                ) : (
                  <ChevronDown className="h-3 w-3 mr-1" />
                )}
                详情
              </Button>

              {showMetadata && (
                <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-800 rounded text-xs">
                  {message.metadata.processingTime && (
                    <div>处理时间: {message.metadata.processingTime}ms</div>
                  )}
                  {message.metadata.confidence && (
                    <div>置信度: {(message.metadata.confidence * 100).toFixed(1)}%</div>
                  )}
                  {message.metadata.version && (
                    <div>版本: {message.metadata.version}</div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        {enableActions && (showActions || message.status === 'failed') && (
          <div className={cn(
            "flex items-center gap-1 mt-2 transition-opacity duration-200",
            isUserMessage && "flex-row-reverse"
          )}>
            <Button
              size="sm"
              variant="ghost"
              onClick={handleCopy}
              className="h-7 px-2 text-xs"
              title="复制消息"
            >
              <Copy className="h-3 w-3" />
            </Button>

            {message.status === 'failed' && onRetry && (
              <Button
                size="sm"
                variant="ghost"
                onClick={handleRetry}
                className="h-7 px-2 text-xs"
                title="重试"
              >
                <RotateCcw className="h-3 w-3" />
              </Button>
            )}

            {onDelete && (
              <Button
                size="sm"
                variant="ghost"
                onClick={handleDelete}
                className="h-7 px-2 text-xs text-red-500 hover:text-red-600"
                title="删除消息"
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            )}
          </div>
        )}
      </div>

      {/* 用户消息头像 */}
      {isUserMessage && showAvatar && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white">
            <User className="h-4 w-4" />
          </div>
        </div>
      )}
    </div>
  );
};

export default Message;