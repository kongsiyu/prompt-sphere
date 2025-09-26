/**
 * MessageList 组件
 * 聊天消息列表展示组件，支持虚拟滚动、自动滚动等功能
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { cn } from '@/utils/cn';
import { Button } from '@/components/ui/Button';
import Message from './Message';
import { ChatMessage } from '@/types/chat';
import { ChevronDown, AlertCircle } from 'lucide-react';

interface MessageListProps {
  messages: ChatMessage[];
  loading?: boolean;
  error?: string;
  className?: string;
  maxHeight?: string | number;

  // 消息操作
  onMessageCopy?: (content: string) => void;
  onMessageRetry?: (messageId: string) => void;
  onMessageDelete?: (messageId: string) => void;

  // 滚动控制
  autoScroll?: boolean;
  showScrollToBottom?: boolean;

  // 消息显示设置
  showAvatar?: boolean;
  showTimestamp?: boolean;
  enableMessageActions?: boolean;

  // 加载更多
  onLoadMore?: () => void;
  hasMore?: boolean;
  loadingMore?: boolean;
}

/**
 * MessageList 组件
 */
export const MessageList: React.FC<MessageListProps> = ({
  messages = [],
  loading = false,
  error,
  className,
  maxHeight = '100%',
  onMessageCopy,
  onMessageRetry,
  onMessageDelete,
  autoScroll = true,
  showScrollToBottom = true,
  showAvatar = true,
  showTimestamp = true,
  enableMessageActions = true,
  onLoadMore,
  hasMore = false,
  loadingMore = false
}) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const lastMessageCountRef = useRef(messages.length);

  // 检查是否在底部
  const checkIsAtBottom = useCallback(() => {
    if (!scrollContainerRef.current) return false;

    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const threshold = 100; // 距离底部100px内认为是在底部
    const atBottom = scrollHeight - scrollTop - clientHeight < threshold;

    setIsAtBottom(atBottom);
    setShowScrollButton(!atBottom && showScrollToBottom);

    return atBottom;
  }, [showScrollToBottom]);

  // 滚动到底部
  const scrollToBottom = useCallback((smooth = false) => {
    if (!scrollContainerRef.current) return;

    const scrollOptions: ScrollToOptions = {
      top: scrollContainerRef.current.scrollHeight,
      behavior: smooth ? 'smooth' : 'instant'
    };

    scrollContainerRef.current.scrollTo(scrollOptions);
  }, []);

  // 监听滚动事件
  const handleScroll = useCallback(() => {
    checkIsAtBottom();

    // 检查是否需要加载更多消息（滚动到顶部附近）
    if (scrollContainerRef.current && onLoadMore && hasMore && !loadingMore) {
      const { scrollTop } = scrollContainerRef.current;
      if (scrollTop < 100) {
        onLoadMore();
      }
    }
  }, [checkIsAtBottom, onLoadMore, hasMore, loadingMore]);

  // 新消息时自动滚动
  useEffect(() => {
    if (!autoScroll) return;

    const newMessageCount = messages.length;
    const hasNewMessages = newMessageCount > lastMessageCountRef.current;

    if (hasNewMessages && isAtBottom) {
      // 使用 requestAnimationFrame 确保在DOM更新后滚动
      requestAnimationFrame(() => {
        scrollToBottom();
      });
    }

    lastMessageCountRef.current = newMessageCount;
  }, [messages.length, isAtBottom, autoScroll, scrollToBottom]);

  // 初始化时滚动到底部
  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, []);

  // 处理消息操作
  const handleMessageCopy = useCallback((content: string) => {
    onMessageCopy?.(content);
    // 可以添加提示消息
  }, [onMessageCopy]);

  const handleMessageRetry = useCallback((messageId: string) => {
    onMessageRetry?.(messageId);
  }, [onMessageRetry]);

  const handleMessageDelete = useCallback((messageId: string) => {
    onMessageDelete?.(messageId);
  }, [onMessageDelete]);

  // 渲染空状态
  if (!loading && messages.length === 0 && !error) {
    return (
      <div className={cn(
        "flex-1 flex items-center justify-center p-8",
        className
      )}>
        <div className="text-center text-gray-500 dark:text-gray-400">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
            <svg
              className="w-8 h-8"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold mb-2">开始对话</h3>
          <p className="text-sm">
            选择一个 Agent 和模式，然后发送你的第一条消息吧！
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn(
      "relative flex-1 flex flex-col",
      className
    )}>
      {/* 错误状态 */}
      {error && (
        <div className="mx-4 mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 dark:bg-red-900/20 dark:border-red-800 dark:text-red-400">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      {/* 消息列表 */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto overscroll-contain"
        style={{ maxHeight }}
        onScroll={handleScroll}
      >
        {/* 加载更多指示器 */}
        {loadingMore && (
          <div className="flex justify-center py-4">
            <div className="text-sm text-gray-500 flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
              加载历史消息...
            </div>
          </div>
        )}

        {/* 消息列表 */}
        <div className="min-h-0">
          {messages.map((message, index) => {
            // 检查是否是第一条消息或与上一条消息来源不同
            const prevMessage = index > 0 ? messages[index - 1] : null;
            const showAvatar =
              !prevMessage ||
              prevMessage.type !== message.type ||
              (message.type === 'agent' && prevMessage.type === 'agent' &&
               'agent' in message && 'agent' in prevMessage &&
               message.agent !== prevMessage.agent);

            return (
              <Message
                key={message.id}
                message={message}
                showAvatar={showAvatar}
                showTimestamp={showTimestamp}
                enableActions={enableMessageActions}
                onCopy={handleMessageCopy}
                onRetry={handleMessageRetry}
                onDelete={handleMessageDelete}
                className="border-b border-gray-50 dark:border-gray-800 last:border-b-0"
              />
            );
          })}
        </div>

        {/* 加载指示器 */}
        {loading && (
          <div className="flex justify-center py-6">
            <div className="flex items-center gap-2 text-gray-500">
              <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
              <span className="text-sm">AI 正在思考中...</span>
            </div>
          </div>
        )}
      </div>

      {/* 滚动到底部按钮 */}
      {showScrollButton && (
        <div className="absolute bottom-4 right-4 z-10">
          <Button
            size="sm"
            variant="primary"
            onClick={() => scrollToBottom(true)}
            className="rounded-full shadow-lg h-10 w-10 p-0 transition-transform hover:scale-105"
            title="滚动到底部"
          >
            <ChevronDown className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* 新消息提示 */}
      {!isAtBottom && messages.length > 0 && (
        <div className="absolute bottom-16 left-1/2 transform -translate-x-1/2 z-10">
          <Button
            size="sm"
            variant="outline"
            onClick={() => scrollToBottom(true)}
            className="rounded-full shadow-lg px-4 py-2 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600"
          >
            <span className="text-xs">有新消息</span>
            <ChevronDown className="h-3 w-3 ml-1" />
          </Button>
        </div>
      )}
    </div>
  );
};

export default MessageList;