/**
 * ChatInterface 组件
 * 完整的聊天界面容器，整合所有聊天相关组件
 */

import React, { useState, useCallback, useEffect } from 'react';
import { cn } from '@/utils/cn';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import TypingIndicator, { SimpleTypingIndicator } from './TypingIndicator';
import { useChat } from '@/hooks/useChat';
import { AgentType, ChatMode } from '@/types/chat';
import {
  Settings,
  Users,
  MessageSquare,
  Zap,
  CheckCircle,
  RefreshCw,
  Maximize2,
  Minimize2,
  X,
  Bot
} from 'lucide-react';

interface ChatInterfaceProps {
  className?: string;
  defaultAgent?: AgentType;
  defaultMode?: ChatMode;

  // 布局模式
  layout?: 'sidebar' | 'fullscreen' | 'embedded';

  // 功能控制
  showAgentSelector?: boolean;
  showModeSelector?: boolean;
  showSessionList?: boolean;
  enableFullscreen?: boolean;

  // 集成相关
  promptContext?: string;
  onPromptUpdate?: (prompt: string) => void;

  // 事件回调
  onAgentChange?: (agent: AgentType) => void;
  onModeChange?: (mode: ChatMode) => void;
  onClose?: () => void;
}

// Agent 配置
const AGENT_CONFIG = {
  pe_engineer: {
    name: 'PE Engineer',
    icon: <Bot className="h-4 w-4" />,
    color: 'text-blue-500',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    borderColor: 'border-blue-200 dark:border-blue-700',
    description: '专业提示词工程师'
  },
  peqa: {
    name: 'PEQA',
    icon: <CheckCircle className="h-4 w-4" />,
    color: 'text-green-500',
    bgColor: 'bg-green-50 dark:bg-green-900/20',
    borderColor: 'border-green-200 dark:border-green-700',
    description: '质量保证专家'
  }
};

// 模式配置
const MODE_CONFIG = {
  create: {
    name: '创建模式',
    icon: <Zap className="h-4 w-4" />,
    color: 'text-purple-500',
    description: '创建新的提示词'
  },
  optimize: {
    name: '优化模式',
    icon: <RefreshCw className="h-4 w-4" />,
    color: 'text-orange-500',
    description: '优化现有提示词'
  },
  quality_check: {
    name: '质量检查',
    icon: <CheckCircle className="h-4 w-4" />,
    color: 'text-green-500',
    description: '检查提示词质量'
  }
};

/**
 * ChatInterface 组件
 */
