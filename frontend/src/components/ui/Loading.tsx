/**
 * Loading 组件
 * 提供多种加载状态指示器，包括spinner、dots、pulse、skeleton等
 */

import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';

// 加载组件样式变体定义
const loadingVariants = cva('', {
  variants: {
    // 加载类型
    type: {
      spinner: 'animate-spin',
      dots: 'flex items-center justify-center gap-1',
      pulse: 'animate-pulse',
      skeleton: 'animate-pulse bg-muted rounded',
      bars: 'flex items-end justify-center gap-1',
    },
    // 尺寸变体
    size: {
      xs: 'h-3 w-3',
      sm: 'h-4 w-4',
      md: 'h-6 w-6',
      lg: 'h-8 w-8',
      xl: 'h-12 w-12',
    },
    // 颜色变体
    color: {
      primary: 'text-primary',
      secondary: 'text-secondary',
      muted: 'text-muted-foreground',
      white: 'text-white',
      current: 'text-current',
    },
  },
  defaultVariants: {
    type: 'spinner',
    size: 'md',
    color: 'primary',
  },
});

// 加载组件Props类型
export interface LoadingProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof loadingVariants> {
  /** 加载文本 */
  text?: string;
  /** 是否居中显示 */
  center?: boolean;
  /** 是否全屏覆盖 */
  overlay?: boolean;
  /** 骨架屏宽度 */
  width?: string | number;
  /** 骨架屏高度 */
  height?: string | number;
}

/**
 * Spinner 加载器
 */
const Spinner: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={cn('animate-spin', className)}
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
    />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>
);

/**
 * Dots 加载器
 */
const Dots: React.FC<{ className?: string; size?: string }> = ({ className, size = 'h-2 w-2' }) => (
  <div className={cn('flex items-center justify-center gap-1', className)}>
    {[0, 1, 2].map((i) => (
      <div
        key={i}
        className={cn(
          'rounded-full bg-current animate-pulse',
          size
        )}
        style={{
          animationDelay: `${i * 0.15}s`,
          animationDuration: '0.6s',
        }}
      />
    ))}
  </div>
);

/**
 * Pulse 加载器
 */
const Pulse: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('animate-pulse rounded-full bg-current', className)} />
);

/**
 * Bars 加载器
 */
const Bars: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('flex items-end justify-center gap-1', className)}>
    {[0, 1, 2, 3].map((i) => (
      <div
        key={i}
        className="w-1 bg-current rounded-full animate-pulse"
        style={{
          height: `${12 + (i % 2) * 8}px`,
          animationDelay: `${i * 0.1}s`,
          animationDuration: '0.8s',
        }}
      />
    ))}
  </div>
);

/**
 * Loading 组件
 *
 * @example
 * ```tsx
 * // 基础spinner
 * <Loading />
 *
 * // 带文本的加载
 * <Loading text="加载中..." />
 *
 * // 不同类型的加载器
 * <Loading type="dots" />
 * <Loading type="pulse" />
 * <Loading type="bars" />
 *
 * // 骨架屏
 * <Loading type="skeleton" width={200} height={20} />
 *
 * // 全屏覆盖
 * <Loading overlay text="正在处理..." />
 *
 * // 居中显示
 * <Loading center text="请稍候..." />
 * ```
 */
export const Loading: React.FC<LoadingProps> = ({
  className,
  type,
  size,
  color,
  text,
  center = false,
  overlay = false,
  width,
  height,
  style,
  ...props
}) => {
  // 渲染不同类型的加载器
  const renderLoader = () => {
    const loaderClassName = loadingVariants({ size, color });

    switch (type) {
      case 'spinner':
        return <Spinner className={loaderClassName} />;

      case 'dots':
        const dotSize = {
          xs: 'h-1 w-1',
          sm: 'h-1.5 w-1.5',
          md: 'h-2 w-2',
          lg: 'h-2.5 w-2.5',
          xl: 'h-3 w-3',
        }[size || 'md'];
        return <Dots className={cn(loaderClassName, color)} size={dotSize} />;

      case 'pulse':
        return <Pulse className={loaderClassName} />;

      case 'bars':
        return <Bars className={cn(loaderClassName, color)} />;

      case 'skeleton':
        return (
          <div
            className="animate-pulse bg-muted rounded"
            style={{
              width: width || '100%',
              height: height || '1rem',
              ...style,
            }}
          />
        );

      default:
        return <Spinner className={loaderClassName} />;
    }
  };

  // 基础容器
  const container = (
    <div
      className={cn(
        'flex items-center gap-2',
        {
          'justify-center': center,
          'flex-col': text && (type === 'spinner' || type === 'pulse'),
        },
        className
      )}
      {...props}
    >
      {type !== 'skeleton' && renderLoader()}
      {type === 'skeleton' && renderLoader()}
      {text && type !== 'skeleton' && (
        <span className="text-sm text-muted-foreground">{text}</span>
      )}
    </div>
  );

  // 全屏覆盖
  if (overlay) {
    return (
      <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm">
        <div className="flex items-center justify-center min-h-screen">
          {container}
        </div>
      </div>
    );
  }

  return container;
};

/**
 * 骨架屏组件 - Loading的便捷封装
 */
export const Skeleton: React.FC<{
  className?: string;
  width?: string | number;
  height?: string | number;
  lines?: number;
}> = ({ className, width, height, lines = 1 }) => {
  if (lines > 1) {
    return (
      <div className={cn('space-y-2', className)}>
        {Array.from({ length: lines }).map((_, i) => (
          <Loading
            key={i}
            type="skeleton"
            width={i === lines - 1 ? '60%' : width}
            height={height}
          />
        ))}
      </div>
    );
  }

  return <Loading type="skeleton" width={width} height={height} className={className} />;
};

/**
 * 页面加载组件
 */
export const PageLoading: React.FC<{
  text?: string;
  overlay?: boolean;
}> = ({ text = '页面加载中...', overlay = true }) => (
  <Loading
    type="spinner"
    size="lg"
    text={text}
    center
    overlay={overlay}
  />
);

/**
 * 按钮加载组件
 */
export const ButtonLoading: React.FC<{
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  color?: 'primary' | 'secondary' | 'muted' | 'white' | 'current';
}> = ({ size = 'sm', color = 'current' }) => (
  <Loading type="spinner" size={size} color={color} />
);

export { loadingVariants };