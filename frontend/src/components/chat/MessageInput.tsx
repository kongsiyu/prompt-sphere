/**
 * MessageInput 组件
 * 消息输入框组件，支持多行输入、快捷键、文件上传等功能
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { cn } from '@/utils/cn';
import { Button } from '@/components/ui/Button';
import {
  Send,
  Paperclip,
  Smile,
  X,
  FileText,
  Image,
  AlertCircle,
  Mic,
  MicOff
} from 'lucide-react';
import { AgentType, ChatMode } from '@/types/chat';

// 附件类型
interface Attachment {
  id: string;
  name: string;
  type: 'file' | 'image' | 'prompt';
  size: number;
  preview?: string;
  content?: string;
}

interface MessageInputProps {
  onSendMessage: (message: string, options?: { attachments?: Attachment[] }) => void;
  disabled?: boolean;
  loading?: boolean;
  placeholder?: string;
  maxLength?: number;
  className?: string;

  // Agent 和模式信息
  currentAgent: AgentType;
  currentMode: ChatMode;

  // 功能开关
  enableAttachments?: boolean;
  enableEmoji?: boolean;
  enableVoiceInput?: boolean;

  // 输入建议
  suggestions?: string[];
  onSuggestionClick?: (suggestion: string) => void;

  // 其他设置
  autoFocus?: boolean;
  showCharacterCount?: boolean;
}

/**
 * 计算文本区域的合适高度
 */
const calculateTextareaHeight = (element: HTMLTextAreaElement, maxRows = 5): number => {
  const lineHeight = 24; // 大约的行高
  const minRows = 1;
  const padding = 16; // 上下padding总和

  // 重置高度来计算scrollHeight
  element.style.height = 'auto';
  const scrollHeight = element.scrollHeight;

  // 计算行数
  const rows = Math.max(minRows, Math.min(maxRows, Math.floor((scrollHeight - padding) / lineHeight)));

  return rows * lineHeight + padding;
};

/**
 * MessageInput 组件
 */
