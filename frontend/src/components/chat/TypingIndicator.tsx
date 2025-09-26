/**
 * TypingIndicator 组件
 * AI 打字状态指示器，显示当前正在回复的 Agent 信息和动画效果
 */

import React from 'react';
import { cn } from '@/utils/cn';
import { Bot } from 'lucide-react';
import { AgentType } from '@/types/chat';

interface TypingIndicatorProps {
  isVisible: boolean;
  agent?: AgentType;
  message?: string;
  className?: string;
}

// Agent 配置
const AGENT_CONFIG: Record<AgentType, { name: string; color: string }> = {
  pe_engineer: {
    name: 'PE Engineer',
    color: 'bg-blue-500'
  },
  peqa: {
    name: 'PEQA',
    color: 'bg-green-500'
  }
};

/**
 * 打字动画组件
 */
const TypingDots: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div className={cn('flex space-x-1', className)}>
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
    </div>
  );
};

/**
 * 脉冲动画组件
 */
const PulseIndicator: React.FC<{ color: string }> = ({ color }) => {
  return (
    <div className="relative">
      <div className={cn('w-3 h-3 rounded-full', color)} />
      <div className={cn(
        'absolute inset-0 w-3 h-3 rounded-full animate-ping opacity-75',
        color
      )} />
    </div>
  );
};

/**
 * TypingIndicator 组件
 */
export const TypingIndicator: React.FC<TypingIndicatorProps> = ({
  isVisible,
  agent = 'pe_engineer',
  message = '正在思考中...',
  className
}) => {
  if (!isVisible) return null;

  const agentConfig = AGENT_CONFIG[agent];

  return (
    <div className={cn(
      'flex items-center gap-3 p-4 transition-all duration-300 ease-in-out',
      'border-b border-gray-50 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/50',
      className
    )}>
      {/* Agent 头像 */}
      <div className="flex-shrink-0 relative">
        <div className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center text-white transition-all duration-200',
          agentConfig.color
        )}>
          <Bot className="h-4 w-4" />
        </div>

        {/* 脉冲指示器 */}
        <div className="absolute -top-1 -right-1">
          <PulseIndicator color={agentConfig.color} />
        </div>
      </div>

      {/* 消息内容区域 */}
      <div className="flex-1 min-w-0">
        {/* Agent 名称和状态 */}
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {agentConfig.name}
          </span>
          <div className="text-xs text-gray-500 dark:text-gray-400 animate-pulse">
            {message}
          </div>
        </div>

        {/* 打字动画 */}
        <div className="flex items-center gap-2">
          <div className="bg-white dark:bg-gray-700 rounded-2xl px-4 py-2 shadow-sm border border-gray-200 dark:border-gray-600">
            <TypingDots />
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * 简化版打字指示器 - 用于输入框附近
 */
export const SimpleTypingIndicator: React.FC<{
  isVisible: boolean;
  agent?: AgentType;
  className?: string;
}> = ({ isVisible, agent = 'pe_engineer', className }) => {
  if (!isVisible) return null;

  const agentConfig = AGENT_CONFIG[agent];

  return (
    <div className={cn(
      'flex items-center gap-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-400',
      'border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800',
      className
    )}>
      <PulseIndicator color={agentConfig.color} />
      <span>{agentConfig.name} 正在回复...</span>
      <TypingDots className="ml-2" />
    </div>
  );
};

/**
 * 浮动打字指示器 - 用于消息列表中
 */
export const FloatingTypingIndicator: React.FC<{
  isVisible: boolean;
  agent?: AgentType;
  position?: 'bottom' | 'inline';
  className?: string;
}> = ({
  isVisible,
  agent = 'pe_engineer',
  position = 'bottom',
  className
}) => {
  if (!isVisible) return null;

  const agentConfig = AGENT_CONFIG[agent];

  return (
    <div className={cn(
      'flex items-center gap-3 p-4',
      position === 'bottom' && 'sticky bottom-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-t border-gray-200 dark:border-gray-700',
      position === 'inline' && 'animate-fadeIn',
      className
    )}>
      {/* Agent 头像 */}
      <div className="flex-shrink-0">
        <div className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center text-white',
          agentConfig.color
        )}>
          <Bot className="h-4 w-4" />
        </div>
      </div>

      {/* 打字动画气泡 */}
      <div className="bg-white dark:bg-gray-700 rounded-2xl px-4 py-3 shadow-sm border border-gray-200 dark:border-gray-600 min-w-20">
        <TypingDots />
      </div>
    </div>
  );
};

/**
 * 多 Agent 打字指示器 - 显示多个 Agent 同时在线
 */
export const MultiAgentTypingIndicator: React.FC<{
  typingAgents: Array<{ agent: AgentType; message?: string }>;
  className?: string;
}> = ({ typingAgents, className }) => {
  if (typingAgents.length === 0) return null;

  return (
    <div className={cn(
      'space-y-2 p-4 bg-gray-50/50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700',
      className
    )}>
      {typingAgents.map(({ agent, message = '正在思考中...' }) => {
        const agentConfig = AGENT_CONFIG[agent];

        return (
          <div key={agent} className="flex items-center gap-3 animate-fadeIn">
            <div className="flex-shrink-0 relative">
              <div className={cn(
                'w-6 h-6 rounded-full flex items-center justify-center text-white',
                agentConfig.color
              )}>
                <Bot className="h-3 w-3" />
              </div>
              <div className="absolute -top-0.5 -right-0.5">
                <div className={cn('w-2 h-2 rounded-full', agentConfig.color)} />
                <div className={cn(
                  'absolute inset-0 w-2 h-2 rounded-full animate-ping opacity-75',
                  agentConfig.color
                )} />
              </div>
            </div>

            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <span className="font-medium">{agentConfig.name}</span>
              <span>{message}</span>
              <TypingDots className="ml-1" />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default TypingIndicator;