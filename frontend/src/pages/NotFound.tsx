import React from 'react';
import { Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/useNavigation';
import { Home, ArrowLeft } from 'lucide-react';

/**
 * 404页面组件
 */
const NotFound: React.FC = () => {
  usePageTitle('页面未找到');

  return (
    <div className="text-center">
      <div className="mb-8">
        <div className="inline-flex items-center justify-center w-24 h-24 bg-gray-100 rounded-full mb-6">
          <span className="text-4xl font-bold text-gray-400">404</span>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">页面未找到</h1>
        <p className="text-lg text-gray-600 mb-8">
          抱歉，您访问的页面不存在或已被移动
        </p>
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <Link
          to="/"
          className="flex items-center bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          <Home className="h-5 w-5 mr-2" />
          返回首页
        </Link>
        <button
          onClick={() => window.history.back()}
          className="flex items-center bg-gray-100 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          返回上一页
        </button>
      </div>

      <div className="mt-12 text-center">
        <p className="text-sm text-gray-500">
          如果您认为这是一个错误，请
          <a href="mailto:support@example.com" className="text-blue-600 hover:text-blue-700 mx-1">
            联系我们
          </a>
        </p>
      </div>
    </div>
  );
};

export default NotFound;