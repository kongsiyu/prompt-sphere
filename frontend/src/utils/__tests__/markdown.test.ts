/**
 * Markdown 工具函数测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  formatMarkdown,
  normalizeMarkdownIndentation,
  getMarkdownStats,
  insertMarkdownFormat,
  getCurrentLineInfo,
  autoCompleteListItem,
  isMarkdownEmpty,
  debounce,
  throttle,
} from '../markdown';

describe('markdown utils', () => {
  describe('formatMarkdown', () => {
    it('should format basic markdown correctly', () => {
      const input = '# Title\n\n\n\nSome content\n\n\n';
      const expected = '# Title\n\nSome content\n';
      expect(formatMarkdown(input)).toBe(expected);
    });

    it('should remove extra newlines when option is enabled', () => {
      const input = 'Line 1\n\n\n\nLine 2\n\n\n\nLine 3';
      const expected = 'Line 1\n\nLine 2\n\nLine 3\n';
      expect(formatMarkdown(input, { removeExtraNewlines: true })).toBe(expected);
    });

    it('should preserve extra newlines when option is disabled', () => {
      const input = 'Line 1\n\n\n\nLine 2';
      const expected = 'Line 1\n\n\n\nLine 2\n';
      expect(formatMarkdown(input, { removeExtraNewlines: false })).toBe(expected);
    });

    it('should normalize indentation when option is enabled', () => {
      const input = '- Item 1\n    - Subitem\n        - Sub-subitem';
      const result = formatMarkdown(input, { normalizeIndentation: true, indentSize: 2 });
      expect(result).toContain('  - Subitem');
    });

    it('should add newline at end if missing', () => {
      const input = 'Content without newline';
      const result = formatMarkdown(input);
      expect(result).toBe('Content without newline\n');
    });

    it('should handle empty content', () => {
      expect(formatMarkdown('')).toBe('');
      expect(formatMarkdown('   ')).toBe('   \n');
    });
  });

  describe('normalizeMarkdownIndentation', () => {
    it('should normalize unordered list indentation', () => {
      const input = '- Item 1\n    - Subitem\n        - Sub-subitem';
      const expected = '- Item 1\n  - Subitem\n    - Sub-subitem';
      expect(normalizeMarkdownIndentation(input, 2)).toBe(expected);
    });

    it('should normalize ordered list indentation', () => {
      const input = '1. Item 1\n    2. Subitem\n        3. Sub-subitem';
      const expected = '1. Item 1\n  2. Subitem\n    3. Sub-subitem';
      expect(normalizeMarkdownIndentation(input, 2)).toBe(expected);
    });

    it('should preserve code block indentation', () => {
      const input = '```javascript\n    const x = 1;\n```';
      const expected = '```javascript\n    const x = 1;\n```';
      expect(normalizeMarkdownIndentation(input, 2)).toBe(expected);
    });

    it('should handle mixed content correctly', () => {
      const input = '- List item\n```\ncode block\n```\n    - Indented item';
      const result = normalizeMarkdownIndentation(input, 2);
      expect(result).toContain('- List item');
      expect(result).toContain('```\ncode block\n```');
      expect(result).toContain('  - Indented item');
    });
  });

  describe('getMarkdownStats', () => {
    it('should calculate basic stats correctly', () => {
      const content = '# Title\n\nSome content with **bold** text.\n\n- List item\n- Another item';
      const stats = getMarkdownStats(content);

      expect(stats.characters).toBeGreaterThan(0);
      expect(stats.words).toBeGreaterThan(0);
      expect(stats.lines).toBe(6);
      expect(stats.paragraphs).toBe(3);
      expect(stats.headings).toBe(1);
    });

    it('should count Chinese characters correctly', () => {
      const content = '这是中文内容 with English words';
      const stats = getMarkdownStats(content);

      expect(stats.words).toBe(8); // 6 Chinese characters + 2 English words
      expect(stats.characters).toBeGreaterThan(0);
    });

    it('should count code blocks', () => {
      const content = '```javascript\nconst x = 1;\n```\n\nInline `code` here.';
      const stats = getMarkdownStats(content);

      expect(stats.codeBlocks).toBe(1);
    });

    it('should count links and images', () => {
      const content = '[Link](http://example.com)\n![Image](image.jpg)';
      const stats = getMarkdownStats(content);

      expect(stats.links).toBe(1);
      expect(stats.images).toBe(1);
    });

    it('should handle empty content', () => {
      const stats = getMarkdownStats('');

      expect(stats.characters).toBe(0);
      expect(stats.words).toBe(0);
      expect(stats.lines).toBe(1);
      expect(stats.paragraphs).toBe(0);
      expect(stats.headings).toBe(0);
      expect(stats.codeBlocks).toBe(0);
      expect(stats.links).toBe(0);
      expect(stats.images).toBe(0);
    });
  });

  describe('insertMarkdownFormat', () => {
    it('should insert bold format correctly', () => {
      const result = insertMarkdownFormat('Hello world', { start: 6, end: 11 }, 'bold');
      expect(result.content).toBe('Hello **world**');
      expect(result.cursorPosition).toBe(15);
    });

    it('should insert bold format without selection', () => {
      const result = insertMarkdownFormat('Hello world', { start: 6, end: 6 }, 'bold');
      expect(result.content).toBe('Hello ****world');
      expect(result.cursorPosition).toBe(8);
    });

    it('should insert italic format correctly', () => {
      const result = insertMarkdownFormat('Hello world', { start: 6, end: 11 }, 'italic');
      expect(result.content).toBe('Hello *world*');
      expect(result.cursorPosition).toBe(13);
    });

    it('should insert inline code format', () => {
      const result = insertMarkdownFormat('Hello world', { start: 6, end: 11 }, 'code');
      expect(result.content).toBe('Hello `world`');
      expect(result.cursorPosition).toBe(13);
    });

    it('should insert multiline code block', () => {
      const result = insertMarkdownFormat('Hello\nworld', { start: 0, end: 11 }, 'code');
      expect(result.content).toBe('```\nHello\nworld\n```');
      expect(result.cursorPosition).toBe(19);
    });

    it('should insert link format', () => {
      const result = insertMarkdownFormat('Hello world', { start: 6, end: 11 }, 'link');
      expect(result.content).toBe('Hello [world](http://)');
      expect(result.cursorPosition).toBe(21);
    });

    it('should insert image format', () => {
      const result = insertMarkdownFormat('Hello world', { start: 6, end: 11 }, 'image');
      expect(result.content).toBe('Hello ![world](http://)');
      expect(result.cursorPosition).toBe(22);
    });

    it('should insert header format', () => {
      const result = insertMarkdownFormat('Hello world\nNext line', { start: 6, end: 11 }, 'header');
      expect(result.content).toBe('Hello ## world\nNext line');
      expect(result.cursorPosition).toBe(14);
    });
  });

  describe('getCurrentLineInfo', () => {
    it('should get correct line info for middle position', () => {
      const content = 'Line 1\nLine 2\nLine 3';
      const info = getCurrentLineInfo(content, 10); // Position in "Line 2"

      expect(info.content).toBe('Line 2');
      expect(info.lineNumber).toBe(2);
      expect(info.columnNumber).toBe(4);
      expect(info.start).toBe(7);
      expect(info.end).toBe(13);
      expect(info.isEmpty).toBe(false);
    });

    it('should detect list items', () => {
      const content = '- List item\n* Another item\n+ Third item';

      const info1 = getCurrentLineInfo(content, 5);
      expect(info1.isListItem).toBe(true);

      const info2 = getCurrentLineInfo(content, 15);
      expect(info2.isListItem).toBe(true);

      const info3 = getCurrentLineInfo(content, 30);
      expect(info3.isListItem).toBe(true);
    });

    it('should detect ordered list items', () => {
      const content = '1. First item\n2. Second item';

      const info1 = getCurrentLineInfo(content, 5);
      expect(info1.isOrderedListItem).toBe(true);

      const info2 = getCurrentLineInfo(content, 20);
      expect(info2.isOrderedListItem).toBe(true);
    });

    it('should detect headings', () => {
      const content = '# Heading 1\n## Heading 2';

      const info1 = getCurrentLineInfo(content, 5);
      expect(info1.isHeading).toBe(true);

      const info2 = getCurrentLineInfo(content, 18);
      expect(info2.isHeading).toBe(true);
    });

    it('should detect code blocks', () => {
      const content = '```javascript\ncode here\n```';

      const info = getCurrentLineInfo(content, 5);
      expect(info.isCodeBlock).toBe(true);
    });

    it('should detect empty lines', () => {
      const content = 'Line 1\n\nLine 3';

      const info = getCurrentLineInfo(content, 7);
      expect(info.isEmpty).toBe(true);
    });
  });

  describe('autoCompleteListItem', () => {
    it('should complete unordered list items', () => {
      const content = '- First item';
      const result = autoCompleteListItem(content, 12);

      expect(result).not.toBeNull();
      expect(result?.content).toBe('- First item\n- ');
      expect(result?.cursorPosition).toBe(15);
    });

    it('should complete ordered list items', () => {
      const content = '1. First item';
      const result = autoCompleteListItem(content, 13);

      expect(result).not.toBeNull();
      expect(result?.content).toBe('1. First item\n2. ');
      expect(result?.cursorPosition).toBe(16);
    });

    it('should handle indented list items', () => {
      const content = '  - Indented item';
      const result = autoCompleteListItem(content, 17);

      expect(result).not.toBeNull();
      expect(result?.content).toBe('  - Indented item\n  - ');
      expect(result?.cursorPosition).toBe(21);
    });

    it('should handle ordered list with double digits', () => {
      const content = '10. Tenth item';
      const result = autoCompleteListItem(content, 14);

      expect(result).not.toBeNull();
      expect(result?.content).toBe('10. Tenth item\n11. ');
      expect(result?.cursorPosition).toBe(19);
    });

    it('should return null for non-list items', () => {
      const content = 'Regular paragraph';
      const result = autoCompleteListItem(content, 17);

      expect(result).toBeNull();
    });

    it('should return null for middle-of-line positions', () => {
      const content = '- List item';
      const result = autoCompleteListItem(content, 5);

      expect(result).toBeNull();
    });
  });

  describe('isMarkdownEmpty', () => {
    it('should return true for empty string', () => {
      expect(isMarkdownEmpty('')).toBe(true);
    });

    it('should return true for whitespace-only string', () => {
      expect(isMarkdownEmpty('   \n\t  ')).toBe(true);
    });

    it('should return false for content with text', () => {
      expect(isMarkdownEmpty('Some content')).toBe(false);
    });

    it('should return false for markdown with only formatting', () => {
      expect(isMarkdownEmpty('**bold**')).toBe(false);
    });
  });

  describe('debounce', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should delay function execution', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 100);

      debouncedFn();
      expect(fn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(50);
      expect(fn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(50);
      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('should reset delay on subsequent calls', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 100);

      debouncedFn();
      vi.advanceTimersByTime(50);
      debouncedFn(); // Reset timer

      vi.advanceTimersByTime(50);
      expect(fn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(50);
      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('should pass arguments correctly', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 100);

      debouncedFn('arg1', 'arg2');
      vi.advanceTimersByTime(100);

      expect(fn).toHaveBeenCalledWith('arg1', 'arg2');
    });
  });

  describe('throttle', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should limit function execution frequency', () => {
      const fn = vi.fn();
      const throttledFn = throttle(fn, 100);

      throttledFn(); // Should execute immediately
      expect(fn).toHaveBeenCalledTimes(1);

      throttledFn(); // Should be ignored
      expect(fn).toHaveBeenCalledTimes(1);

      vi.advanceTimersByTime(100);
      throttledFn(); // Should execute after delay
      expect(fn).toHaveBeenCalledTimes(2);
    });

    it('should pass arguments correctly', () => {
      const fn = vi.fn();
      const throttledFn = throttle(fn, 100);

      throttledFn('arg1', 'arg2');
      expect(fn).toHaveBeenCalledWith('arg1', 'arg2');
    });

    it('should handle rapid successive calls', () => {
      const fn = vi.fn();
      const throttledFn = throttle(fn, 100);

      throttledFn();
      throttledFn();
      throttledFn();

      expect(fn).toHaveBeenCalledTimes(1);

      vi.advanceTimersByTime(100);
      throttledFn();

      expect(fn).toHaveBeenCalledTimes(2);
    });
  });
});