/**
 * MarkdownPreview 组件测试
 */

import React, { createRef } from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MarkdownPreview, type MarkdownPreviewRef } from '../MarkdownPreview';

// Mock react-markdown and its plugins
vi.mock('react-markdown', () => {
  return {
    default: ({ children, components }: any) => {
      // Simulate basic markdown rendering
      const content = children || '';

      // Handle different markdown elements for testing
      if (content.includes('# ')) {
        return <div data-testid="markdown-content"><h1>{content.replace('# ', '')}</h1></div>;
      }
      if (content.includes('**') && content.includes('**')) {
        const boldText = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        return <div data-testid="markdown-content" dangerouslySetInnerHTML={{ __html: boldText }} />;
      }
      if (content.includes('[') && content.includes('](')) {
        const linkMatch = content.match(/\[(.*?)\]\((.*?)\)/);
        if (linkMatch) {
          return (
            <div data-testid="markdown-content">
              <a href={linkMatch[2]} onClick={components?.a?.onClick}>
                {linkMatch[1]}
              </a>
            </div>
          );
        }
      }
      if (content.includes('![') && content.includes('](')) {
        const imgMatch = content.match(/!\[(.*?)\]\((.*?)\)/);
        if (imgMatch) {
          return (
            <div data-testid="markdown-content">
              <img src={imgMatch[2]} alt={imgMatch[1]} onLoad={components?.img?.onLoad} />
            </div>
          );
        }
      }
      if (content.includes('```')) {
        return (
          <div data-testid="markdown-content">
            <pre><code>{content.replace(/```[\s\S]*?```/g, 'code block')}</code></pre>
          </div>
        );
      }

      return <div data-testid="markdown-content">{content}</div>;
    }
  };
});

vi.mock('remark-gfm', () => ({
  default: () => {},
}));

vi.mock('rehype-highlight', () => ({
  default: () => {},
}));

