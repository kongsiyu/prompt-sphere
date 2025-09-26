/**
 * Modal 组件
 * 模态框组件，支持不同尺寸、动画效果和无障碍访问
 */

import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { cva, type VariantProps } from 'class-variance-authority';
import { X } from 'lucide-react';
import { cn } from '@/utils/cn';
import { Button } from './Button';

// 模态框样式变体定义
const modalVariants = cva(
  'relative bg-background rounded-lg shadow-lg transform transition-all duration-200',
  {
    variants: {
      // 尺寸变体
      size: {
        xs: 'w-full max-w-xs',
        sm: 'w-full max-w-sm',
        md: 'w-full max-w-md',
        lg: 'w-full max-w-lg',
        xl: 'w-full max-w-xl',
        '2xl': 'w-full max-w-2xl',
        '3xl': 'w-full max-w-3xl',
        '4xl': 'w-full max-w-4xl',
        '5xl': 'w-full max-w-5xl',
        full: 'w-full h-full max-w-none max-h-none rounded-none',
      },
      // 动画效果
      animation: {
        scale: 'scale-100 opacity-100',
        slideUp: 'translate-y-0 opacity-100',
        slideDown: 'translate-y-0 opacity-100',
        fade: 'opacity-100',
      },
    },
    defaultVariants: {
      size: 'md',
      animation: 'scale',
    },
  }
);

// 模态框背景样式
const overlayVariants = cva(
  'fixed inset-0 z-50 bg-black/50 backdrop-blur-sm transition-opacity duration-200',
  {
    variants: {
      visible: {
        true: 'opacity-100',
        false: 'opacity-0',
      },
    },
  }
);

// 模态框Props类型
export interface ModalProps extends VariantProps<typeof modalVariants> {
  /** 是否显示模态框 */
  open: boolean;
  /** 关闭模态框回调 */
  onClose: () => void;
  /** 模态框标题 */
  title?: React.ReactNode;
  /** 模态框内容 */
  children: React.ReactNode;
  /** 模态框底部 */
  footer?: React.ReactNode;
  /** 自定义类名 */
  className?: string;
  /** 覆盖层类名 */
  overlayClassName?: string;
  /** 头部类名 */
  headerClassName?: string;
  /** 内容类名 */
  contentClassName?: string;
  /** 底部类名 */
  footerClassName?: string;
  /** 是否显示关闭按钮 */
  showCloseButton?: boolean;
  /** 是否点击外部关闭 */
  closeOnOverlayClick?: boolean;
  /** 是否按ESC关闭 */
  closeOnEscape?: boolean;
  /** 是否阻止滚动 */
  preventScroll?: boolean;
  /** 焦点陷阱 */
  trapFocus?: boolean;
  /** 自动聚焦元素选择器 */
  autoFocus?: string;
  /** 关闭前确认 */
  onBeforeClose?: () => boolean | Promise<boolean>;
}

/**
 * Modal 组件
 *
 * @example
 * ```tsx
 * // 基础模态框
 * <Modal open={isOpen} onClose={() => setIsOpen(false)} title="标题">
 *   <div>模态框内容</div>
 * </Modal>
 *
 * // 带底部操作的模态框
 * <Modal
 *   open={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   title="确认操作"
 *   footer={
 *     <div className="flex gap-2">
 *       <Button variant="outline" onClick={() => setIsOpen(false)}>取消</Button>
 *       <Button onClick={handleConfirm}>确认</Button>
 *     </div>
 *   }
 * >
 *   <div>确认要执行此操作吗？</div>
 * </Modal>
 *
 * // 大尺寸模态框
 * <Modal open={isOpen} onClose={() => setIsOpen(false)} size="2xl">
 *   <div>大尺寸内容</div>
 * </Modal>
 * ```
 */
