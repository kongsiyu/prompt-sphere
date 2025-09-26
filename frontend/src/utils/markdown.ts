/**
 * Markdown 处理工具函数
 * 提供 Markdown 文本的解析、格式化和辅助功能
 */

import { remark } from 'remark';
import remarkGfm from 'remark-gfm';

/**
 * Markdown 格式化选项
 */
export interface MarkdownFormatOptions {
  /** 是否启用 GitHub Flavored Markdown */
  enableGfm?: boolean;
  /** 是否移除多余的空行 */
  removeExtraNewlines?: boolean;
  /** 是否标准化缩进 */
  normalizeIndentation?: boolean;
  /** 缩进大小（空格数） */
  indentSize?: number;
}

/**
 * Markdown 统计信息
 */
export interface MarkdownStats {
  /** 字符数 */
  characters: number;
  /** 单词数 */
  words: number;
  /** 行数 */
  lines: number;
  /** 段落数 */
  paragraphs: number;
  /** 标题数 */
  headings: number;
  /** 代码块数 */
  codeBlocks: number;
  /** 链接数 */
  links: number;
  /** 图片数 */
  images: number;
}

/**
 * 格式化 Markdown 文本
 *
 * @param content - Markdown 内容
 * @param options - 格式化选项
 * @returns 格式化后的 Markdown 文本
 */
export function formatMarkdown(
  content: string,
  options: MarkdownFormatOptions = {}
): string {
  const {
    enableGfm = true,
    removeExtraNewlines = true,
    normalizeIndentation = true,
    indentSize = 2,
  } = options;

  let formatted = content;

  // 移除多余的空行（连续的空行合并为一个）
  if (removeExtraNewlines) {
    formatted = formatted.replace(/\n\s*\n\s*\n/g, '\n\n');
  }

  // 标准化缩进
  if (normalizeIndentation) {
    formatted = normalizeMarkdownIndentation(formatted, indentSize);
  }

  // 确保文件末尾有换行符
  if (formatted && !formatted.endsWith('\n')) {
    formatted += '\n';
  }

  return formatted;
}

/**
 * 标准化 Markdown 缩进
 *
 * @param content - Markdown 内容
 * @param indentSize - 缩进大小
 * @returns 标准化缩进后的内容
 */
