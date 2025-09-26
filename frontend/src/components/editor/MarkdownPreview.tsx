/**
 * Markdown 预览组件
 * 基于 react-markdown，支持 GitHub Flavored Markdown 和代码高亮
 */

import React, { forwardRef, useCallback, useEffect, useImperativeHandle, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { cn } from '../../utils/cn';
import { getMarkdownStats, type MarkdownStats } from '../../utils/markdown';

/**
 * 预览主题
 */
export type PreviewTheme = 'light' | 'dark';

/**
 * 预览配置选项
 */
export interface MarkdownPreviewOptions {
  /** 是否启用 GitHub Flavored Markdown，默认 true */
  enableGfm?: boolean;
  /** 是否启用代码高亮，默认 true */
  enableHighlight?: boolean;
  /** 是否显示行号，默认 false */
  showLineNumbers?: boolean;
  /** 主题，默认 'light' */
  theme?: PreviewTheme;
  /** 是否启用任务列表，默认 true */
  enableTaskList?: boolean;
  /** 是否启用表格，默认 true */
  enableTable?: boolean;
  /** 是否启用删除线，默认 true */
  enableStrikethrough?: boolean;
  /** 是否启用链接自动识别，默认 true */
  enableAutoLink?: boolean;
  /** 最大高度（CSS 值） */
  maxHeight?: string;
  /** 最小高度（CSS 值） */
  minHeight?: string;
}

/**
 * 预览属性
 */
export interface MarkdownPreviewProps {
  /** Markdown 内容 */
  content: string;
  /** 焦点变化回调 */
  onFocus?: (focused: boolean) => void;
  /** 滚动回调 */
  onScroll?: (event: Event) => void;
  /** 点击回调 */
  onClick?: (event: React.MouseEvent<HTMLDivElement>) => void;
  /** 链接点击回调 */
  onLinkClick?: (url: string, event: React.MouseEvent<HTMLAnchorElement>) => void;
  /** 图片加载回调 */
  onImageLoad?: (src: string) => void;
  /** 统计信息变化回调 */
  onStatsChange?: (stats: MarkdownStats) => void;
  /** 预览配置选项 */
  options?: MarkdownPreviewOptions;
  /** 自定义样式类名 */
  className?: string;
  /** 内联样式 */
  style?: React.CSSProperties;
}

/**
 * 预览引用接口
 */
export interface MarkdownPreviewRef {
  /** 获取预览容器 */
  getContainer: () => HTMLDivElement | null;
  /** 滚动到指定位置 */
  scrollTo: (top: number) => void;
  /** 滚动到顶部 */
  scrollToTop: () => void;
  /** 滚动到底部 */
  scrollToBottom: () => void;
  /** 获取统计信息 */
  getStats: () => MarkdownStats;
  /** 聚焦预览区域 */
  focus: () => void;
}

/**
 * 默认预览选项
 */
const defaultOptions: Required<MarkdownPreviewOptions> = {
  enableGfm: true,
  enableHighlight: true,
  showLineNumbers: false,
  theme: 'light',
  enableTaskList: true,
  enableTable: true,
  enableStrikethrough: true,
  enableAutoLink: true,
  maxHeight: '600px',
  minHeight: '300px',
};

/**
 * 自定义链接组件
 */
const CustomLink: React.FC<{
  href?: string;
  children: React.ReactNode;
  onLinkClick?: (url: string, event: React.MouseEvent<HTMLAnchorElement>) => void;
}> = ({ href, children, onLinkClick }) => {
  const handleClick = useCallback((event: React.MouseEvent<HTMLAnchorElement>) => {
    if (href && onLinkClick) {
      event.preventDefault();
      onLinkClick(href, event);
    }
  }, [href, onLinkClick]);

  return (
    <a
      href={href}
      onClick={handleClick}
      className={cn(
        'text-blue-600 hover:text-blue-800 underline',
        'dark:text-blue-400 dark:hover:text-blue-300'
      )}
      target={href?.startsWith('http') ? '_blank' : undefined}
      rel={href?.startsWith('http') ? 'noopener noreferrer' : undefined}
    >
      {children}
    </a>
  );
};

/**
 * 自定义图片组件
 */
const CustomImage: React.FC<{
  src?: string;
  alt?: string;
  onImageLoad?: (src: string) => void;
}> = ({ src, alt, onImageLoad }) => {
  const handleLoad = useCallback(() => {
    if (src && onImageLoad) {
      onImageLoad(src);
    }
  }, [src, onImageLoad]);

  return (
    <img
      src={src}
      alt={alt}
      onLoad={handleLoad}
      className={cn(
        'max-w-full h-auto rounded-md shadow-sm',
        'border border-gray-200 dark:border-gray-700'
      )}
      loading="lazy"
    />
  );
};

/**
 * 自定义代码块组件
 */
const CustomCode: React.FC<{
  className?: string;
  children: React.ReactNode;
  showLineNumbers?: boolean;
}> = ({ className, children, showLineNumbers }) => {
  const language = className?.replace('language-', '') || '';

  if (!className) {
    // 内联代码
    return (
      <code className={cn(
        'px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800',
        'text-sm font-mono text-gray-800 dark:text-gray-200'
      )}>
        {children}
      </code>
    );
  }

  // 代码块
  return (
    <div className="relative">
      {language && (
        <div className={cn(
          'absolute top-2 right-2 px-2 py-1 rounded text-xs',
          'bg-gray-700 text-gray-300 font-mono'
        )}>
          {language}
        </div>
      )}
      <pre className={cn(
        'p-4 rounded-md bg-gray-50 dark:bg-gray-900',
        'border border-gray-200 dark:border-gray-700',
        'overflow-x-auto text-sm'
      )}>
        <code className={cn(
          className,
          'font-mono text-gray-800 dark:text-gray-200'
        )}>
          {children}
        </code>
      </pre>
    </div>
  );
};

/**
 * 自定义表格组件
 */
const CustomTable: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="overflow-x-auto my-4">
    <table className={cn(
      'min-w-full border-collapse border border-gray-300 dark:border-gray-600'
    )}>
      {children}
    </table>
  </div>
);

