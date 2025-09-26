import React from 'react';
import { Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/useNavigation';
import {
  MessageSquare,
  File,
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
      icon: <File className="h-8 w-8 text-green-600" />,
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
    { label: '提示词模板', value: '100+', icon: <File className="h-5 w-5" /> },
    { label: '用户数量', value: '1000+', icon: <Users className="h-5 w-5" /> },
    { label: '生成次数', value: '10K+', icon: <TrendingUp className="h-5 w-5" /> }
  ];

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="bg-white rounded-xl p-12 text-center shadow-sm border border-gray-200">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          AI System Prompt Generator
        </h1>
        <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
          智能系统提示词生成器，让AI更懂你的需求
        </p>

        {isAuthenticated ? (
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/prompt-editor/create"
              className="bg-blue-600 text-white px-8 py-4 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center shadow-md"
            >
              <Plus className="h-5 w-5 mr-2" />
              创建提示词
            </Link>
            <Link
              to="/prompts"
              className="bg-white text-blue-600 border-2 border-blue-600 px-8 py-4 rounded-lg font-medium hover:bg-blue-50 transition-colors shadow-md"
            >
              管理提示词
            </Link>
          </div>
        ) : (
          <div className="flex justify-center">
            <Link
              to="/auth/login"
              className="bg-blue-600 text-white px-10 py-4 rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-md"
            >
              立即开始
            </Link>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-gray-900 mb-1">{stat.value}</p>
                <p className="text-sm text-gray-600">{stat.label}</p>
              </div>
              <div className="text-blue-600 bg-blue-50 p-3 rounded-lg">
                {stat.icon}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Features Section */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900 text-center mb-10">
          核心功能
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 hover:border-gray-300"
            >
              <div className="mb-6 inline-flex p-3 bg-gray-50 rounded-lg">
                {feature.icon}
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">
                {feature.title}
              </h3>
              <p className="text-gray-600 mb-6 line-height-relaxed">
                {feature.description}
              </p>
              {isAuthenticated ? (
                <Link
                  to={feature.link}
                  className="text-blue-600 hover:text-blue-700 font-medium inline-flex items-center"
                >
                  了解更多
                  <span className="ml-1">→</span>
                </Link>
              ) : (
                <Link
                  to="/auth/login"
                  className="text-blue-600 hover:text-blue-700 font-medium inline-flex items-center"
                >
                  登录使用
                  <span className="ml-1">→</span>
                </Link>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity Section - 仅认证用户可见 */}
      {isAuthenticated && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold text-gray-900">
              最近活动
            </h2>
            <Link
              to="/prompts"
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              查看全部
            </Link>
          </div>
          <div className="text-center py-12 text-gray-500">
            <div className="inline-flex p-4 bg-gray-50 rounded-full mb-4">
              <MessageSquare className="h-8 w-8 text-gray-400" />
            </div>
            <p className="text-lg mb-3">暂无最近活动</p>
            <Link
              to="/prompt-editor/create"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
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