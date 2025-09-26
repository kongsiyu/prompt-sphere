/**
 * Input 组件
 * 支持多种样式、状态、图标和无障碍访问
 */

import React, { forwardRef, useState } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';
import { Eye, EyeOff } from 'lucide-react';

// 输入框样式变体定义
const inputVariants = cva(
  // 基础样式
  'flex w-full rounded-md border bg-background text-sm transition-all duration-200 file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-50',
  {
    variants: {
      // 尺寸变体
      size: {
        sm: 'h-8 px-2 py-1 text-xs',
        md: 'h-9 px-3 py-2 text-sm',
        lg: 'h-10 px-4 py-2',
        xl: 'h-11 px-4 py-2 text-base',
      },
      // 状态变体
      status: {
        default: 'border-input',
        error: 'border-red-500 focus-visible:ring-red-500',
        success: 'border-green-500 focus-visible:ring-green-500',
        warning: 'border-yellow-500 focus-visible:ring-yellow-500',
      },
      // 圆角变体
      rounded: {
        none: 'rounded-none',
        sm: 'rounded-sm',
        md: 'rounded-md',
        lg: 'rounded-lg',
        full: 'rounded-full',
      },
    },
    defaultVariants: {
      size: 'md',
      status: 'default',
      rounded: 'md',
    },
  }
);

// 输入框组件Props类型
export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof inputVariants> {
  /** 标签文本 */
  label?: string;
  /** 帮助文本 */
  helperText?: string;
  /** 错误信息 */
  error?: string;
  /** 成功信息 */
  success?: string;
  /** 警告信息 */
  warning?: string;
  /** 左侧图标 */
  leftIcon?: React.ReactNode;
  /** 右侧图标 */
  rightIcon?: React.ReactNode;
  /** 是否显示清除按钮 */
  clearable?: boolean;
  /** 清除按钮回调 */
  onClear?: () => void;
  /** 容器类名 */
  containerClassName?: string;
  /** 标签类名 */
  labelClassName?: string;
  /** 帮助文本类名 */
  helperClassName?: string;
}

/**
 * Input 组件
 *
 * @example
 * ```tsx
 * // 基础用法
 * <Input placeholder="请输入内容" />
 *
 * // 带标签和帮助文本
 * <Input
 *   label="用户名"
 *   placeholder="请输入用户名"
 *   helperText="用户名长度为3-20个字符"
 * />
 *
 * // 不同状态
 * <Input status="error" error="用户名不能为空" />
 * <Input status="success" success="验证通过" />
 *
 * // 带图标
 * <Input leftIcon={<UserIcon />} placeholder="用户名" />
 * <Input rightIcon={<SearchIcon />} placeholder="搜索" />
 *
 * // 可清除
 * <Input clearable onClear={() => setValue('')} />
 *
 * // 密码输入框
 * <Input type="password" />
 * ```
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      containerClassName,
      labelClassName,
      helperClassName,
      size,
      status,
      rounded,
      type = 'text',
      label,
      helperText,
      error,
      success,
      warning,
      leftIcon,
      rightIcon,
      clearable,
      onClear,
      value,
      onChange,
      ...props
    },
    ref
  ) => {
    const [showPassword, setShowPassword] = useState(false);
    const [internalValue, setInternalValue] = useState(value || '');

    // 确定当前状态
    const currentStatus = error ? 'error' : success ? 'success' : warning ? 'warning' : status;

    // 确定状态消息
    const statusMessage = error || success || warning || helperText;

    // 处理值变化
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setInternalValue(newValue);
      onChange?.(e);
    };

    // 处理清除
    const handleClear = () => {
      setInternalValue('');
      onClear?.();
      // 触发 onChange 事件
      const event = new Event('input', { bubbles: true });
      Object.defineProperty(event, 'target', {
        value: { value: '' },
        enumerable: true,
      });
      onChange?.(event as any);
    };

    // 切换密码显示
    const togglePasswordVisibility = () => {
      setShowPassword(!showPassword);
    };

    // 确定输入框类型
    const inputType = type === 'password' && showPassword ? 'text' : type;

    // 确定是否显示值
    const displayValue = value !== undefined ? value : internalValue;
    const hasValue = String(displayValue).length > 0;

    return (
      <div className={cn('w-full', containerClassName)}>
        {/* 标签 */}
        {label && (
          <label className={cn('mb-1.5 block text-sm font-medium text-foreground', labelClassName)}>
            {label}
          </label>
        )}

        {/* 输入框容器 */}
        <div className="relative">
          {/* 左侧图标 */}
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
              {leftIcon}
            </div>
          )}

          {/* 输入框 */}
          <input
            type={inputType}
            className={cn(
              inputVariants({ size, status: currentStatus, rounded }),
              leftIcon && 'pl-10',
              (rightIcon || clearable || type === 'password') && 'pr-10',
              className
            )}
            ref={ref}
            value={displayValue}
            onChange={handleChange}
            {...props}
          />

          {/* 右侧图标区域 */}
          {(rightIcon || clearable || type === 'password') && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
              {/* 清除按钮 */}
              {clearable && hasValue && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="清除内容"
                >
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              )}

              {/* 密码切换按钮 */}
              {type === 'password' && (
                <button
                  type="button"
                  onClick={togglePasswordVisibility}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={showPassword ? '隐藏密码' : '显示密码'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              )}

              {/* 自定义右侧图标 */}
              {rightIcon && !clearable && type !== 'password' && (
                <div className="text-muted-foreground">{rightIcon}</div>
              )}
            </div>
          )}
        </div>

        {/* 状态消息 */}
        {statusMessage && (
          <p
            className={cn(
              'mt-1.5 text-xs',
              {
                'text-red-500': error,
                'text-green-500': success,
                'text-yellow-500': warning,
                'text-muted-foreground': !error && !success && !warning,
              },
              helperClassName
            )}
          >
            {statusMessage}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { inputVariants };