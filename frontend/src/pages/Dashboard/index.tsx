/**
 * Dashboard 页面
 * 首页仪表盘，提供应用概览和快速操作
 */

import React from 'react';
import { Link } from 'react-router-dom';
import {
  Plus,
  MessageSquare,
  File,
  TrendingUp,
  Clock,
  Star,
  Settings,
  Users,
  BarChart3,
  Zap,
  BookOpen,
  Edit3
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { cn } from '@/utils/cn';

/**
 * 统计卡片数据类型
 */
interface StatCard {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
}

/**
 * 快速操作项数据类型
 */
interface QuickAction {
  title: string;
  description: string;
  icon: React.ReactNode;
  href: string;
  variant: 'primary' | 'secondary' | 'outline';
}

/**
 * Dashboard 页面组件
 */
const Dashboard: React.FC = () => {
  const isAuthenticated = !!localStorage.getItem('authToken');

  // 统计数据卡片
  const statsCards: StatCard[] = [
    {
      title: '我的提示词',
      value: '12',
      change: '+3 本月',
      changeType: 'positive',
      icon: <MessageSquare className="h-5 w-5" />
    },
    {
      title: '使用的模板',
      value: '8',
      change: '+2 本周',
      changeType: 'positive',
      icon: <File className="h-5 w-5" />
    },
    {
      title: '总使用次数',
      value: '156',
      change: '+28 本周',
      changeType: 'positive',
      icon: <TrendingUp className="h-5 w-5" />
    },
    {
      title: '活跃天数',
      value: '24',
      change: '连续 7 天',
      changeType: 'neutral',
      icon: <BarChart3 className="h-5 w-5" />
    }
  ];

  // 快速操作项
  const quickActions: QuickAction[] = [
    {
      title: '创建新提示词',
      description: '从零开始创建一个新的AI提示词',
      icon: <Plus className="h-5 w-5" />,
      href: '/prompt-editor/create',
      variant: 'primary'
    },
    {
      title: '浏览模板库',
      description: '从丰富的模板库中选择合适的模板',
      icon: <BookOpen className="h-5 w-5" />,
      href: '/templates',
      variant: 'secondary'
    },
    {
      title: '管理提示词',
      description: '查看和管理你的所有提示词',
      icon: <Edit3 className="h-5 w-5" />,
      href: '/prompts',
      variant: 'outline'
    }
  ];

  // 最近活动数据（模拟）
  const recentActivities = [
    {
      id: '1',
      type: 'create',
      title: '创建了新提示词',
      name: '技术文档写作助手',
      time: '2小时前',
      icon: <Plus className="h-4 w-4 text-green-500" />
    },
    {
      id: '2',
      type: 'edit',
      title: '编辑了提示词',
      name: '代码审查助手',
      time: '1天前',
      icon: <Edit3 className="h-4 w-4 text-blue-500" />
    },
    {
      id: '3',
      type: 'use',
      title: '使用了模板',
      name: '营销文案模板',
      time: '2天前',
      icon: <File className="h-4 w-4 text-purple-500" />
    }
  ];

  // 推荐模板数据（模拟）
  const recommendedTemplates = [
    {
      id: '1',
      title: '代码生成助手',
      description: '帮助生成各种编程语言的代码片段',
      category: '开发工具',
      rating: 4.8,
      uses: 1200
    },
    {
      id: '2',
      title: '文章写作助手',
      description: '协助撰写高质量的技术和营销文章',
      category: '内容创作',
      rating: 4.9,
      uses: 980
    },
    {
      id: '3',
      title: '数据分析师',
      description: '专业的数据分析和洞察提供者',
      category: '数据分析',
      rating: 4.7,
      uses: 756
    }
  ];

  if (!isAuthenticated) {
    return (
      <div className="space-y-8">
        {/* 欢迎区域 */}
        <div className="text-center py-12">
          <div className="max-w-3xl mx-auto">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              欢迎使用 AI System Prompt Generator
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              智能系统提示词生成器，让AI更懂你的需求
            </p>
            <div className="flex justify-center gap-4">
              <Button size="lg" variant="primary" className="px-8">
                <Link to="/auth/login" className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  立即开始
                </Link>
              </Button>
              <Button size="lg" variant="outline" className="px-8">
                <BookOpen className="h-5 w-5" />
                了解更多
              </Button>
            </div>
          </div>
        </div>

        {/* 功能特性 */}
        <div className="grid md:grid-cols-3 gap-6">
          <Card className="p-6 hover:shadow-md transition-shadow">
            <div className="text-center space-y-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto">
                <Zap className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">智能生成</h3>
              <p className="text-gray-600">
                使用先进的AI技术，快速生成高质量的系统提示词
              </p>
            </div>
          </Card>

          <Card className="p-6 hover:shadow-md transition-shadow">
            <div className="text-center space-y-4">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto">
                <File className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">丰富模板</h3>
              <p className="text-gray-600">
                提供覆盖各种场景的模板库，满足不同需求
              </p>
            </div>
          </Card>

          <Card className="p-6 hover:shadow-md transition-shadow">
            <div className="text-center space-y-4">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto">
                <Settings className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">易于管理</h3>
              <p className="text-gray-600">
                简洁直观的界面，让提示词管理变得轻松简单
              </p>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* 欢迎信息 */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-6 text-white">
        <div className="max-w-4xl">
          <h1 className="text-2xl md:text-3xl font-bold mb-2">
            欢迎回来! 👋
          </h1>
          <p className="text-blue-100 mb-4">
            今天是个创作的好日子，准备好创建新的AI提示词了吗？
          </p>
          <Button
            variant="outline"
            className="bg-white/10 border-white/20 text-white hover:bg-white/20"
          >
            <Plus className="h-4 w-4 mr-2" />
            创建新提示词
          </Button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statsCards.map((stat, index) => (
          <Card key={index} className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">{stat.title}</p>
                <p className="text-2xl font-bold text-gray-900 mb-1">{stat.value}</p>
                <p className={cn(
                  "text-xs",
                  stat.changeType === 'positive' && "text-green-600",
                  stat.changeType === 'negative' && "text-red-600",
                  stat.changeType === 'neutral' && "text-gray-500"
                )}>
                  {stat.change}
                </p>
              </div>
              <div className="p-3 bg-blue-50 rounded-lg">
                {stat.icon}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* 快速操作 */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          快速操作
        </h2>
        <div className="grid md:grid-cols-3 gap-4">
          {quickActions.map((action, index) => (
            <Link
              key={index}
              to={action.href}
              className="block p-4 border rounded-lg hover:shadow-md transition-all hover:border-blue-200 group"
            >
              <div className="flex items-start gap-3">
                <div className="p-2 bg-blue-50 rounded-lg group-hover:bg-blue-100 transition-colors">
                  {action.icon}
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 mb-1">{action.title}</h3>
                  <p className="text-sm text-gray-600">{action.description}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* 最近活动 */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              最近活动
            </h2>
            <Button variant="ghost" size="sm">
              <Clock className="h-4 w-4 mr-1" />
              查看全部
            </Button>
          </div>
          <div className="space-y-4">
            {recentActivities.length > 0 ? (
              recentActivities.map((activity) => (
                <div key={activity.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <div className="flex-shrink-0">
                    {activity.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900">
                      {activity.title}
                    </p>
                    <p className="text-sm text-gray-600 truncate">
                      {activity.name}
                    </p>
                  </div>
                  <div className="flex-shrink-0">
                    <p className="text-xs text-gray-500">{activity.time}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>暂无最近活动</p>
              </div>
            )}
          </div>
        </Card>

        {/* 推荐模板 */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              推荐模板
            </h2>
            <Button variant="ghost" size="sm">
              <Star className="h-4 w-4 mr-1" />
              浏览全部
            </Button>
          </div>
          <div className="space-y-4">
            {recommendedTemplates.map((template) => (
              <div key={template.id} className="p-3 border rounded-lg hover:shadow-sm transition-shadow cursor-pointer">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium text-gray-900">{template.title}</h3>
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                    {template.rating}
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-2">{template.description}</p>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span className="bg-gray-100 px-2 py-1 rounded">{template.category}</span>
                  <span>{template.uses} 次使用</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;