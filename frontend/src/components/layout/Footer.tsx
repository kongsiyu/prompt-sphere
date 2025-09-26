/**
 * Footer 组件
 * 应用底部区域，包含版权信息、链接等
 */

import React from 'react';
import { Heart, ExternalLink } from 'lucide-react';
import { cn } from '@/utils/cn';
import { Button } from '@/components/ui/Button';

export interface FooterProps {
  /** 自定义类名 */
  className?: string;
  /** 是否显示详细信息 */
  showDetails?: boolean;
  /** 版权年份 */
  copyrightYear?: number;
  /** 版权所有者 */
  copyrightOwner?: string;
  /** 版本信息 */
  version?: string;
}

/**
 * Footer 组件
 *
 * @example
 * ```tsx
 * <Footer
 *   showDetails
 *   copyrightYear={2024}
 *   copyrightOwner="AI Team"
 *   version="1.0.0"
 * />
 * ```
 */
export const Footer: React.FC<FooterProps> = ({
  className,
  showDetails = true,
  copyrightYear = new Date().getFullYear(),
  copyrightOwner = 'AI System Prompt Generator',
  version = '1.0.0',
}) => {
  const footerLinks = [
    {
      title: '产品',
      links: [
        { name: '功能特性', href: '/features' },
        { name: '定价', href: '/pricing' },
        { name: '更新日志', href: '/changelog' },
        { name: 'API文档', href: '/api-docs' },
      ],
    },
    {
      title: '支持',
      links: [
        { name: '帮助中心', href: '/help' },
        { name: '联系我们', href: '/contact' },
        { name: '社区', href: '/community' },
        { name: '反馈建议', href: '/feedback' },
      ],
    },
    {
      title: '公司',
      links: [
        { name: '关于我们', href: '/about' },
        { name: '博客', href: '/blog' },
        { name: '招聘', href: '/careers' },
        { name: '媒体资料', href: '/press' },
      ],
    },
    {
      title: '法律',
      links: [
        { name: '隐私政策', href: '/privacy' },
        { name: '服务条款', href: '/terms' },
        { name: 'Cookie政策', href: '/cookies' },
        { name: '许可证', href: '/license' },
      ],
    },
  ];

  if (!showDetails) {
    return (
      <footer className={cn('border-t bg-background', className)}>
        <div className="container mx-auto max-w-screen-2xl px-4 py-6">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            {/* 版权信息 */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>© {copyrightYear} {copyrightOwner}</span>
              <span>•</span>
              <span>v{version}</span>
            </div>

            {/* 制作信息 */}
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <span>用</span>
              <Heart className="h-3 w-3 text-red-500" />
              <span>制作</span>
            </div>
          </div>
        </div>
      </footer>
    );
  }

  return (
    <footer className={cn('border-t bg-background', className)}>
      <div className="container mx-auto max-w-screen-2xl px-4 py-12">
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-5">
          {/* 公司信息 */}
          <div className="lg:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold">
                AI
              </div>
              <span className="text-lg font-semibold">AI System Prompt Generator</span>
            </div>
            <p className="text-sm text-muted-foreground mb-4 max-w-md">
              智能提示词生成器，帮助您快速创建高质量的AI提示词，提升工作效率和创作质量。
            </p>
            <div className="flex gap-2">
              <Button variant="outline" size="icon">
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    fillRule="evenodd"
                    d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="sr-only">Facebook</span>
              </Button>
              <Button variant="outline" size="icon">
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
                </svg>
                <span className="sr-only">Twitter</span>
              </Button>
              <Button variant="outline" size="icon">
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    fillRule="evenodd"
                    d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="sr-only">GitHub</span>
              </Button>
            </div>
          </div>

          {/* 链接组 */}
          {footerLinks.map((group) => (
            <div key={group.title}>
              <h3 className="text-sm font-semibold mb-3">{group.title}</h3>
              <ul className="space-y-2">
                {group.links.map((link) => (
                  <li key={link.name}>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-auto p-0 text-sm text-muted-foreground hover:text-foreground justify-start"
                      rightIcon={
                        link.href.startsWith('http') ? (
                          <ExternalLink className="h-3 w-3" />
                        ) : undefined
                      }
                    >
                      {link.name}
                    </Button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* 底部分割线和版权信息 */}
        <div className="mt-8 border-t pt-6">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            {/* 版权和版本信息 */}
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>© {copyrightYear} {copyrightOwner}</span>
              <span>•</span>
              <span>版本 {version}</span>
              <span>•</span>
              <span>保留所有权利</span>
            </div>

            {/* 制作信息 */}
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <span>用</span>
              <Heart className="h-3 w-3 text-red-500" />
              <span>在中国制作</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};