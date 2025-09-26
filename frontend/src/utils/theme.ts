/**
 * 主题相关工具函数
 */

import type { Theme } from '@/types/theme';

/**
 * 获取系统主题偏好
 */
export function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') {
    return 'light';
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

/**
 * 解析主题值，将 'system' 转换为实际主题
 */
export function resolveTheme(theme: Theme): 'light' | 'dark' {
  if (theme === 'system') {
    return getSystemTheme();
  }
  return theme;
}

/**
 * 从本地存储获取主题
 */
export function getStoredTheme(storageKey: string): Theme | null {
  try {
    const storedTheme = localStorage.getItem(storageKey);
    if (storedTheme && ['light', 'dark', 'system'].includes(storedTheme)) {
      return storedTheme as Theme;
    }
  } catch (error) {
    console.warn('获取存储的主题失败:', error);
  }
  return null;
}

/**
 * 将主题保存到本地存储
 */
export function setStoredTheme(storageKey: string, theme: Theme): void {
  try {
    localStorage.setItem(storageKey, theme);
  } catch (error) {
    console.warn('保存主题到本地存储失败:', error);
  }
}

/**
 * 应用主题到文档
 */
export function applyTheme(
  theme: 'light' | 'dark',
  attribute: 'class' | 'data-theme' = 'class',
  disableTransition = false
): void {
  const root = document.documentElement;

  // 禁用过渡动画防止闪烁
  if (disableTransition) {
    const css = document.createElement('style');
    css.appendChild(
      document.createTextNode(
        '*,*::before,*::after{transition-property:none!important;animation-duration:0.01ms!important;animation-delay:0.01ms!important}'
      )
    );
    document.head.appendChild(css);

    // 强制重排
    void document.body.offsetHeight;

    // 100ms后移除禁用样式
    setTimeout(() => {
      if (css.parentNode) {
        css.parentNode.removeChild(css);
      }
    }, 100);
  }

  if (attribute === 'class') {
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
  } else {
    root.setAttribute('data-theme', theme);
  }

  // 设置颜色方案以提高性能
  root.style.colorScheme = theme;
}

/**
 * 监听系统主题变化
 */
export function createSystemThemeListener(
  callback: (theme: 'light' | 'dark') => void
): () => void {
  if (typeof window === 'undefined') {
    return () => {};
  }

  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

  const handleChange = (e: MediaQueryListEvent) => {
    callback(e.matches ? 'dark' : 'light');
  };

  mediaQuery.addEventListener('change', handleChange);

  return () => {
    mediaQuery.removeEventListener('change', handleChange);
  };
}