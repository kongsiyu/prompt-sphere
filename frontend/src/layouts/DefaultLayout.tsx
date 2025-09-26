import React from 'react';
import Navbar from '../components/navigation/Navbar';
import Sidebar from '../components/navigation/Sidebar';
import Breadcrumb from '../components/navigation/Breadcrumb';

interface DefaultLayoutProps {
  children: React.ReactNode;
}

/**
 * 默认布局组件 - 包含导航栏、侧边栏和面包屑
 */
const DefaultLayout: React.FC<DefaultLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <Navbar />

      <div className="flex">
        {/* 侧边栏 */}
        <Sidebar />

        {/* 主内容区域 */}
        <main className="flex-1 lg:ml-64 pt-16">
          <div className="p-4">
            {/* 面包屑导航 */}
            <Breadcrumb />

            {/* 页面内容 */}
            <div className="mt-4">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default DefaultLayout;