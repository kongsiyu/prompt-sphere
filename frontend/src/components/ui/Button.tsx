/**
 * Button 组件
 * 支持多种样式变体、尺寸、状态和无障碍访问
 */

import React, { forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';

// 按钮样式变体定义
const buttonVariants = cva(
  // 基础样式
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0',
  {
    variants: {
      // 样式变体
      variant: {
        default: 'bg-primary text-primary-foreground shadow hover:bg-primary/90 active:scale-95',
        primary: 'bg-blue-500 text-white shadow-md hover:bg-blue-600 active:bg-blue-700 active:scale-95',
        secondary: 'bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80 active:scale-95',
        outline: 'border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground active:scale-95',
        ghost: 'hover:bg-accent hover:text-accent-foreground active:scale-95',
        link: 'text-primary underline-offset-4 hover:underline active:opacity-70',
        destructive: 'bg-red-500 text-white shadow-md hover:bg-red-600 active:bg-red-700 active:scale-95',
        success: 'bg-green-500 text-white shadow-md hover:bg-green-600 active:bg-green-700 active:scale-95',
        warning: 'bg-yellow-500 text-white shadow-md hover:bg-yellow-600 active:bg-yellow-700 active:scale-95',
      },
      // 尺寸变体
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-9 px-4 py-2',
        lg: 'h-10 px-6',
        xl: 'h-11 px-8',
        icon: 'h-9 w-9',
      },
      // 圆角变体
      rounded: {
        none: 'rounded-none',
        sm: 'rounded-sm',
        md: 'rounded-md',
        lg: 'rounded-lg',
        full: 'rounded-full',
      },
      // 全宽变体
      fullWidth: {
        true: 'w-full',
        false: 'w-auto',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
      rounded: 'md',
      fullWidth: false,
    },
  }
);

// 按钮组件Props类型
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** 是否为异步操作（显示加载状态） */
  loading?: boolean;
  /** 加载状态文本 */
  loadingText?: string;
  /** 左侧图标 */
  leftIcon?: React.ReactNode;
  /** 右侧图标 */
  rightIcon?: React.ReactNode;
  /** 按钮内容 */
  children?: React.ReactNode;
}

/**
 * Button 组件
 *
 * @example
 * ```tsx
 * // 基础用法
 * <Button>点击我</Button>
 *
 * // 不同样式
 * <Button variant="primary">主要按钮</Button>
 * <Button variant="outline">轮廓按钮</Button>
 *
 * // 不同尺寸
 * <Button size="sm">小按钮</Button>
 * <Button size="lg">大按钮</Button>
 *
 * // 带图标
 * <Button leftIcon={<PlusIcon />}>添加</Button>
 * <Button rightIcon={<ArrowRightIcon />}>下一步</Button>
 *
 * // 加载状态
 * <Button loading>提交中...</Button>
 * <Button loading loadingText="保存中...">保存</Button>
 *
 * // 全宽
 * <Button fullWidth>全宽按钮</Button>
 * ```
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      rounded,
      fullWidth,
      loading = false,
      loadingText,
      leftIcon,
      rightIcon,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        className={cn(buttonVariants({ variant, size, rounded, fullWidth, className }))}
        ref={ref}
        disabled={isDisabled}
        {...props}
      >
        {/* 左侧图标或加载图标 */}
        {loading ? (
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
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
        ) : (
          leftIcon
        )}

        {/* 按钮文本 */}
        {loading && loadingText ? loadingText : children}

        {/* 右侧图标 */}
        {!loading && rightIcon}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { buttonVariants };