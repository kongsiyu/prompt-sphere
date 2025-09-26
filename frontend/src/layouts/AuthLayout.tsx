import React from 'react';

interface AuthLayoutProps {
  children: React.ReactNode;
}

/**
 * 认证布局组件 - 用于登录、注册等认证相关页面
 */
const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="flex min-h-screen items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-md space-y-8">
          {/* 应用Logo和标题 */}
          <div className="text-center">
            <h2 className="mt-6 text-3xl font-bold tracking-tight text-gray-900">
              AI System Prompt Generator
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              智能系统提示词生成器
            </p>
          </div>

          {/* 认证内容 */}
          <div className="bg-white rounded-lg shadow-lg p-8">
            {children}
          </div>

          {/* 页脚信息 */}
          <div className="text-center">
            <p className="text-xs text-gray-500">
              © 2024 AI System Prompt Generator. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;