export function normalizeMarkdownIndentation(
  content: string,
  indentSize: number = 2
): string {
  const lines = content.split('\n');
  const indentString = ' '.repeat(indentSize);

  return lines
    .map((line) => {
      // 处理列表项的缩进
      if (line.match(/^(\s*)[-*+]\s/)) {
        const match = line.match(/^(\s*)(.*)$/);
        if (match) {
          const indentLevel = Math.floor(match[1].length / indentSize);
          return indentString.repeat(indentLevel) + match[2].trimStart();
        }
      }

      // 处理有序列表的缩进
      if (line.match(/^(\s*)\d+\.\s/)) {
        const match = line.match(/^(\s*)(.*)$/);
        if (match) {
          const indentLevel = Math.floor(match[1].length / indentSize);
          return indentString.repeat(indentLevel) + match[2].trimStart();
        }
      }

      // 处理代码块缩进
      if (line.match(/^(\s*)(```|    )/)) {
        return line; // 保持代码块原有缩进
      }

      return line;
    })
    .join('\n');
}

/**
 * 获取 Markdown 文本统计信息
 *
 * @param content - Markdown 内容
 * @returns 统计信息
 */
export function getMarkdownStats(content: string): MarkdownStats {
  const lines = content.split('\n');
  const nonEmptyLines = lines.filter((line) => line.trim().length > 0);

  // 计算字符数（不包括 Markdown 标记）
  const plainText = content
    .replace(/!\[.*?\]\(.*?\)/g, '') // 移除图片
    .replace(/\[.*?\]\(.*?\)/g, '') // 移除链接
    .replace(/```[\s\S]*?```/g, '') // 移除代码块
    .replace(/`[^`]+`/g, '') // 移除内联代码
    .replace(/[#*_~`]/g, '') // 移除 Markdown 标记
    .replace(/^\s*[-*+]\s/gm, '') // 移除列表标记
    .replace(/^\s*\d+\.\s/gm, ''); // 移除有序列表标记

  // 计算单词数（支持中文）
  const wordCount = plainText
    .replace(/[\u4e00-\u9fa5]/g, ' ') // 中文字符替换为空格
    .split(/\s+/)
    .filter((word) => word.length > 0).length +
    (plainText.match(/[\u4e00-\u9fa5]/g) || []).length; // 加上中文字符数

  return {
    characters: plainText.length,
    words: wordCount,
    lines: lines.length,
    paragraphs: content.split(/\n\s*\n/).filter((p) => p.trim().length > 0).length,
    headings: (content.match(/^#+\s/gm) || []).length,
    codeBlocks: (content.match(/```[\s\S]*?```/g) || []).length,
    links: (content.match(/\[.*?\]\(.*?\)/g) || []).length,
    images: (content.match(/!\[.*?\]\(.*?\)/g) || []).length,
  };
}

/**
 * 插入 Markdown 格式文本
 *
 * @param content - 原始内容
 * @param selection - 选中的文本范围
 * @param format - 要插入的格式
 * @returns 格式化后的内容和新的光标位置
 */
export function insertMarkdownFormat(
  content: string,
  selection: { start: number; end: number },
  format: 'bold' | 'italic' | 'code' | 'link' | 'image' | 'header'
): { content: string; cursorPosition: number } {
  const { start, end } = selection;
  const selectedText = content.slice(start, end);

  let beforeText = content.slice(0, start);
  let afterText = content.slice(end);
  let insertText = '';
  let cursorOffset = 0;

  switch (format) {
    case 'bold':
      insertText = `**${selectedText}**`;
      cursorOffset = selectedText ? insertText.length : 2;
      break;

    case 'italic':
      insertText = `*${selectedText}*`;
      cursorOffset = selectedText ? insertText.length : 1;
      break;

    case 'code':
      if (selectedText.includes('\n')) {
        // 多行代码块
        insertText = `\`\`\`\n${selectedText}\n\`\`\``;
        cursorOffset = selectedText ? insertText.length : 4;
      } else {
        // 内联代码
        insertText = `\`${selectedText}\``;
        cursorOffset = selectedText ? insertText.length : 1;
      }
      break;

    case 'link':
      insertText = `[${selectedText || '链接文本'}](http://)`;
      cursorOffset = selectedText ? insertText.length - 1 : 4;
      break;

    case 'image':
      insertText = `![${selectedText || '图片描述'}](http://)`;
      cursorOffset = selectedText ? insertText.length - 1 : 4;
      break;

    case 'header':
      // 在行首插入标题标记
      const lineStart = beforeText.lastIndexOf('\n') + 1;
      beforeText = content.slice(0, lineStart);
      afterText = content.slice(lineStart);
      insertText = `## ${afterText.split('\n')[0]}`;
      cursorOffset = insertText.length;
      afterText = afterText.replace(/^.*/, '').slice(1) || '';
      break;
  }

  return {
    content: beforeText + insertText + afterText,
    cursorPosition: start + cursorOffset,
  };
}

/**
 * 获取当前行信息
 *
 * @param content - 内容
 * @param position - 光标位置
 * @returns 当前行的信息
 */
export function getCurrentLineInfo(content: string, position: number) {
  const beforePosition = content.slice(0, position);
  const afterPosition = content.slice(position);

  const lineStart = beforePosition.lastIndexOf('\n') + 1;
  const lineEnd = position + (afterPosition.indexOf('\n') !== -1 ? afterPosition.indexOf('\n') : afterPosition.length);

  const currentLine = content.slice(lineStart, lineEnd);
  const lineNumber = beforePosition.split('\n').length;
  const columnNumber = position - lineStart + 1;

  return {
    content: currentLine,
    start: lineStart,
    end: lineEnd,
    lineNumber,
    columnNumber,
    isEmpty: currentLine.trim().length === 0,
    isListItem: /^\s*[-*+]\s/.test(currentLine),
    isOrderedListItem: /^\s*\d+\.\s/.test(currentLine),
    isHeading: /^\s*#+\s/.test(currentLine),
    isCodeBlock: /^\s*```/.test(currentLine),
  };
}

/**
 * 自动补全列表项
 *
 * @param content - 内容
 * @param position - 光标位置
 * @returns 更新后的内容和光标位置
 */
export function autoCompleteListItem(
  content: string,
  position: number
): { content: string; cursorPosition: number } | null {
  const lineInfo = getCurrentLineInfo(content, position);

  // 检查是否在列表项的末尾按了回车
  if (position !== lineInfo.end) {
    return null;
  }

  let newItemPrefix = '';

  if (lineInfo.isListItem) {
    const match = lineInfo.content.match(/^(\s*)([-*+])\s/);
    if (match) {
      newItemPrefix = `${match[1]}${match[2]} `;
    }
  } else if (lineInfo.isOrderedListItem) {
    const match = lineInfo.content.match(/^(\s*)(\d+)\.\s/);
    if (match) {
      const nextNumber = parseInt(match[2]) + 1;
      newItemPrefix = `${match[1]}${nextNumber}. `;
    }
  }

  if (newItemPrefix) {
    const insertText = `\n${newItemPrefix}`;
    return {
      content: content.slice(0, position) + insertText + content.slice(position),
      cursorPosition: position + insertText.length,
    };
  }

  return null;
}

/**
 * 检查内容是否为空或只包含空白字符
 *
 * @param content - 要检查的内容
 * @returns 是否为空
 */
export function isMarkdownEmpty(content: string): boolean {
  return !content || content.trim().length === 0;
}

/**
 * 防抖函数
 *
 * @param func - 要防抖的函数
 * @param delay - 延迟时间（毫秒）
 * @returns 防抖后的函数
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

/**
 * 节流函数
 *
 * @param func - 要节流的函数
 * @param delay - 延迟时间（毫秒）
 * @returns 节流后的函数
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let lastCallTime = 0;

  return (...args: Parameters<T>) => {
    const now = Date.now();
    if (now - lastCallTime >= delay) {
      lastCallTime = now;
      func(...args);
    }
  };
}