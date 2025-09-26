/**
 * UI组件相关类型定义
 */

import type React from 'react';

// 基础组件Props
export interface BaseComponentProps {
  /** 自定义CSS类名 */
  className?: string;
  /** 子元素 */
  children?: React.ReactNode;
}

// 尺寸变体
export type SizeVariant = 'sm' | 'md' | 'lg' | 'xl';

// 颜色变体
export type ColorVariant = 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error';

// 按钮变体
export type ButtonVariant = 'default' | 'primary' | 'secondary' | 'outline' | 'ghost' | 'link' | 'destructive';

// 输入框状态
export type InputStatus = 'default' | 'error' | 'success' | 'warning';

// 模态框尺寸
export type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

// 卡片变体
export type CardVariant = 'default' | 'outlined' | 'elevated' | 'filled';

// 加载状态类型
export type LoadingType = 'spinner' | 'dots' | 'pulse' | 'skeleton';

// 可用的图标名称 (基于 Lucide React)
export type IconName =
  | 'chevron-left'
  | 'chevron-right'
  | 'chevron-up'
  | 'chevron-down'
  | 'x'
  | 'menu'
  | 'search'
  | 'user'
  | 'settings'
  | 'home'
  | 'plus'
  | 'minus'
  | 'check'
  | 'alert-circle'
  | 'info'
  | 'help-circle'
  | 'eye'
  | 'eye-off'
  | 'edit'
  | 'trash'
  | 'download'
  | 'upload'
  | 'external-link'
  | 'copy'
  | 'share'
  | 'heart'
  | 'star'
  | 'bookmark'
  | 'sun'
  | 'moon'
  | 'monitor'
  | 'smartphone'
  | 'tablet'
  | 'laptop'
  | 'desktop-computer';