/**
 * Header 组件
 * 应用顶部导航栏，包含logo、导航菜单、主题切换等
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, Sun, Moon, Monitor, Settings, User, LogOut } from 'lucide-react';
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
  const location = useLocation();
  const [userMenuOpen, setUserMenuOpen] = React.useState(false);

  // 检查用户认证状态
  const isAuthenticated = !!localStorage.getItem('authToken');
  const userEmail = localStorage.getItem('userEmail') || 'user@example.com';

  // 主题图标映射
  const themeIcons = {
    light: Sun,
    dark: Moon,
    system: Monitor,
  };

  const ThemeIcon = themeIcons[theme];

  // 注销处理
  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    window.location.href = '/auth/login';
  };

  return (
    <header
      className={cn(
        'sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-sm',
        className
      )}
    >
      <div className="flex h-16 items-center justify-between px-6 w-full">
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
          <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            {logo ? (
              <div className="flex items-center">{logo}</div>
            ) : (
              <div className="flex items-center justify-center w-8 h-8 bg-blue-600 rounded-lg text-white font-bold text-sm">
                AI
              </div>
            )}
            <div className="flex flex-col">
              <h1 className="text-lg font-semibold leading-tight">Prompt Generator</h1>
              <span className="hidden text-xs text-muted-foreground sm:block">
                智能提示词生成器
              </span>
            </div>
          </Link>
        </div>

        {/* 中间：导航菜单（桌面端） */}
        <nav className="hidden lg:flex items-center space-x-1">
          <NavItem href="/dashboard" label="工作台" />
          <NavItem href="/prompts" label="提示词管理" />
          <NavItem href="/templates" label="模板库" />
          <NavItem href="/settings" label="设置" />
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


          {/* 用户菜单 */}
          {showUserMenu && (
            <div className="relative">
              {isAuthenticated ? (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center gap-2"
                    aria-label="用户菜单"
                  >
                    <User className="h-4 w-4" />
                    <span className="hidden sm:inline">{userEmail.split('@')[0]}</span>
                  </Button>

                  {userMenuOpen && (
                    <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-lg shadow-lg border z-50">
                      <div className="p-2">
                        <div className="px-3 py-2 text-sm text-gray-500 border-b">
                          {userEmail}
                        </div>
                        <Link
                          to="/settings"
                          className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50 rounded"
                          onClick={() => setUserMenuOpen(false)}
                        >
                          <Settings className="h-4 w-4" />
                          设置
                        </Link>
                        <button
                          onClick={handleLogout}
                          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded"
                        >
                          <LogOut className="h-4 w-4" />
                          注销
                        </button>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <Link to="/auth/login">
                  <Button variant="ghost" size="sm">
                    登录
                  </Button>
                </Link>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 移动端导航菜单 */}
      <nav className="border-t bg-background lg:hidden">
        <div className="px-6 py-2 w-full">
          <div className="flex items-center justify-around">
            <NavItem href="/dashboard" label="工作台" />
            <NavItem href="/prompts" label="提示词" />
            <NavItem href="/templates" label="模板" />
            <NavItem href="/settings" label="设置" />
          </div>
        </div>
      </nav>
    </header>
  );
};

/**
 * NavItem 组件 - 导航菜单项
 */
interface NavItemProps {
  href: string;
  label: string;
}

const NavItem: React.FC<NavItemProps> = ({ href, label }) => {
  const location = useLocation();
  const isActive = location.pathname === href;

  return (
    <Link to={href}>
      <Button
        variant={isActive ? "secondary" : "ghost"}
        size="sm"
        className={cn(
          "transition-colors",
          isActive && "bg-blue-100 text-blue-700 hover:bg-blue-200"
        )}
      >
        {label}
      </Button>
    </Link>
  );
};