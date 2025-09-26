import React from 'react';

interface MinimalLayoutProps {
  children: React.ReactNode;
}

/**
 * 最小布局组件 - 用于404页面等简单页面
 */
const MinimalLayout: React.FC<MinimalLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center">
      <div className="max-w-2xl mx-auto px-4">
        {children}
      </div>
    </div>
  );
};

export default MinimalLayout;