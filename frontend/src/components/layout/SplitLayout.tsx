/**
 * 分栏布局组件
 * 支持左右分栏、响应式设计、可调整大小
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { cn } from '@/utils/cn';

interface SplitLayoutProps {
  /** 左侧面板内容 */
  leftPanel: React.ReactNode;
  /** 右侧面板内容 */
  rightPanel: React.ReactNode;
  /** 默认分割位置（百分比，0-100） */
  defaultSplitPosition?: number;
  /** 最小左侧面板宽度（百分比） */
  minLeftWidth?: number;
  /** 最大左侧面板宽度（百分比） */
  maxLeftWidth?: number;
  /** 是否允许调整大小 */
  resizable?: boolean;
  /** 分割线样式类名 */
  dividerClassName?: string;
  /** 左侧面板样式类名 */
  leftClassName?: string;
  /** 右侧面板样式类名 */
  rightClassName?: string;
  /** 容器样式类名 */
  className?: string;
  /** 分割位置改变回调 */
  onSplitPositionChange?: (position: number) => void;
  /** 移动端断点（px） */
  mobileBreakpoint?: number;
}

/**
 * SplitLayout 分栏布局组件
 *
 * @example
 * ```tsx
 * <SplitLayout
 *   leftPanel={<MetadataForm />}
 *   rightPanel={<ChatInterface />}
 *   defaultSplitPosition={50}
 *   minLeftWidth={30}
 *   maxLeftWidth={70}
 *   resizable
 * />
 * ```
 */
export const SplitLayout: React.FC<SplitLayoutProps> = ({
  leftPanel,
  rightPanel,
  defaultSplitPosition = 50,
  minLeftWidth = 20,
  maxLeftWidth = 80,
  resizable = true,
  dividerClassName,
  leftClassName,
  rightClassName,
  className,
  onSplitPositionChange,
  mobileBreakpoint = 768,
}) => {
  const [splitPosition, setSplitPosition] = useState(defaultSplitPosition);
  const [isDragging, setIsDragging] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const dividerRef = useRef<HTMLDivElement>(null);

  // 检查是否为移动端
  const checkIsMobile = useCallback(() => {
    const width = window.innerWidth;
    setIsMobile(width < mobileBreakpoint);
  }, [mobileBreakpoint]);

  // 监听窗口大小变化
  useEffect(() => {
    checkIsMobile();

    const handleResize = () => {
      checkIsMobile();
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [checkIsMobile]);

  // 处理拖拽开始
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (!resizable || isMobile) return;

    e.preventDefault();
    setIsDragging(true);

    // 添加全局事件监听
    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;

      const rect = containerRef.current.getBoundingClientRect();
      const newPosition = ((e.clientX - rect.left) / rect.width) * 100;

      // 限制在最小和最大值之间
      const clampedPosition = Math.max(minLeftWidth, Math.min(maxLeftWidth, newPosition));
      setSplitPosition(clampedPosition);
      onSplitPositionChange?.(clampedPosition);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [resizable, isMobile, minLeftWidth, maxLeftWidth, onSplitPositionChange]);

  // 处理触摸事件（移动端）
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (!resizable || !isMobile) return;

    e.preventDefault();
    setIsDragging(true);

    const handleTouchMove = (e: TouchEvent) => {
      if (!containerRef.current) return;

      const touch = e.touches[0];
      const rect = containerRef.current.getBoundingClientRect();
      const newPosition = ((touch.clientX - rect.left) / rect.width) * 100;

      const clampedPosition = Math.max(minLeftWidth, Math.min(maxLeftWidth, newPosition));
      setSplitPosition(clampedPosition);
      onSplitPositionChange?.(clampedPosition);
    };

    const handleTouchEnd = () => {
      setIsDragging(false);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };

    document.addEventListener('touchmove', handleTouchMove);
    document.addEventListener('touchend', handleTouchEnd);
  }, [resizable, isMobile, minLeftWidth, maxLeftWidth, onSplitPositionChange]);

  // 移动端显示模式（垂直堆叠）
  if (isMobile) {
    return (
      <div className={cn('flex flex-col h-full', className)} ref={containerRef}>
        <div className={cn('flex-shrink-0', leftClassName)}>
          {leftPanel}
        </div>
        <div className={cn('flex-1 overflow-hidden', rightClassName)}>
          {rightPanel}
        </div>
      </div>
    );
  }

  // 桌面端分栏布局
  return (
    <div
      className={cn('flex h-full relative', className)}
      ref={containerRef}
    >
      {/* 左侧面板 */}
      <div
        className={cn('overflow-hidden', leftClassName)}
        style={{ width: `${splitPosition}%` }}
      >
        {leftPanel}
      </div>

      {/* 分割线 */}
      {resizable && (
        <div
          ref={dividerRef}
          className={cn(
            'w-1 bg-border hover:bg-border-hover cursor-col-resize flex-shrink-0 relative group',
            'transition-colors duration-200',
            isDragging && 'bg-primary',
            dividerClassName
          )}
          onMouseDown={handleMouseDown}
          onTouchStart={handleTouchStart}
        >
          {/* 拖拽指示器 */}
          <div className="absolute inset-y-0 -left-1 -right-1 flex items-center justify-center group-hover:bg-primary/10 transition-colors duration-200">
            <div className="w-1 h-8 bg-border-hover rounded-full group-hover:bg-primary transition-colors duration-200" />
          </div>
        </div>
      )}

      {/* 右侧面板 */}
      <div
        className={cn('flex-1 overflow-hidden', rightClassName)}
        style={{ width: `${100 - splitPosition}%` }}
      >
        {rightPanel}
      </div>

      {/* 拖拽遮罩（防止iframe等元素干扰） */}
      {isDragging && (
        <div className="absolute inset-0 z-50 cursor-col-resize" />
      )}
    </div>
  );
};

export default SplitLayout;