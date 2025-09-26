import React from 'react';
import { Link } from 'react-router-dom';
import { usePageTitle } from '../../hooks/useNavigation';
import { Plus, Search, Filter } from 'lucide-react';

/**
 * 提示词管理页面
 */
const Prompts: React.FC = () => {
  usePageTitle('提示词管理');

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">提示词管理</h1>
          <p className="mt-1 text-sm text-gray-500">管理和组织您的AI提示词</p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Link
            to="/prompt-editor/create"
            className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center"
          >
            <Plus className="h-5 w-5 mr-2" />
            创建提示词
          </Link>
        </div>
      </div>

      {/* 搜索和过滤 */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder="搜索提示词..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
        <button className="flex items-center px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
          <Filter className="h-5 w-5 mr-2" />
          筛选
        </button>
      </div>

      {/* 提示词列表 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6">
          <div className="text-center py-12">
            <Plus className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无提示词</h3>
            <p className="text-gray-500 mb-6">开始创建您的第一个提示词</p>
            <Link
              to="/prompt-editor/create"
              className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors inline-flex items-center"
            >
              <Plus className="h-5 w-5 mr-2" />
              创建提示词
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Prompts;