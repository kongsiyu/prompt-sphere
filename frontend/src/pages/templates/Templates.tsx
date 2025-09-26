import React from 'react';
import { usePageTitle } from '../../hooks/useNavigation';
import { Search, Filter, File, Download } from 'lucide-react';

/**
 * 模板库页面
 */
const Templates: React.FC = () => {
  usePageTitle('模板库');

  const templateCategories = [
    { id: 'all', name: '全部', count: 25 },
    { id: 'coding', name: '编程', count: 8 },
    { id: 'writing', name: '写作', count: 6 },
    { id: 'analysis', name: '分析', count: 5 },
    { id: 'general', name: '通用', count: 6 }
  ];

  const sampleTemplates = [
    {
      id: 1,
      title: '代码审查助手',
      description: '帮助审查代码质量、安全性和最佳实践',
      category: 'coding',
      downloads: 152,
      rating: 4.8
    },
    {
      id: 2,
      title: '文章写作助手',
      description: '协助创作高质量的文章内容',
      category: 'writing',
      downloads: 98,
      rating: 4.6
    },
    {
      id: 3,
      title: '数据分析专家',
      description: '专业的数据分析和洞察生成',
      category: 'analysis',
      downloads: 76,
      rating: 4.9
    }
  ];

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">模板库</h1>
        <p className="mt-1 text-sm text-gray-500">
          从丰富的提示词模板中选择，快速开始您的项目
        </p>
      </div>

      {/* 搜索和过滤 */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder="搜索模板..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
        <button className="flex items-center px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
          <Filter className="h-5 w-5 mr-2" />
          筛选
        </button>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* 侧边栏分类 */}
        <div className="lg:w-64 flex-shrink-0">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <h3 className="font-medium text-gray-900 mb-4">分类</h3>
            <div className="space-y-2">
              {templateCategories.map(category => (
                <button
                  key={category.id}
                  className="w-full flex items-center justify-between px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                >
                  <span>{category.name}</span>
                  <span className="text-gray-500">{category.count}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 模板网格 */}
        <div className="flex-1">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sampleTemplates.map(template => (
              <div
                key={template.id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <File className="h-8 w-8 text-blue-600" />
                  <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full">
                    {templateCategories.find(cat => cat.id === template.category)?.name}
                  </span>
                </div>

                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {template.title}
                </h3>
                <p className="text-gray-600 text-sm mb-4">
                  {template.description}
                </p>

                <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                  <div className="flex items-center">
                    <Download className="h-4 w-4 mr-1" />
                    {template.downloads} 次使用
                  </div>
                  <div className="flex items-center">
                    <span className="text-yellow-400 mr-1">★</span>
                    {template.rating}
                  </div>
                </div>

                <div className="flex space-x-2">
                  <button className="flex-1 bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors">
                    使用模板
                  </button>
                  <button className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium hover:bg-gray-50 transition-colors">
                    预览
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Templates;