describe('MarkdownPreview', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('basic rendering', () => {
    it('should render with empty content', () => {
      render(<MarkdownPreview content="" />);

      expect(screen.getByText('在左侧编辑器中开始编写 Markdown')).toBeInTheDocument();
      expect(screen.getByText('支持 GitHub Flavored Markdown 语法')).toBeInTheDocument();
      expect(screen.getByText('📝')).toBeInTheDocument();
    });

    it('should render markdown content', () => {
      render(<MarkdownPreview content="# Hello World" />);

      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Hello World');
    });

    it('should apply custom className', () => {
      render(<MarkdownPreview content="test" className="custom-class" />);

      const container = screen.getByTestId('markdown-content').closest('.markdown-preview-container');
      expect(container).toHaveClass('custom-class');
    });

    it('should apply custom styles', () => {
      const customStyles = { backgroundColor: 'blue' };
      render(<MarkdownPreview content="test" style={customStyles} />);

      const container = screen.getByTestId('markdown-content').closest('.markdown-preview-container');
      expect(container).toHaveStyle('background-color: blue');
    });
  });

  describe('theme support', () => {
    it('should apply light theme classes by default', () => {
      render(<MarkdownPreview content="test" />);

      const container = screen.getByTestId('markdown-content').closest('.markdown-preview-container');
      expect(container).toHaveClass('border-gray-300', 'bg-white');
      expect(container).not.toHaveClass('prose-invert', 'border-gray-600', 'bg-gray-900');
    });

    it('should apply dark theme classes when specified', () => {
      render(<MarkdownPreview content="test" options={{ theme: 'dark' }} />);

      const container = screen.getByTestId('markdown-content').closest('.markdown-preview-container');
      expect(container).toHaveClass('prose-invert', 'border-gray-600', 'bg-gray-900');
      expect(container).toHaveAttribute('data-color-mode', 'dark');
    });
  });

  describe('user interactions', () => {
    it('should handle focus events', async () => {
      const onFocus = vi.fn();
      render(<MarkdownPreview content="test" onFocus={onFocus} />);

      const container = screen.getByTestId('markdown-content').closest('.markdown-preview-container');
      await user.click(container!);

      expect(onFocus).toHaveBeenCalledWith(true);
    });

    it('should handle blur events', async () => {
      const onFocus = vi.fn();
      render(<MarkdownPreview content="test" onFocus={onFocus} />);

      const container = screen.getByTestId('markdown-content').closest('.markdown-preview-container');
      await user.click(container!);
      await user.tab(); // Tab away to blur

      expect(onFocus).toHaveBeenCalledWith(false);
    });

    it('should handle scroll events', () => {
      const onScroll = vi.fn();
      render(<MarkdownPreview content="test" onScroll={onScroll} />);

      const container = screen.getByTestId('markdown-content').closest('.markdown-preview-container');
      fireEvent.scroll(container!);

      expect(onScroll).toHaveBeenCalled();
    });

    it('should handle click events', () => {
      const onClick = vi.fn();
      render(<MarkdownPreview content="test" onClick={onClick} />);

      const container = screen.getByTestId('markdown-content').closest('.markdown-preview-container');
      fireEvent.click(container!);

      expect(onClick).toHaveBeenCalled();
    });
  });

  describe('markdown rendering', () => {
    it('should render headings correctly', () => {
      render(<MarkdownPreview content="# Main Title" />);

      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Main Title');
    });

    it('should render bold text correctly', () => {
      render(<MarkdownPreview content="This is **bold** text" />);

      const content = screen.getByTestId('markdown-content');
      expect(content.innerHTML).toContain('<strong>bold</strong>');
    });

    it('should render links correctly', () => {
      const onLinkClick = vi.fn();
      render(<MarkdownPreview content="[Link text](http://example.com)" onLinkClick={onLinkClick} />);

      const link = screen.getByRole('link');
      expect(link).toHaveTextContent('Link text');
      expect(link).toHaveAttribute('href', 'http://example.com');
    });

    it('should render images correctly', () => {
      const onImageLoad = vi.fn();
      render(<MarkdownPreview content="![Alt text](image.jpg)" onImageLoad={onImageLoad} />);

      const image = screen.getByRole('img');
      expect(image).toHaveAttribute('src', 'image.jpg');
      expect(image).toHaveAttribute('alt', 'Alt text');
    });

    it('should render code blocks correctly', () => {
      render(<MarkdownPreview content="```javascript\nconst x = 1;\n```" />);

      const codeBlock = screen.getByText('code block');
      expect(codeBlock).toBeInTheDocument();
    });
  });

  describe('link interactions', () => {
    it('should call onLinkClick when link is clicked', async () => {
      const onLinkClick = vi.fn();
      render(<MarkdownPreview content="[Test Link](http://example.com)" onLinkClick={onLinkClick} />);

      const link = screen.getByRole('link');
      await user.click(link);

      expect(onLinkClick).toHaveBeenCalledWith('http://example.com', expect.any(Object));
    });

    it('should open external links in new tab by default', () => {
      render(<MarkdownPreview content="[External](http://example.com)" />);

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('should not open internal links in new tab', () => {
      render(<MarkdownPreview content="[Internal](/internal)" />);

      const link = screen.getByRole('link');
      expect(link).not.toHaveAttribute('target');
      expect(link).not.toHaveAttribute('rel');
    });
  });

  describe('image interactions', () => {
    it('should call onImageLoad when image loads', () => {
      const onImageLoad = vi.fn();
      render(<MarkdownPreview content="![Test](image.jpg)" onImageLoad={onImageLoad} />);

      const image = screen.getByRole('img');
      fireEvent.load(image);

      expect(onImageLoad).toHaveBeenCalledWith('image.jpg');
    });
  });

  describe('statistics tracking', () => {
    it('should call onStatsChange when content changes', () => {
      const onStatsChange = vi.fn();
      const { rerender } = render(
        <MarkdownPreview content="Initial content" onStatsChange={onStatsChange} />
      );

      expect(onStatsChange).toHaveBeenCalled();

      rerender(<MarkdownPreview content="New content" onStatsChange={onStatsChange} />);

      expect(onStatsChange).toHaveBeenCalledTimes(2);
    });
  });

  describe('ref methods', () => {
    it('should expose container element through ref', () => {
      const ref = createRef<MarkdownPreviewRef>();
      render(<MarkdownPreview ref={ref} content="Test content" />);

      expect(ref.current?.getContainer()).toBeInstanceOf(HTMLElement);
    });

    it('should scroll to position through ref', () => {
      const ref = createRef<MarkdownPreviewRef>();
      render(<MarkdownPreview ref={ref} content="Test content" />);

      const container = ref.current?.getContainer();
      if (container) {
        Object.defineProperty(container, 'scrollTop', {
          value: 0,
          writable: true,
          configurable: true
        });

        ref.current?.scrollTo(100);
        expect(container.scrollTop).toBe(100);
      }
    });

    it('should scroll to top through ref', () => {
      const ref = createRef<MarkdownPreviewRef>();
      render(<MarkdownPreview ref={ref} content="Test content" />);

      const container = ref.current?.getContainer();
      if (container) {
        Object.defineProperty(container, 'scrollTop', {
          value: 200,
          writable: true,
          configurable: true
        });

        ref.current?.scrollToTop();
        expect(container.scrollTop).toBe(0);
      }
    });

    it('should scroll to bottom through ref', () => {
      const ref = createRef<MarkdownPreviewRef>();
      render(<MarkdownPreview ref={ref} content="Test content" />);

      const container = ref.current?.getContainer();
      if (container) {
        Object.defineProperty(container, 'scrollTop', {
          value: 0,
          writable: true,
          configurable: true
        });
        Object.defineProperty(container, 'scrollHeight', {
          value: 1000,
          writable: false,
          configurable: true
        });

        ref.current?.scrollToBottom();
        expect(container.scrollTop).toBe(1000);
      }
    });

    it('should get stats through ref', () => {
      const ref = createRef<MarkdownPreviewRef>();
      render(<MarkdownPreview ref={ref} content="# Title\nContent with **bold** text." />);

      const stats = ref.current?.getStats();
      expect(stats).toHaveProperty('characters');
      expect(stats).toHaveProperty('words');
      expect(stats).toHaveProperty('headings');
      expect(stats?.headings).toBe(1);
    });

    it('should focus preview through ref', () => {
      const ref = createRef<MarkdownPreviewRef>();
      render(<MarkdownPreview ref={ref} content="Test content" />);

      const container = ref.current?.getContainer();
      const focusSpy = vi.spyOn(container!, 'focus');

      ref.current?.focus();

      expect(focusSpy).toHaveBeenCalled();
    });
  });

  describe('configuration options', () => {
    it('should apply height constraints', () => {
      render(
        <MarkdownPreview
          content="test"
          options={{ minHeight: '200px', maxHeight: '800px' }}
        />
      );

      const container = screen.getByTestId('markdown-content').closest('.markdown-preview-container');
      expect(container).toHaveStyle({
        'min-height': '200px',
        'max-height': '800px'
      });
    });

    it('should handle disabled GFM', () => {
      render(<MarkdownPreview content="test" options={{ enableGfm: false }} />);

      // Component should render without errors
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });

    it('should handle disabled syntax highlighting', () => {
      render(<MarkdownPreview content="```js\ncode\n```" options={{ enableHighlight: false }} />);

      // Component should render without errors
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('should be focusable', () => {
      render(<MarkdownPreview content="test" />);

      const container = screen.getByTestId('markdown-content').closest('.markdown-preview-container');
      expect(container).toHaveAttribute('tabindex', '0');
    });

    it('should have proper semantic structure', () => {
      render(<MarkdownPreview content="# Heading\nParagraph text" />);

      const container = screen.getByTestId('markdown-content').closest('.markdown-preview-container');
      expect(container).toHaveClass('prose');
    });

    it('should handle keyboard navigation', async () => {
      const onFocus = vi.fn();
      render(<MarkdownPreview content="test" onFocus={onFocus} />);

      await user.tab(); // Tab to focus the preview

      expect(onFocus).toHaveBeenCalledWith(true);
    });
  });

  describe('error handling', () => {
    it('should handle malformed markdown gracefully', () => {
      const malformedMarkdown = '[unclosed link';

      expect(() => {
        render(<MarkdownPreview content={malformedMarkdown} />);
      }).not.toThrow();

      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });

    it('should handle empty image src gracefully', () => {
      render(<MarkdownPreview content="![alt text]()" />);

      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });

    it('should handle missing link href gracefully', () => {
      render(<MarkdownPreview content="[link text]()" />);

      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });
  });

  describe('performance considerations', () => {
    it('should handle large content efficiently', () => {
      const largeContent = '# Large Content\n' + 'Line of text\n'.repeat(1000);

      const startTime = performance.now();
      render(<MarkdownPreview content={largeContent} />);
      const endTime = performance.now();

      // Should render within reasonable time (adjust threshold as needed)
      expect(endTime - startTime).toBeLessThan(1000);
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });

    it('should handle frequent content updates', () => {
      const onStatsChange = vi.fn();
      const { rerender } = render(
        <MarkdownPreview content="Initial" onStatsChange={onStatsChange} />
      );

      // Simulate rapid content changes
      for (let i = 0; i < 10; i++) {
        rerender(<MarkdownPreview content={`Content ${i}`} onStatsChange={onStatsChange} />);
      }

      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
      expect(onStatsChange).toHaveBeenCalled();
    });
  });

  describe('custom components', () => {
    it('should render tables with custom styling', () => {
      const tableMarkdown = `
| Column 1 | Column 2 |
|----------|----------|
| Cell 1   | Cell 2   |
      `;

      render(<MarkdownPreview content={tableMarkdown} />);

      // Should render without errors (specific table testing would need more complex mocking)
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });

    it('should handle task lists', () => {
      const taskListMarkdown = `
- [x] Completed task
- [ ] Incomplete task
      `;

      render(<MarkdownPreview content={taskListMarkdown} />);

      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });
  });
});