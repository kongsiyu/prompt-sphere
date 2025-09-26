/**
 * 主题相关类型定义
 */

export type Theme = 'light' | 'dark' | 'system';

export interface ThemeContextType {
  /** 当前主题模式 */
  theme: Theme;
  /** 实际应用的主题 (解析后的，去除system) */
  resolvedTheme: 'light' | 'dark';
  /** 设置主题 */
  setTheme: (theme: Theme) => void;
  /** 切换主题 */
  toggleTheme: () => void;
}

export interface ThemeProviderProps {
  children: React.ReactNode;
  /** 默认主题 */
  defaultTheme?: Theme;
  /** 存储键名 */
  storageKey?: string;
  /** 是否启用系统主题检测 */
  enableSystem?: boolean;
  /** 主题应用到的元素 */
  attribute?: 'class' | 'data-theme';
  /** 禁用过渡动画 */
  disableTransitionOnChange?: boolean;
}