import React from 'react';
import { usePageTitle } from '../../hooks/useNavigation';
import { User, Bell, Lock, Palette, Globe } from 'lucide-react';

/**
 * 用户设置页面
 */
const Settings: React.FC = () => {
  usePageTitle('用户设置');

  const settingSections = [
    {
      icon: <User className="h-5 w-5" />,
      title: '个人信息',
      description: '管理您的个人资料和账户信息'
    },
    {
      icon: <Bell className="h-5 w-5" />,
      title: '通知设置',
      description: '控制您接收的通知类型和频率'
    },
    {
      icon: <Lock className="h-5 w-5" />,
      title: '安全与隐私',
      description: '管理密码、两步验证和隐私设置'
    },
    {
      icon: <Palette className="h-5 w-5" />,
      title: '界面偏好',
      description: '自定义界面主题和布局设置'
    },
    {
      icon: <Globe className="h-5 w-5" />,
      title: '语言与地区',
      description: '设置您的语言和地区偏好'
    }
  ];

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">用户设置</h1>
        <p className="mt-1 text-sm text-gray-500">
          管理您的账户设置和个人偏好
        </p>
      </div>

      {/* 设置网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {settingSections.map((section, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 p-2 bg-blue-100 rounded-lg text-blue-600">
                {section.icon}
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {section.title}
                </h3>
                <p className="text-sm text-gray-600">
                  {section.description}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 账户操作 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">账户操作</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between py-3 border-b border-gray-200">
            <div>
              <h3 className="text-sm font-medium text-gray-900">导出数据</h3>
              <p className="text-sm text-gray-500">下载您的所有数据副本</p>
            </div>
            <button className="text-blue-600 hover:text-blue-700 font-medium">
              导出
            </button>
          </div>

          <div className="flex items-center justify-between py-3 border-b border-gray-200">
            <div>
              <h3 className="text-sm font-medium text-gray-900">账户暂停</h3>
              <p className="text-sm text-gray-500">临时停用您的账户</p>
            </div>
            <button className="text-yellow-600 hover:text-yellow-700 font-medium">
              暂停
            </button>
          </div>

          <div className="flex items-center justify-between py-3">
            <div>
              <h3 className="text-sm font-medium text-gray-900">删除账户</h3>
              <p className="text-sm text-gray-500">永久删除您的账户和所有数据</p>
            </div>
            <button className="text-red-600 hover:text-red-700 font-medium">
              删除
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;