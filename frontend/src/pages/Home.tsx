import React from 'react';
import { Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/useNavigation';
import {
  MessageSquare,
  FileTemplate,
  Settings,
  Plus,
  TrendingUp,
  Users,
  Zap
} from 'lucide-react';

/**
 * 首页组件
 */
const Home: React.FC = () => {
  usePageTitle('首页');

  const isAuthenticated = !!localStorage.getItem('authToken');

  const features = [
    {
      icon: <MessageSquare className="h-8 w-8 text-blue-600" />,
      title: '智能提示词生成',
      description: '使用AI技术生成高质量的系统提示词，提高工作效率',
      link: '/prompts'
    },
    {
      icon: <FileTemplate className="h-8 w-8 text-green-600" />,
      title: '模板库',
      description: '丰富的提示词模板，涵盖各种应用场景',
      link: '/templates'
    },
    {
      icon: <Zap className="h-8 w-8 text-yellow-600" />,
      title: '快速创建',
      description: '简单易用的界面，快速创建和编辑提示词',
      link: '/prompts/create'
    }
  ];

  const stats = [
    { label: '提示词模板', value: '100+', icon: <FileTemplate className="h-5 w-5" /> },
    { label: '用户数量', value: '1000+', icon: <Users className="h-5 w-5" /> },
    { label: '生成次数', value: '10K+', icon: <TrendingUp className="h-5 w-5" /> }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-100 rounded-xl p-8 mb-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            AI System Prompt Generator
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            智能系统提示词生成器，让AI更懂你的需求
          </p>

          {isAuthenticated ? (
            <div className="flex flex-wrap justify-center gap-4">
              <Link
                to="/prompts/create"
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center"
              >
                <Plus className="h-5 w-5 mr-2" />
                创建提示词
              </Link>
              <Link
                to="/prompts"
                className="bg-white text-blue-600 border border-blue-600 px-6 py-3 rounded-lg font-medium hover:bg-blue-50 transition-colors"
              >
                管理提示词
              </Link>
            </div>
          ) : (
            <div className="flex flex-wrap justify-center gap-4">
              <Link
                to="/auth/login"
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                立即开始
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Stats Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                <p className="text-sm text-gray-600">{stat.label}</p>
              </div>
              <div className="text-blue-600">
                {stat.icon}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Features Section */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
          核心功能
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="mb-4">
                {feature.icon}
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600 mb-4">
                {feature.description}
              </p>
              {isAuthenticated ? (
                <Link
                  to={feature.link}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                >
                  了解更多 →
                </Link>
              ) : (
                <Link
                  to="/auth/login"
                  className="text-blue-600 hover:text-blue-700 font-medium"
                >
                  登录使用 →
                </Link>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity Section - 仅认证用户可见 */}
      {isAuthenticated && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              最近活动
            </h2>
            <Link
              to="/prompts"
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              查看全部
            </Link>
          </div>
          <div className="text-center py-8 text-gray-500">
            <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>暂无最近活动</p>
            <Link
              to="/prompts/create"
              className="text-blue-600 hover:text-blue-700 font-medium mt-2 inline-block"
            >
              创建第一个提示词
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default Home;