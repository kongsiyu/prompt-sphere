/**
 * 主题上下文提供器
 * 支持亮色/暗色主题切换，系统主题检测，主题持久化
 */

import React, { createContext, useCallback, useEffect, useState } from 'react';
import type { Theme, ThemeContextType, ThemeProviderProps } from '@/types/theme';
import {
  applyTheme,
  createSystemThemeListener,
  getStoredTheme,
  resolveTheme,
  setStoredTheme,
} from '@/utils/theme';

// 创建主题上下文
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/**
 * 主题提供器组件
 */
export function ThemeProvider({
  children,
  defaultTheme = 'system',
  storageKey = 'theme-preference',
  enableSystem = true,
  attribute = 'class',
  disableTransitionOnChange = false,
}: ThemeProviderProps) {
  // 初始化主题状态
  const [theme, setThemeState] = useState<Theme>(() => {
    // 服务端渲染时使用默认主题
    if (typeof window === 'undefined') {
      return defaultTheme;
    }

    // 尝试从本地存储获取主题
    const storedTheme = getStoredTheme(storageKey);
    return storedTheme || defaultTheme;
  });

  // 解析当前主题
  const resolvedTheme = resolveTheme(theme);

  /**
   * 设置主题
   */
  const setTheme = useCallback(
    (newTheme: Theme) => {
      setThemeState(newTheme);
      setStoredTheme(storageKey, newTheme);
    },
    [storageKey]
  );

  /**
   * 切换主题 (在 light 和 dark 之间切换)
   */
  const toggleTheme = useCallback(() => {
    const newTheme = resolvedTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  }, [resolvedTheme, setTheme]);

  /**
   * 应用主题到DOM
   */
  useEffect(() => {
    applyTheme(resolvedTheme, attribute, disableTransitionOnChange);
  }, [resolvedTheme, attribute, disableTransitionOnChange]);

  /**
   * 监听系统主题变化
   */
  useEffect(() => {
    if (!enableSystem || theme !== 'system') {
      return;
    }

    const cleanup = createSystemThemeListener((systemTheme) => {
      if (theme === 'system') {
        applyTheme(systemTheme, attribute, disableTransitionOnChange);
      }
    });

    return cleanup;
  }, [theme, enableSystem, attribute, disableTransitionOnChange]);

  /**
   * 初始化时应用主题
   */
  useEffect(() => {
    // 确保在客户端初始化时正确应用主题
    if (typeof window !== 'undefined') {
      applyTheme(resolvedTheme, attribute, true);
    }
  }, []);

  const contextValue: ThemeContextType = {
    theme,
    resolvedTheme,
    setTheme,
    toggleTheme,
  };

  return <ThemeContext.Provider value={contextValue}>{children}</ThemeContext.Provider>;
}

/**
 * 获取主题上下文的钩子
 */
export function useThemeContext(): ThemeContextType {
  const context = React.useContext(ThemeContext);

  if (context === undefined) {
    throw new Error('useThemeContext 必须在 ThemeProvider 内部使用');
  }

  return context;
}

// 导出上下文以供测试使用
export { ThemeContext };