/**
 * 自定义表格头组件
 */
const CustomTableHead: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <thead className="bg-gray-50 dark:bg-gray-800">
    {children}
  </thead>
);

/**
 * 自定义表格单元格组件
 */
const CustomTableCell: React.FC<{
  children: React.ReactNode;
  isHeader?: boolean;
}> = ({ children, isHeader }) => {
  const Component = isHeader ? 'th' : 'td';
  return (
    <Component className={cn(
      'px-4 py-2 border border-gray-300 dark:border-gray-600',
      'text-left text-gray-800 dark:text-gray-200',
      isHeader && 'font-semibold bg-gray-50 dark:bg-gray-800'
    )}>
      {children}
    </Component>
  );
};

/**
 * Markdown 预览组件
 */
export const MarkdownPreview = forwardRef<MarkdownPreviewRef, MarkdownPreviewProps>(
  function MarkdownPreview(props, ref) {
    const {
      content,
      onFocus,
      onScroll,
      onClick,
      onLinkClick,
      onImageLoad,
      onStatsChange,
      options = {},
      className,
      style,
    } = props;

    // 合并选项
    const resolvedOptions = { ...defaultOptions, ...options };

    // 引用
    const containerRef = useRef<HTMLDivElement | null>(null);

    /**
     * 处理焦点
     */
    const handleFocus = useCallback(() => {
      onFocus?.(true);
    }, [onFocus]);

    /**
     * 处理失去焦点
     */
    const handleBlur = useCallback(() => {
      onFocus?.(false);
    }, [onFocus]);

    /**
     * 处理滚动事件
     */
    const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
      onScroll?.(event.nativeEvent);
    }, [onScroll]);

    /**
     * 滚动到指定位置
     */
    const scrollTo = useCallback((top: number) => {
      const container = containerRef.current;
      if (container) {
        container.scrollTop = top;
      }
    }, []);

    /**
     * 滚动到顶部
     */
    const scrollToTop = useCallback(() => {
      scrollTo(0);
    }, [scrollTo]);

    /**
     * 滚动到底部
     */
    const scrollToBottom = useCallback(() => {
      const container = containerRef.current;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }, []);

    /**
     * 获取统计信息
     */
    const getStats = useCallback(() => {
      return getMarkdownStats(content);
    }, [content]);

    /**
     * 聚焦预览区域
     */
    const focus = useCallback(() => {
      containerRef.current?.focus();
    }, []);

    // 暴露方法给外部引用
    useImperativeHandle(ref, () => ({
      getContainer: () => containerRef.current,
      scrollTo,
      scrollToTop,
      scrollToBottom,
      getStats,
      focus,
    }), [scrollTo, scrollToTop, scrollToBottom, getStats, focus]);

    // 监听内容变化，更新统计信息
    useEffect(() => {
      const stats = getMarkdownStats(content);
      onStatsChange?.(stats);
    }, [content, onStatsChange]);

    // 配置 remark 和 rehype 插件
    const remarkPlugins = [];
    const rehypePlugins = [];

    if (resolvedOptions.enableGfm) {
      remarkPlugins.push(remarkGfm);
    }

    if (resolvedOptions.enableHighlight) {
      rehypePlugins.push(rehypeHighlight);
    }

    return (
      <div
        ref={containerRef}
        className={cn(
          'markdown-preview-container',
          'prose prose-sm max-w-none',
          'p-4 overflow-auto',
          'border rounded-md',
          resolvedOptions.theme === 'dark'
            ? 'prose-invert border-gray-600 bg-gray-900'
            : 'border-gray-300 bg-white',
          // 自定义样式
          'prose-headings:font-semibold',
          'prose-headings:text-gray-900 dark:prose-headings:text-gray-100',
          'prose-p:text-gray-700 dark:prose-p:text-gray-300',
          'prose-strong:text-gray-900 dark:prose-strong:text-gray-100',
          'prose-em:text-gray-800 dark:prose-em:text-gray-200',
          'prose-blockquote:border-l-blue-500 dark:prose-blockquote:border-l-blue-400',
          'prose-blockquote:bg-blue-50 dark:prose-blockquote:bg-blue-900/20',
          'prose-blockquote:px-4 prose-blockquote:py-2 prose-blockquote:rounded-r',
          className
        )}
        style={{
          minHeight: resolvedOptions.minHeight,
          maxHeight: resolvedOptions.maxHeight,
          ...style,
        }}
        tabIndex={0}
        onFocus={handleFocus}
        onBlur={handleBlur}
        onScroll={handleScroll}
        onClick={onClick}
        data-color-mode={resolvedOptions.theme}
      >
        {content ? (
          <ReactMarkdown
            remarkPlugins={remarkPlugins}
            rehypePlugins={rehypePlugins}
            components={{
              a: ({ href, children }) => (
                <CustomLink href={href} onLinkClick={onLinkClick}>
                  {children}
                </CustomLink>
              ),
              img: ({ src, alt }) => (
                <CustomImage src={src} alt={alt} onImageLoad={onImageLoad} />
              ),
              code: ({ className, children }) => (
                <CustomCode
                  className={className}
                  showLineNumbers={resolvedOptions.showLineNumbers}
                >
                  {children}
                </CustomCode>
              ),
              table: ({ children }) => (
                <CustomTable>{children}</CustomTable>
              ),
              thead: ({ children }) => (
                <CustomTableHead>{children}</CustomTableHead>
              ),
              th: ({ children }) => (
                <CustomTableCell isHeader>{children}</CustomTableCell>
              ),
              td: ({ children }) => (
                <CustomTableCell>{children}</CustomTableCell>
              ),
            }}
          >
            {content}
          </ReactMarkdown>
        ) : (
          <div className={cn(
            'flex items-center justify-center h-full text-center',
            'text-gray-500 dark:text-gray-400'
          )}>
            <div>
              <div className="text-2xl mb-2">📝</div>
              <p>在左侧编辑器中开始编写 Markdown</p>
              <p className="text-sm mt-1">支持 GitHub Flavored Markdown 语法</p>
            </div>
          </div>
        )}
      </div>
    );
  }
);

export default MarkdownPreview;