/**
 * 主题钩子 - 提供便捷的主题访问和操作接口
 */

import { useThemeContext } from '@/contexts/ThemeContext';

/**
 * 使用主题的钩子
 *
 * @returns 主题上下文对象
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme();
 *
 *   return (
 *     <div>
 *       <p>当前主题: {theme}</p>
 *       <p>解析后的主题: {resolvedTheme}</p>
 *       <button onClick={toggleTheme}>切换主题</button>
 *       <button onClick={() => setTheme('system')}>使用系统主题</button>
 *     </div>
 *   );
 * }
 * ```
 */
export const useTheme = useThemeContext;