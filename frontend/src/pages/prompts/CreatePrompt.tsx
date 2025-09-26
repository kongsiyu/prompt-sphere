import React from 'react';
import { usePageTitle } from '../../hooks/useNavigation';
import { Save, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * 创建提示词页面
 */
const CreatePrompt: React.FC = () => {
  usePageTitle('创建提示词');

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/prompts"
            className="flex items-center text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft className="h-5 w-5 mr-1" />
            返回
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">创建提示词</h1>
            <p className="mt-1 text-sm text-gray-500">创建一个新的AI提示词</p>
          </div>
        </div>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center">
          <Save className="h-5 w-5 mr-2" />
          保存
        </button>
      </div>

      {/* 创建表单 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="space-y-6">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700">
              标题
            </label>
            <input
              type="text"
              id="title"
              name="title"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="请输入提示词标题"
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
              描述
            </label>
            <textarea
              id="description"
              name="description"
              rows={3}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="请输入提示词描述"
            />
          </div>

          <div>
            <label htmlFor="content" className="block text-sm font-medium text-gray-700">
              提示词内容
            </label>
            <textarea
              id="content"
              name="content"
              rows={8}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 font-mono"
              placeholder="请输入提示词内容..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="category" className="block text-sm font-medium text-gray-700">
                分类
              </label>
              <select
                id="category"
                name="category"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">选择分类</option>
                <option value="general">通用</option>
                <option value="coding">编程</option>
                <option value="writing">写作</option>
                <option value="analysis">分析</option>
              </select>
            </div>

            <div>
              <label htmlFor="tags" className="block text-sm font-medium text-gray-700">
                标签
              </label>
              <input
                type="text"
                id="tags"
                name="tags"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="使用逗号分隔多个标签"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreatePrompt;