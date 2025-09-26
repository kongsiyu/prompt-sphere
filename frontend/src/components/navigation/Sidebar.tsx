import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Home,
  MessageSquare,
  File,
  Settings,
  ChevronLeft,
  ChevronRight,
  Plus
} from 'lucide-react';
import { navigationItems } from '../../router/routes';

/**
 * 导航菜单项组件
 */
interface NavigationItemProps {
  href: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  isActive: boolean;
  isCollapsed: boolean;
}

const NavigationItem: React.FC<NavigationItemProps> = ({
  href,
  icon,
  children,
  isActive,
  isCollapsed
}) => {
  return (
    <Link
      to={href}
      className={`
        flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors
        ${isActive
          ? 'bg-blue-100 text-blue-700 border-r-2 border-blue-600'
          : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
        }
        ${isCollapsed ? 'justify-center' : ''}
      `}
      title={isCollapsed ? String(children) : undefined}
    >
      <span className="flex-shrink-0">{icon}</span>
      {!isCollapsed && <span className="ml-3">{children}</span>}
    </Link>
  );
};

/**
 * 侧边栏组件
 */
const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();

  const isAuthenticated = !!localStorage.getItem('authToken');

  // 图标映射
  const iconMap: Record<string, React.ReactNode> = {
    Home: <Home className="h-5 w-5" />,
    MessageSquare: <MessageSquare className="h-5 w-5" />,
    FileTemplate: <File className="h-5 w-5" />,
    File: <File className="h-5 w-5" />,
    Settings: <Settings className="h-5 w-5" />
  };

  // 过滤需要认证的菜单项
  const filteredNavItems = navigationItems.filter(
    item => !item.requiresAuth || isAuthenticated
  );

  return (
    <>
      {/* 桌面端侧边栏 */}
      <aside
        className={`
          fixed left-0 top-16 h-[calc(100vh-4rem)] bg-white border-r border-gray-200 transition-all duration-300 z-20
          ${isCollapsed ? 'w-16' : 'w-64'}
          hidden lg:block
        `}
      >
        <div className="flex flex-col h-full">
          {/* 侧边栏切换按钮 */}
          <div className="flex justify-end p-2 border-b border-gray-200">
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100"
            >
              {isCollapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </button>
          </div>

          {/* 导航菜单 */}
          <nav className="flex-1 px-3 py-4 space-y-1">
            {filteredNavItems.map(item => (
              <NavigationItem
                key={item.key}
                href={item.path || '/'}
                icon={iconMap[item.icon || 'Home']}
                isActive={location.pathname === item.path}
                isCollapsed={isCollapsed}
              >
                {item.label}
              </NavigationItem>
            ))}

            {/* 快速操作按钮 */}
            {isAuthenticated && (
              <div className="pt-4 border-t border-gray-200">
                <Link
                  to="/prompts/create"
                  className={`
                    flex items-center px-3 py-2 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors
                    ${isCollapsed ? 'justify-center' : ''}
                  `}
                  title={isCollapsed ? '创建提示词' : undefined}
                >
                  <Plus className="h-5 w-5 flex-shrink-0" />
                  {!isCollapsed && <span className="ml-3">创建提示词</span>}
                </Link>
              </div>
            )}
          </nav>

          {/* 侧边栏底部信息 */}
          {!isCollapsed && (
            <div className="p-3 border-t border-gray-200">
              <div className="text-xs text-gray-500 text-center">
                <p>AI System Prompt Generator</p>
                <p className="mt-1">v1.0.0</p>
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* 移动端侧边栏占位 */}
      <div className={`${isCollapsed ? 'w-16' : 'w-64'} flex-shrink-0 hidden lg:block`} />
    </>
  );
};

export default Sidebar;