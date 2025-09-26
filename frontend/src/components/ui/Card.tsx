/**
 * Card 组件
 * 灵活的卡片布局组件，支持头部、内容、底部等区域
 */

import React, { forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';

// 卡片样式变体定义
const cardVariants = cva(
  // 基础样式
  'rounded-lg border bg-card text-card-foreground transition-all duration-200',
  {
    variants: {
      // 样式变体
      variant: {
        default: 'shadow-sm',
        outlined: 'border-2',
        elevated: 'shadow-lg hover:shadow-xl',
        filled: 'bg-muted/50',
      },
      // 尺寸变体
      size: {
        sm: 'p-3',
        md: 'p-4',
        lg: 'p-6',
        xl: 'p-8',
      },
      // 圆角变体
      rounded: {
        none: 'rounded-none',
        sm: 'rounded-sm',
        md: 'rounded-md',
        lg: 'rounded-lg',
        xl: 'rounded-xl',
        '2xl': 'rounded-2xl',
      },
      // 悬停效果
      hoverable: {
        true: 'cursor-pointer hover:shadow-md hover:scale-[1.01] active:scale-[0.99]',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
      rounded: 'lg',
      hoverable: false,
    },
  }
);

// 卡片头部样式
const cardHeaderVariants = cva(
  'flex flex-col space-y-1.5',
  {
    variants: {
      padding: {
        none: '',
        sm: 'p-3',
        md: 'p-4',
        lg: 'p-6',
      },
    },
    defaultVariants: {
      padding: 'md',
    },
  }
);

// 卡片内容样式
const cardContentVariants = cva(
  '',
  {
    variants: {
      padding: {
        none: '',
        sm: 'p-3',
        md: 'p-4',
        lg: 'p-6',
      },
    },
    defaultVariants: {
      padding: 'md',
    },
  }
);

// 卡片底部样式
const cardFooterVariants = cva(
  'flex items-center',
  {
    variants: {
      padding: {
        none: '',
        sm: 'p-3',
        md: 'p-4',
        lg: 'p-6',
      },
    },
    defaultVariants: {
      padding: 'md',
    },
  }
);

// 基础卡片Props
export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

// 卡片头部Props
export interface CardHeaderProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardHeaderVariants> {}

// 卡片标题Props
export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  /** 标题级别 */
  level?: 1 | 2 | 3 | 4 | 5 | 6;
}

// 卡片描述Props
export interface CardDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {}

// 卡片内容Props
export interface CardContentProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardContentVariants> {}

// 卡片底部Props
export interface CardFooterProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardFooterVariants> {}

/**
 * Card 主容器
 *
 * @example
 * ```tsx
 * <Card>
 *   <CardHeader>
 *     <CardTitle>标题</CardTitle>
 *     <CardDescription>描述</CardDescription>
 *   </CardHeader>
 *   <CardContent>
 *     内容区域
 *   </CardContent>
 *   <CardFooter>
 *     底部操作
 *   </CardFooter>
 * </Card>
 * ```
 */
export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, size, rounded, hoverable, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardVariants({ variant, size, rounded, hoverable, className }))}
      {...props}
    />
  )
);
Card.displayName = 'Card';

/**
 * CardHeader 头部区域
 */
export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, padding, ...props }, ref) => (
    <div ref={ref} className={cn(cardHeaderVariants({ padding, className }))} {...props} />
  )
);
CardHeader.displayName = 'CardHeader';

/**
 * CardTitle 标题
 */
export const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className, level = 3, children, ...props }, ref) => {
    const Heading = `h${level}` as keyof JSX.IntrinsicElements;

    return (
      <Heading
        ref={ref as any}
        className={cn(
          'font-semibold leading-none tracking-tight',
          {
            'text-2xl': level === 1,
            'text-xl': level === 2,
            'text-lg': level === 3,
            'text-base': level === 4,
            'text-sm': level === 5,
            'text-xs': level === 6,
          },
          className
        )}
        {...props}
      >
        {children}
      </Heading>
    );
  }
);
CardTitle.displayName = 'CardTitle';

/**
 * CardDescription 描述文本
 */
export const CardDescription = forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ className, ...props }, ref) => (
    <p ref={ref} className={cn('text-sm text-muted-foreground', className)} {...props} />
  )
);
CardDescription.displayName = 'CardDescription';

/**
 * CardContent 内容区域
 */
export const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, padding, ...props }, ref) => (
    <div ref={ref} className={cn(cardContentVariants({ padding, className }))} {...props} />
  )
);
CardContent.displayName = 'CardContent';

/**
 * CardFooter 底部区域
 */
export const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, padding, ...props }, ref) => (
    <div ref={ref} className={cn(cardFooterVariants({ padding, className }))} {...props} />
  )
);
CardFooter.displayName = 'CardFooter';

export { cardVariants, cardHeaderVariants, cardContentVariants, cardFooterVariants };