export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  className,
  defaultAgent = 'pe_engineer',
  defaultMode = 'create',
  layout = 'embedded',
  showAgentSelector = true,
  showModeSelector = true,
  showSessionList = false,
  enableFullscreen = true,
  promptContext,
  onPromptUpdate,
  onAgentChange,
  onModeChange,
  onClose
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // 使用聊天 Hook
  const {
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
    copyMessage
  } = useChat({
    initialAgent: defaultAgent,
    initialMode: defaultMode,
    enableWebSocket: true,
    autoSave: true
  });

  // 处理 Agent 切换
  const handleAgentChange = useCallback((agent: AgentType) => {
    switchAgent(agent);
    onAgentChange?.(agent);
  }, [switchAgent, onAgentChange]);

  // 处理模式切换
  const handleModeChange = useCallback((mode: ChatMode) => {
    switchMode(mode);
    onModeChange?.(mode);
  }, [switchMode, onModeChange]);

  // 处理消息发送
  const handleSendMessage = useCallback(async (content: string, options?: any) => {
    // 如果有提示词上下文，将其包含在消息中
    let messageContent = content;
    if (promptContext && state.currentMode === 'optimize') {
      messageContent = `当前提示词：\n${promptContext}\n\n用户请求：${content}`;
    }

    await sendMessage(messageContent, options);
  }, [sendMessage, promptContext, state.currentMode]);

  // 处理消息复制
  const handleMessageCopy = useCallback((content: string) => {
    copyMessage(''); // 这里需要传入实际的消息ID
    navigator.clipboard.writeText(content);

    // 如果复制的是优化建议，可以更新提示词
    if (onPromptUpdate && (content.includes('优化') || content.includes('建议'))) {
      // 这里可以解析Agent的回复，提取优化后的提示词
      // 暂时简单处理
    }
  }, [copyMessage, onPromptUpdate]);

  // 切换全屏模式
  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen);
  }, [isFullscreen]);

  // 渲染 Agent 选择器
  const renderAgentSelector = () => {
    if (!showAgentSelector) return null;

    return (
      <div className="flex gap-2 p-2 border-b border-gray-200 dark:border-gray-700">
        <span className="text-sm text-gray-500 py-2 px-1">Agent:</span>
        {Object.entries(AGENT_CONFIG).map(([key, config]) => {
          const agent = key as AgentType;
          const isSelected = state.currentAgent === agent;

          return (
            <Button
              key={agent}
              size="sm"
              variant={isSelected ? "primary" : "outline"}
              onClick={() => handleAgentChange(agent)}
              className={cn(
                'flex items-center gap-2',
                isSelected && config.color
              )}
            >
              {config.icon}
              {config.name}
            </Button>
          );
        })}
      </div>
    );
  };

  // 渲染模式选择器
  const renderModeSelector = () => {
    if (!showModeSelector) return null;

    return (
      <div className="flex gap-2 p-2 border-b border-gray-200 dark:border-gray-700">
        <span className="text-sm text-gray-500 py-2 px-1">模式:</span>
        {Object.entries(MODE_CONFIG).map(([key, config]) => {
          const mode = key as ChatMode;
          const isSelected = state.currentMode === mode;

          return (
            <Button
              key={mode}
              size="sm"
              variant={isSelected ? "primary" : "outline"}
              onClick={() => handleModeChange(mode)}
              className="flex items-center gap-2"
              title={config.description}
            >
              {config.icon}
              {config.name}
            </Button>
          );
        })}
      </div>
    );
  };

  // 渲染连接状态
  const renderConnectionStatus = () => {
    if (!state.isConnected) {
      return (
        <div className="px-4 py-2 bg-yellow-50 border-b border-yellow-200 text-yellow-700 text-sm dark:bg-yellow-900/20 dark:border-yellow-700 dark:text-yellow-400">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
            连接状态: {state.connectionStatus === 'connecting' ? '连接中...' : '已断开'}
          </div>
        </div>
      );
    }

    return (
      <div className="px-4 py-2 bg-green-50 border-b border-green-200 text-green-700 text-sm dark:bg-green-900/20 dark:border-green-700 dark:text-green-400">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          已连接到聊天服务
        </div>
      </div>
    );
  };

  // 渲染工具栏
  const renderToolbar = () => {
    return (
      <div className="flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <MessageSquare className="h-4 w-4" />
            <span>聊天助手</span>
          </div>

          {state.currentSession && state.currentSession.messages.length > 0 && (
            <div className="text-xs text-gray-500 bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">
              {state.currentSession.messages.length} 条消息
            </div>
          )}
        </div>

        <div className="flex items-center gap-1">
          {/* 清空消息 */}
          {state.currentSession && state.currentSession.messages.length > 0 && (
            <Button
              size="sm"
              variant="ghost"
              onClick={clearMessages}
              title="清空对话"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          )}

          {/* 设置 */}
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowSettings(!showSettings)}
            title="设置"
          >
            <Settings className="h-4 w-4" />
          </Button>

          {/* 全屏切换 */}
          {enableFullscreen && (
            <Button
              size="sm"
              variant="ghost"
              onClick={toggleFullscreen}
              title={isFullscreen ? "退出全屏" : "全屏显示"}
            >
              {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </Button>
          )}

          {/* 关闭按钮 */}
          {onClose && (
            <Button
              size="sm"
              variant="ghost"
              onClick={onClose}
              title="关闭"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    );
  };

  // 确定容器样式
  const containerClasses = cn(
    'flex flex-col bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm',
    {
      'fixed inset-0 z-50 m-0 rounded-none': isFullscreen && layout !== 'fullscreen',
      'h-full': layout === 'fullscreen' || isFullscreen,
      'h-[600px]': layout === 'embedded' && !isFullscreen,
      'w-full': layout === 'sidebar' || layout === 'fullscreen',
      'max-w-4xl': layout === 'embedded' && !isFullscreen
    },
    className
  );

  return (
    <div className={containerClasses}>
      {/* 工具栏 */}
      {renderToolbar()}

      {/* Agent 选择器 */}
      {renderAgentSelector()}

      {/* 模式选择器 */}
      {renderModeSelector()}

      {/* 连接状态 */}
      {renderConnectionStatus()}

      {/* 错误提示 */}
      {state.error && (
        <div className="px-4 py-2 bg-red-50 border-b border-red-200 text-red-700 text-sm dark:bg-red-900/20 dark:border-red-700 dark:text-red-400">
          错误: {state.error}
        </div>
      )}

      {/* 消息列表 */}
      <MessageList
        messages={state.currentSession?.messages || []}
        loading={state.isLoading}
        error={state.error}
        onMessageCopy={handleMessageCopy}
        onMessageRetry={retryMessage}
        onMessageDelete={deleteMessage}
        className="flex-1"
        showAvatar={true}
        showTimestamp={true}
        enableMessageActions={true}
      />

      {/* 打字指示器 */}
      {state.isTyping && state.typingAgent && (
        <SimpleTypingIndicator
          isVisible={state.isTyping}
          agent={state.typingAgent}
        />
      )}

      {/* 消息输入框 */}
      <MessageInput
        onSendMessage={handleSendMessage}
        disabled={!state.isConnected || state.isLoading}
        loading={state.isLoading}
        currentAgent={state.currentAgent}
        currentMode={state.currentMode}
        enableAttachments={false}
        enableEmoji={false}
        enableVoiceInput={false}
        placeholder={`与 ${AGENT_CONFIG[state.currentAgent].name} 对话...`}
        autoFocus={true}
      />
    </div>
  );
};

/**
 * 简化版聊天界面 - 用于嵌入到其他组件中
 */
export const SimpleChatInterface: React.FC<Omit<ChatInterfaceProps, 'layout'>> = (props) => {
  return (
    <ChatInterface
      {...props}
      layout="embedded"
      showAgentSelector={false}
      showModeSelector={false}
      showSessionList={false}
      enableFullscreen={false}
    />
  );
};

export default ChatInterface;