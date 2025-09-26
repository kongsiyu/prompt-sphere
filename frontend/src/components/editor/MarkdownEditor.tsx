/**
 * Markdown 编辑器组件
 * 基于 @uiw/react-md-editor，支持语法高亮、快捷键和工具栏
 */

import React, { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react';
import MDEditor from '@uiw/react-md-editor';
import { cn } from '../../utils/cn';
import {
  insertMarkdownFormat,
  autoCompleteListItem,
  getCurrentLineInfo,
  getMarkdownStats,
  type MarkdownStats,
} from '../../utils/markdown';

/**
 * 编辑器主题
 */
export type EditorTheme = 'light' | 'dark';

/**
 * 编辑器配置选项
 */
export interface MarkdownEditorOptions {
  /** 是否显示工具栏，默认 true */
  showToolbar?: boolean;
  /** 是否显示预览，默认 false（由外部控制） */
  showPreview?: boolean;
  /** 是否启用行号，默认 false */
  showLineNumbers?: boolean;
  /** 是否启用代码折叠，默认 true */
  enableCodeFolding?: boolean;
  /** 是否启用自动补全，默认 true */
  enableAutoComplete?: boolean;
  /** 主题，默认 'light' */
  theme?: EditorTheme;
  /** 占位符文本 */
  placeholder?: string;
  /** 最大高度（CSS 值） */
  maxHeight?: string;
  /** 最小高度（CSS 值） */
  minHeight?: string;
  /** 是否只读 */
  readOnly?: boolean;
  /** Tab 键大小 */
  tabSize?: number;
}

/**
 * 编辑器属性
 */
export interface MarkdownEditorProps {
  /** 初始值 */
  value?: string;
  /** 值变化回调 */
  onChange?: (value: string) => void;
  /** 焦点变化回调 */
  onFocus?: (focused: boolean) => void;
  /** 滚动回调 */
  onScroll?: (event: Event) => void;
  /** 选择变化回调 */
  onSelectionChange?: (start: number, end: number) => void;
  /** 统计信息变化回调 */
  onStatsChange?: (stats: MarkdownStats) => void;
  /** 编辑器配置选项 */
  options?: MarkdownEditorOptions;
  /** 自定义样式类名 */
  className?: string;
  /** 内联样式 */
  style?: React.CSSProperties;
  /** 是否禁用 */
  disabled?: boolean;
}

/**
 * 编辑器引用接口
 */
export interface MarkdownEditorRef {
  /** 获取编辑器实例 */
  getEditor: () => HTMLTextAreaElement | null;
  /** 插入文本 */
  insertText: (text: string) => void;
  /** 插入格式 */
  insertFormat: (format: 'bold' | 'italic' | 'code' | 'link' | 'image' | 'header') => void;
  /** 获取选中文本 */
  getSelectedText: () => string;
  /** 设置选中范围 */
  setSelection: (start: number, end: number) => void;
  /** 聚焦编辑器 */
  focus: () => void;
  /** 获取统计信息 */
  getStats: () => MarkdownStats;
  /** 撤销 */
  undo: () => void;
  /** 重做 */
  redo: () => void;
}

/**
 * 默认编辑器选项
 */
const defaultOptions: Required<MarkdownEditorOptions> = {
  showToolbar: true,
  showPreview: false,
  showLineNumbers: false,
  enableCodeFolding: true,
  enableAutoComplete: true,
  theme: 'light',
  placeholder: '开始编写您的 Markdown 内容...',
  maxHeight: '600px',
  minHeight: '300px',
  readOnly: false,
  tabSize: 2,
};

/**
 * Markdown 编辑器组件
 */
export const MarkdownEditor = forwardRef<MarkdownEditorRef, MarkdownEditorProps>(
  function MarkdownEditor(props, ref) {
    const {
      value = '',
      onChange,
      onFocus,
      onScroll,
      onSelectionChange,
      onStatsChange,
      options = {},
      className,
      style,
      disabled = false,
    } = props;

    // 合并选项
    const resolvedOptions = { ...defaultOptions, ...options };

    // 状态
    const [internalValue, setInternalValue] = useState(value);
    const [isFocused, setIsFocused] = useState(false);
    const [selection, setSelection] = useState({ start: 0, end: 0 });

    // 引用
    const editorRef = useRef<HTMLTextAreaElement | null>(null);
    const containerRef = useRef<HTMLDivElement | null>(null);

    /**
     * 处理值变化
     */
    const handleChange = useCallback((val: string = '') => {
      setInternalValue(val);
      onChange?.(val);

      // 计算统计信息
      const stats = getMarkdownStats(val);
      onStatsChange?.(stats);
    }, [onChange, onStatsChange]);

    /**
     * 处理焦点变化
     */
    const handleFocus = useCallback(() => {
      setIsFocused(true);
      onFocus?.(true);
    }, [onFocus]);

    /**
     * 处理失去焦点
     */
    const handleBlur = useCallback(() => {
      setIsFocused(false);
      onFocus?.(false);
    }, [onFocus]);

    /**
     * 处理键盘事件
     */
    const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLTextAreaElement>) => {
      const editor = event.currentTarget;
      const { selectionStart, selectionEnd } = editor;

      // Enter 键自动补全列表
      if (event.key === 'Enter' && resolvedOptions.enableAutoComplete) {
        const autoCompleteResult = autoCompleteListItem(internalValue, selectionStart);
        if (autoCompleteResult) {
          event.preventDefault();
          handleChange(autoCompleteResult.content);

          // 设置新的光标位置
          setTimeout(() => {
            editor.setSelectionRange(
              autoCompleteResult.cursorPosition,
              autoCompleteResult.cursorPosition
            );
          }, 0);
        }
      }

      // Tab 键处理
      if (event.key === 'Tab') {
        event.preventDefault();
        const tabString = ' '.repeat(resolvedOptions.tabSize);
        const newValue =
          internalValue.slice(0, selectionStart) +
          tabString +
          internalValue.slice(selectionEnd);

        handleChange(newValue);

        setTimeout(() => {
          const newPosition = selectionStart + tabString.length;
          editor.setSelectionRange(newPosition, newPosition);
        }, 0);
      }

      // 快捷键处理
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case 'b':
            event.preventDefault();
            insertFormat('bold');
            break;
          case 'i':
            event.preventDefault();
            insertFormat('italic');
            break;
          case 'k':
            event.preventDefault();
            insertFormat('link');
            break;
          case '`':
            event.preventDefault();
            insertFormat('code');
            break;
        }
      }
    }, [internalValue, resolvedOptions.enableAutoComplete, resolvedOptions.tabSize, handleChange]);

    /**
     * 处理选择变化
     */
    const handleSelectionChange = useCallback(() => {
      const editor = editorRef.current;
      if (editor) {
        const { selectionStart, selectionEnd } = editor;
        setSelection({ start: selectionStart, end: selectionEnd });
        onSelectionChange?.(selectionStart, selectionEnd);
      }
    }, [onSelectionChange]);

    /**
     * 处理滚动事件
     */
    const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
      onScroll?.(event.nativeEvent);
    }, [onScroll]);

    /**
     * 插入文本
     */
    const insertText = useCallback((text: string) => {
      const editor = editorRef.current;
      if (!editor) return;

      const { selectionStart, selectionEnd } = editor;
      const newValue =
        internalValue.slice(0, selectionStart) +
        text +
        internalValue.slice(selectionEnd);

      handleChange(newValue);

      setTimeout(() => {
        const newPosition = selectionStart + text.length;
        editor.setSelectionRange(newPosition, newPosition);
        editor.focus();
      }, 0);
    }, [internalValue, handleChange]);

    /**
     * 插入格式
     */
    const insertFormat = useCallback((format: 'bold' | 'italic' | 'code' | 'link' | 'image' | 'header') => {
      const editor = editorRef.current;
      if (!editor) return;

      const { selectionStart, selectionEnd } = editor;
      const result = insertMarkdownFormat(
        internalValue,
        { start: selectionStart, end: selectionEnd },
        format
      );

      handleChange(result.content);

      setTimeout(() => {
        editor.setSelectionRange(result.cursorPosition, result.cursorPosition);
        editor.focus();
      }, 0);
    }, [internalValue, handleChange]);

    /**
     * 获取选中文本
     */
    const getSelectedText = useCallback(() => {
      return internalValue.slice(selection.start, selection.end);
    }, [internalValue, selection]);

    /**
     * 设置选中范围
     */
    const setSelectionRange = useCallback((start: number, end: number) => {
      const editor = editorRef.current;
      if (editor) {
        editor.setSelectionRange(start, end);
        setSelection({ start, end });
      }
    }, []);

    /**
     * 聚焦编辑器
     */
    const focusEditor = useCallback(() => {
      editorRef.current?.focus();
    }, []);

    /**
     * 获取统计信息
     */
    const getStats = useCallback(() => {
      return getMarkdownStats(internalValue);
    }, [internalValue]);

    // 暴露方法给外部引用
    useImperativeHandle(ref, () => ({
      getEditor: () => editorRef.current,
      insertText,
      insertFormat,
      getSelectedText,
      setSelection: setSelectionRange,
      focus: focusEditor,
      getStats,
      undo: () => {
        // 简单的撤销实现，可以扩展为更完整的历史记录
        document.execCommand('undo');
      },
      redo: () => {
        // 简单的重做实现
        document.execCommand('redo');
      },
    }), [insertText, insertFormat, getSelectedText, setSelectionRange, focusEditor, getStats]);

    // 同步外部 value 变化
    useEffect(() => {
      if (value !== internalValue) {
        setInternalValue(value);
      }
    }, [value]);

    // 编辑器配置
    const editorData = {
      'data-color-mode': resolvedOptions.theme,
    };

    return (
      <div
        ref={containerRef}
        className={cn(
          'markdown-editor-container',
          'border rounded-md overflow-hidden',
          resolvedOptions.theme === 'dark'
            ? 'border-gray-600 bg-gray-800'
            : 'border-gray-300 bg-white',
          disabled && 'opacity-50 pointer-events-none',
          className
        )}
        style={{
          minHeight: resolvedOptions.minHeight,
          maxHeight: resolvedOptions.maxHeight,
          ...style,
        }}
        onScroll={handleScroll}
        {...editorData}
      >
        <MDEditor
          value={internalValue}
          onChange={handleChange}
          preview={resolvedOptions.showPreview ? 'edit' : 'edit'}
          hideToolbar={!resolvedOptions.showToolbar}
          data-color-mode={resolvedOptions.theme}
          textareaProps={{
            ref: editorRef,
            placeholder: resolvedOptions.placeholder,
            disabled,
            style: {
              fontSize: '14px',
              lineHeight: '1.5',
              fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
            },
            onFocus: handleFocus,
            onBlur: handleBlur,
            onKeyDown: handleKeyDown,
            onSelect: handleSelectionChange,
            onClick: handleSelectionChange,
          }}
          height={undefined} // 让容器控制高度
        />
      </div>
    );
  }
);

export default MarkdownEditor;