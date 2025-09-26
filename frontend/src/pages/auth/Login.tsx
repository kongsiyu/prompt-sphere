import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { usePageTitle } from '../../hooks/useNavigation';
import { Eye, EyeOff, LogIn } from 'lucide-react';

/**
 * 登录页面组件
 */
const Login: React.FC = () => {
  usePageTitle('登录');

  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // 清除错误信息
    if (error) setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // 简化的登录逻辑 - 实际应该调用API
      if (formData.email && formData.password) {
        // 模拟API调用延迟
        await new Promise(resolve => setTimeout(resolve, 1000));

        // 简单的演示登录逻辑
        if (formData.email === 'demo@example.com' && formData.password === 'password') {
          // 设置认证token
          localStorage.setItem('authToken', 'demo-token');
          localStorage.setItem('userRoles', JSON.stringify(['user']));

          // 检查是否有重定向路径
          const urlParams = new URLSearchParams(window.location.search);
          const redirectPath = urlParams.get('redirect') || '/';

          navigate(redirectPath);
        } else {
          setError('邮箱或密码错误');
        }
      } else {
        setError('请填写所有必填字段');
      }
    } catch (err) {
      setError('登录失败，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900">
          登录您的账户
        </h2>
        <p className="mt-2 text-sm text-gray-600">
          请输入您的凭据以访问您的账户
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 错误信息 */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
            {error}
          </div>
        )}

        {/* 演示账户信息 */}
        <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded-md text-sm">
          <p className="font-medium">演示账户：</p>
          <p>邮箱: demo@example.com</p>
          <p>密码: password</p>
        </div>

        {/* 邮箱输入 */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            邮箱地址
          </label>
          <div className="mt-1">
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={formData.email}
              onChange={handleInputChange}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="请输入您的邮箱"
            />
          </div>
        </div>

        {/* 密码输入 */}
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            密码
          </label>
          <div className="mt-1 relative">
            <input
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              required
              value={formData.password}
              onChange={handleInputChange}
              className="block w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="请输入您的密码"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
            >
              {showPassword ? (
                <EyeOff className="h-5 w-5" />
              ) : (
                <Eye className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>

        {/* 记住密码和忘记密码 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <input
              id="remember-me"
              name="remember-me"
              type="checkbox"
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
              记住我
            </label>
          </div>

          <div className="text-sm">
            <button type="button" className="font-medium text-blue-600 hover:text-blue-500">
              忘记密码？
            </button>
          </div>
        </div>

        {/* 登录按钮 */}
        <div>
          <button
            type="submit"
            disabled={isLoading}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <LogIn className="h-5 w-5 mr-2" />
                登录
              </>
            )}
          </button>
        </div>
      </form>

      {/* 底部链接 */}
      <div className="mt-6 text-center">
        <p className="text-sm text-gray-600">
          还没有账户？{' '}
          <button className="font-medium text-blue-600 hover:text-blue-500">
            立即注册
          </button>
        </p>
      </div>

      {/* 返回首页链接 */}
      <div className="mt-4 text-center">
        <Link
          to="/"
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          ← 返回首页
        </Link>
      </div>
    </div>
  );
};

export default Login;