export const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  disabled = false,
  loading = false,
  placeholder = '输入消息...',
  maxLength = 2000,
  className,
  currentAgent,
  currentMode,
  enableAttachments = true,
  enableEmoji = false,
  enableVoiceInput = false,
  suggestions = [],
  onSuggestionClick,
  autoFocus = false,
  showCharacterCount = true
}) => {
  const [message, setMessage] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 自动调整输入框高度
  const adjustTextareaHeight = useCallback(() => {
    if (textareaRef.current) {
      const height = calculateTextareaHeight(textareaRef.current);
      textareaRef.current.style.height = `${height}px`;
    }
  }, []);

  // 处理输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    if (value.length <= maxLength) {
      setMessage(value);
      adjustTextareaHeight();
    }
  };

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        // Shift+Enter 换行
        return;
      } else if (e.ctrlKey || e.metaKey) {
        // Ctrl+Enter 或 Cmd+Enter 发送
        e.preventDefault();
        handleSendMessage();
      } else {
        // Enter 发送（可配置）
        e.preventDefault();
        handleSendMessage();
      }
    }

    // Esc 键清除输入
    if (e.key === 'Escape') {
      setMessage('');
      setShowSuggestions(false);
      adjustTextareaHeight();
    }
  };

  // 发送消息
  const handleSendMessage = useCallback(() => {
    if (!message.trim() && attachments.length === 0) return;
    if (disabled || loading) return;

    onSendMessage(message.trim(), {
      attachments: attachments.length > 0 ? attachments : undefined
    });

    // 清空输入
    setMessage('');
    setAttachments([]);
    setShowSuggestions(false);

    // 重置文本框高度
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [message, attachments, disabled, loading, onSendMessage]);

  // 处理文件选择
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);

    files.forEach(file => {
      // 检查文件大小 (5MB 限制)
      if (file.size > 5 * 1024 * 1024) {
        alert('文件大小不能超过 5MB');
        return;
      }

      const attachment: Attachment = {
        id: `file-${Date.now()}-${Math.random()}`,
        name: file.name,
        type: file.type.startsWith('image/') ? 'image' : 'file',
        size: file.size
      };

      // 如果是图片，生成预览
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          attachment.preview = e.target?.result as string;
          setAttachments(prev => [...prev, attachment]);
        };
        reader.readAsDataURL(file);
      } else {
        setAttachments(prev => [...prev, attachment]);
      }
    });

    // 清空文件输入
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 删除附件
  const removeAttachment = (id: string) => {
    setAttachments(prev => prev.filter(att => att.id !== id));
  };

  // 处建议点击
  const handleSuggestionClick = (suggestion: string) => {
    setMessage(suggestion);
    setShowSuggestions(false);
    onSuggestionClick?.(suggestion);
    textareaRef.current?.focus();
    // 延迟调整高度，等待状态更新
    setTimeout(adjustTextareaHeight, 0);
  };

  // 语音输入（模拟实现）
  const toggleVoiceInput = () => {
    setIsRecording(!isRecording);
    // 这里应该集成实际的语音识别API
    if (!isRecording) {
      // 开始录音
      console.log('开始语音输入');
    } else {
      // 停止录音
      console.log('停止语音输入');
    }
  };

  // 自动聚焦
  useEffect(() => {
    if (autoFocus && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [autoFocus]);

  // 判断是否可以发送
  const canSend = (message.trim().length > 0 || attachments.length > 0) && !disabled && !loading;

  return (
    <div className={cn('border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800', className)}>
      {/* 建议列表 */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="border-b border-gray-200 dark:border-gray-700 p-3">
          <div className="flex flex-wrap gap-2">
            <span className="text-xs text-gray-500 mr-2">建议：</span>
            {suggestions.slice(0, 5).map((suggestion, index) => (
              <Button
                key={index}
                size="sm"
                variant="outline"
                onClick={() => handleSuggestionClick(suggestion)}
                className="text-xs px-2 py-1 h-auto"
              >
                {suggestion}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* 附件预览 */}
      {attachments.length > 0 && (
        <div className="p-3 border-b border-gray-200 dark:border-gray-700">
          <div className="flex flex-wrap gap-2">
            {attachments.map(attachment => (
              <div
                key={attachment.id}
                className="relative flex items-center gap-2 bg-gray-50 dark:bg-gray-700 rounded-lg p-2 pr-8"
              >
                {attachment.type === 'image' ? (
                  <Image className="h-4 w-4 text-blue-500" />
                ) : (
                  <FileText className="h-4 w-4 text-gray-500" />
                )}
                <span className="text-sm truncate max-w-32">{attachment.name}</span>
                <span className="text-xs text-gray-500">
                  ({Math.round(attachment.size / 1024)}KB)
                </span>
                <button
                  onClick={() => removeAttachment(attachment.id)}
                  className="absolute top-1 right-1 text-gray-400 hover:text-red-500 transition-colors"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 主输入区域 */}
      <div className="p-4">
        {/* Agent 和模式提示 */}
        <div className="flex items-center gap-2 mb-3 text-sm text-gray-500">
          <span>当前: {currentAgent === 'pe_engineer' ? 'PE Engineer' : 'PEQA'}</span>
          <span>•</span>
          <span>
            {currentMode === 'create' && '创建模式'}
            {currentMode === 'optimize' && '优化模式'}
            {currentMode === 'quality_check' && '质量检查模式'}
          </span>
        </div>

        {/* 输入框区域 */}
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => setShowSuggestions(suggestions.length > 0)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            placeholder={placeholder}
            disabled={disabled || loading}
            className={cn(
              'w-full resize-none border-0 bg-transparent text-sm placeholder:text-gray-400 focus:outline-none focus:ring-0',
              'min-h-[48px] max-h-32 py-3 pr-12 pl-4',
              'scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
            style={{ height: 'auto' }}
          />

          {/* 右侧按钮区域 */}
          <div className="absolute right-2 bottom-2 flex items-center gap-1">
            {/* 语音输入按钮 */}
            {enableVoiceInput && (
              <Button
                size="sm"
                variant="ghost"
                onClick={toggleVoiceInput}
                disabled={disabled}
                className={cn(
                  'h-8 w-8 p-0',
                  isRecording && 'text-red-500 animate-pulse'
                )}
                title={isRecording ? '停止录音' : '开始录音'}
              >
                {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </Button>
            )}

            {/* 附件按钮 */}
            {enableAttachments && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
                className="h-8 w-8 p-0"
                title="添加附件"
              >
                <Paperclip className="h-4 w-4" />
              </Button>
            )}

            {/* 表情按钮 */}
            {enableEmoji && (
              <Button
                size="sm"
                variant="ghost"
                disabled={disabled}
                className="h-8 w-8 p-0"
                title="添加表情"
              >
                <Smile className="h-4 w-4" />
              </Button>
            )}

            {/* 发送按钮 */}
            <Button
              size="sm"
              variant={canSend ? "primary" : "ghost"}
              onClick={handleSendMessage}
              disabled={!canSend}
              loading={loading}
              className="h-8 w-8 p-0"
              title="发送消息 (Enter)"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* 底部信息栏 */}
        <div className="flex justify-between items-center mt-2 text-xs text-gray-500">
          <div className="flex items-center gap-4">
            <span>Enter 发送，Shift+Enter 换行</span>
            {message.length > maxLength * 0.8 && (
              <div className="flex items-center gap-1 text-yellow-500">
                <AlertCircle className="h-3 w-3" />
                <span>字符较多</span>
              </div>
            )}
          </div>

          {showCharacterCount && (
            <div className={cn(
              'transition-colors',
              message.length > maxLength * 0.9 && 'text-red-500',
              message.length > maxLength * 0.8 && message.length <= maxLength * 0.9 && 'text-yellow-500'
            )}>
              {message.length} / {maxLength}
            </div>
          )}
        </div>
      </div>

      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,.pdf,.doc,.docx,.txt"
        onChange={handleFileSelect}
        className="hidden"
      />
    </div>
  );
};

export default MessageInput;