export const Modal: React.FC<ModalProps> = ({
  open,
  onClose,
  title,
  children,
  footer,
  className,
  overlayClassName,
  headerClassName,
  contentClassName,
  footerClassName,
  size,
  animation,
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  preventScroll = true,
  trapFocus = true,
  autoFocus,
  onBeforeClose,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // 处理关闭
  const handleClose = async () => {
    if (onBeforeClose) {
      const canClose = await onBeforeClose();
      if (!canClose) return;
    }
    onClose();
  };

  // 处理键盘事件
  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && closeOnEscape) {
        handleClose();
      }

      // 焦点陷阱
      if (event.key === 'Tab' && trapFocus) {
        const modal = modalRef.current;
        if (!modal) return;

        const focusableElements = modal.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0] as HTMLElement;
        const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, closeOnEscape, trapFocus, handleClose]);

  // 管理滚动和焦点
  useEffect(() => {
    if (open) {
      // 保存当前焦点
      previousFocusRef.current = document.activeElement as HTMLElement;

      // 阻止滚动
      if (preventScroll) {
        document.body.style.overflow = 'hidden';
      }

      // 自动聚焦
      setTimeout(() => {
        if (autoFocus) {
          const element = modalRef.current?.querySelector(autoFocus) as HTMLElement;
          element?.focus();
        } else if (modalRef.current) {
          const firstFocusable = modalRef.current.querySelector(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          ) as HTMLElement;
          firstFocusable?.focus();
        }
      }, 100);
    } else {
      // 恢复滚动
      if (preventScroll) {
        document.body.style.overflow = '';
      }

      // 恢复焦点
      if (previousFocusRef.current) {
        previousFocusRef.current.focus();
      }
    }

    return () => {
      if (preventScroll) {
        document.body.style.overflow = '';
      }
    };
  }, [open, preventScroll, autoFocus]);

  // 如果未打开，不渲染
  if (!open) return null;

  // 获取动画初始状态
  const getInitialAnimationClass = () => {
    switch (animation) {
      case 'scale':
        return 'scale-95 opacity-0';
      case 'slideUp':
        return 'translate-y-4 opacity-0';
      case 'slideDown':
        return '-translate-y-4 opacity-0';
      case 'fade':
        return 'opacity-0';
      default:
        return 'scale-95 opacity-0';
    }
  };

  const modal = (
    <div
      className={cn(overlayVariants({ visible: true }), overlayClassName)}
      onClick={closeOnOverlayClick ? handleClose : undefined}
    >
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          ref={modalRef}
          className={cn(
            modalVariants({ size, animation }),
            open ? '' : getInitialAnimationClass(),
            'mx-auto',
            className
          )}
          onClick={(e) => e.stopPropagation()}
          role="dialog"
          aria-modal="true"
          aria-labelledby={title ? 'modal-title' : undefined}
        >
          {/* 头部 */}
          {(title || showCloseButton) && (
            <div
              className={cn(
                'flex items-center justify-between p-6 border-b',
                headerClassName
              )}
            >
              {title && (
                <h2
                  id="modal-title"
                  className="text-lg font-semibold text-foreground"
                >
                  {title}
                </h2>
              )}
              {showCloseButton && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleClose}
                  aria-label="关闭模态框"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          )}

          {/* 内容 */}
          <div className={cn('p-6', contentClassName)}>
            {children}
          </div>

          {/* 底部 */}
          {footer && (
            <div
              className={cn(
                'flex items-center justify-end gap-2 p-6 border-t bg-muted/20',
                footerClassName
              )}
            >
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // 渲染到 portal
  return createPortal(modal, document.body);
};

/**
 * 确认对话框组件
 */
export interface ConfirmModalProps {
  /** 是否显示 */
  open: boolean;
  /** 关闭回调 */
  onClose: () => void;
  /** 确认回调 */
  onConfirm: () => void | Promise<void>;
  /** 标题 */
  title?: string;
  /** 内容 */
  message?: React.ReactNode;
  /** 确认按钮文本 */
  confirmText?: string;
  /** 取消按钮文本 */
  cancelText?: string;
  /** 确认按钮样式 */
  confirmVariant?: 'default' | 'primary' | 'destructive' | 'success' | 'warning';
  /** 是否加载中 */
  loading?: boolean;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  open,
  onClose,
  onConfirm,
  title = '确认操作',
  message = '确定要执行此操作吗？',
  confirmText = '确认',
  cancelText = '取消',
  confirmVariant = 'primary',
  loading = false,
}) => {
  const handleConfirm = async () => {
    await onConfirm();
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <div className="flex gap-2">
          <Button variant="outline" onClick={onClose} disabled={loading}>
            {cancelText}
          </Button>
          <Button
            variant={confirmVariant}
            onClick={handleConfirm}
            loading={loading}
          >
            {confirmText}
          </Button>
        </div>
      }
    >
      <div className="text-muted-foreground">{message}</div>
    </Modal>
  );
};

export { modalVariants, overlayVariants };