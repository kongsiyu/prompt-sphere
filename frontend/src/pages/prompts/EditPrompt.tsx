import React from 'react';
import { usePageTitle } from '../../hooks/useNavigation';
import { Save, ArrowLeft } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

/**
 * 编辑提示词页面
 */
const EditPrompt: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  usePageTitle(`编辑提示词 #${id}`);

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
            <h1 className="text-2xl font-bold text-gray-900">编辑提示词</h1>
            <p className="mt-1 text-sm text-gray-500">编辑提示词 #{id}</p>
          </div>
        </div>
        <div className="flex space-x-2">
          <button className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-300 transition-colors">
            预览
          </button>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center">
            <Save className="h-5 w-5 mr-2" />
            保存
          </button>
        </div>
      </div>

      {/* 编辑表单 */}
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
              defaultValue="示例提示词标题"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
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
              defaultValue="这是一个示例提示词的描述"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
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
              defaultValue="你是一个专业的AI助手，请帮助用户解决问题..."
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 font-mono"
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
                defaultValue="general"
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
                defaultValue="AI, 助手, 通用"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditPrompt;