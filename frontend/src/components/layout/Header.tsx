/**
 * Header 组件
 * 应用顶部导航栏，包含logo、导航菜单、主题切换等
 */

import React from 'react';
import { Menu, Sun, Moon, Monitor, Settings, User } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useTheme } from '@/hooks/useTheme';
import { Button } from '@/components/ui/Button';

export interface HeaderProps {
  /** 自定义类名 */
  className?: string;
  /** 是否显示菜单按钮（用于移动端） */
  showMenuButton?: boolean;
  /** 菜单按钮点击回调 */
  onMenuClick?: () => void;
  /** 是否显示主题切换 */
  showThemeToggle?: boolean;
  /** 是否显示用户菜单 */
  showUserMenu?: boolean;
  /** 应用标题 */
  title?: string;
  /** 应用logo */
  logo?: React.ReactNode;
}

/**
 * Header 组件
 *
 * @example
 * ```tsx
 * <Header
 *   title="AI Prompt Generator"
 *   showThemeToggle
 *   showUserMenu
 *   onMenuClick={() => setMobileMenuOpen(true)}
 * />
 * ```
 */
export const Header: React.FC<HeaderProps> = ({
  className,
  showMenuButton = true,
  onMenuClick,
  showThemeToggle = true,
  showUserMenu = true,
  title = 'AI System Prompt Generator',
  logo,
}) => {
  const { theme, setTheme, toggleTheme } = useTheme();

  // 主题图标映射
  const themeIcons = {
    light: Sun,
    dark: Moon,
    system: Monitor,
  };

  const ThemeIcon = themeIcons[theme];

  return (
    <header
      className={cn(
        'sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-sm',
        className
      )}
    >
      <div className="container mx-auto flex h-16 max-w-screen-2xl items-center justify-between px-4">
        {/* 左侧：菜单按钮 + Logo + 标题 */}
        <div className="flex items-center gap-4">
          {/* 移动端菜单按钮 */}
          {showMenuButton && (
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={onMenuClick}
              aria-label="打开菜单"
            >
              <Menu className="h-5 w-5" />
            </Button>
          )}

          {/* Logo 和标题 */}
          <div className="flex items-center gap-3">
            {logo && <div className="flex items-center">{logo}</div>}
            <div className="flex flex-col">
              <h1 className="text-lg font-semibold leading-tight">{title}</h1>
              <span className="hidden text-xs text-muted-foreground sm:block">
                智能提示词生成器
              </span>
            </div>
          </div>
        </div>

        {/* 中间：导航菜单（桌面端） */}
        <nav className="hidden lg:flex items-center space-x-1">
          <Button variant="ghost" size="sm">
            工作台
          </Button>
          <Button variant="ghost" size="sm">
            模板库
          </Button>
          <Button variant="ghost" size="sm">
            我的项目
          </Button>
          <Button variant="ghost" size="sm">
            帮助文档
          </Button>
        </nav>

        {/* 右侧：主题切换 + 用户菜单 */}
        <div className="flex items-center gap-2">
          {/* 主题切换 */}
          {showThemeToggle && (
            <div className="flex items-center">
              {/* 主题切换按钮 */}
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
                aria-label={`当前主题: ${theme}, 点击切换`}
                title="切换主题"
              >
                <ThemeIcon className="h-4 w-4" />
              </Button>

              {/* 主题选择下拉菜单（桌面端） */}
              <div className="hidden lg:block">
                <div className="flex items-center border rounded-md">
                  <Button
                    variant={theme === 'light' ? 'secondary' : 'ghost'}
                    size="sm"
                    onClick={() => setTheme('light')}
                    className="rounded-r-none border-r"
                    aria-label="切换到亮色主题"
                  >
                    <Sun className="h-3 w-3" />
                  </Button>
                  <Button
                    variant={theme === 'dark' ? 'secondary' : 'ghost'}
                    size="sm"
                    onClick={() => setTheme('dark')}
                    className="rounded-none border-r"
                    aria-label="切换到暗色主题"
                  >
                    <Moon className="h-3 w-3" />
                  </Button>
                  <Button
                    variant={theme === 'system' ? 'secondary' : 'ghost'}
                    size="sm"
                    onClick={() => setTheme('system')}
                    className="rounded-l-none"
                    aria-label="使用系统主题"
                  >
                    <Monitor className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* 设置按钮 */}
          <Button variant="ghost" size="icon" aria-label="设置" title="设置">
            <Settings className="h-4 w-4" />
          </Button>

          {/* 用户菜单 */}
          {showUserMenu && (
            <Button variant="ghost" size="icon" aria-label="用户菜单" title="用户菜单">
              <User className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* 移动端导航菜单 */}
      <nav className="border-t bg-background lg:hidden">
        <div className="container mx-auto max-w-screen-2xl px-4 py-2">
          <div className="flex items-center justify-around">
            <Button variant="ghost" size="sm">
              工作台
            </Button>
            <Button variant="ghost" size="sm">
              模板
            </Button>
            <Button variant="ghost" size="sm">
              项目
            </Button>
            <Button variant="ghost" size="sm">
              文档
            </Button>
          </div>
        </div>
      </nav>
    </header>
  );
};