/**
 * Markdown 同步钩子
 * 处理编辑器和预览之间的双向同步，包括内容同步和滚动同步
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { throttle } from '../utils/markdown';

/**
 * 滚动同步选项
 */
export interface ScrollSyncOptions {
  /** 是否启用滚动同步，默认 true */
  enabled?: boolean;
  /** 节流延迟（毫秒），默认 16 */
  throttleDelay?: number;
  /** 同步偏移量，用于调整同步精度 */
  offset?: number;
}

/**
 * Markdown 同步状态
 */
export interface MarkdownSyncState {
  /** 当前内容 */
  content: string;
  /** 编辑器是否获得焦点 */
  editorFocused: boolean;
  /** 预览是否获得焦点 */
  previewFocused: boolean;
  /** 编辑器滚动位置 */
  editorScrollTop: number;
  /** 预览滚动位置 */
  previewScrollTop: number;
  /** 是否正在同步滚动 */
  isSyncingScroll: boolean;
}

/**
 * 同步来源
 */
type SyncSource = 'editor' | 'preview';

/**
 * Markdown 同步钩子
 *
 * @param initialContent - 初始内容
 * @param scrollSyncOptions - 滚动同步选项
 * @returns 同步状态和控制函数
 */
export function useMarkdownSync(
  initialContent: string = '',
  scrollSyncOptions: ScrollSyncOptions = {}
) {
  const {
    enabled: scrollSyncEnabled = true,
    throttleDelay = 16,
    offset = 0,
  } = scrollSyncOptions;

  const [state, setState] = useState<MarkdownSyncState>({
    content: initialContent,
    editorFocused: false,
    previewFocused: false,
    editorScrollTop: 0,
    previewScrollTop: 0,
    isSyncingScroll: false,
  });

  // 使用 ref 存储 DOM 引用
  const editorRef = useRef<HTMLElement | null>(null);
  const previewRef = useRef<HTMLElement | null>(null);
  const syncingRef = useRef<boolean>(false);
  const lastSyncSourceRef = useRef<SyncSource | null>(null);

  /**
   * 设置编辑器引用
   */
  const setEditorRef = useCallback((element: HTMLElement | null) => {
    editorRef.current = element;
  }, []);

  /**
   * 设置预览引用
   */
  const setPreviewRef = useCallback((element: HTMLElement | null) => {
    previewRef.current = element;
  }, []);

  /**
   * 更新内容
   */
  const updateContent = useCallback((newContent: string) => {
    setState(prev => ({
      ...prev,
      content: newContent,
    }));
  }, []);

  /**
   * 处理编辑器焦点变化
   */
  const handleEditorFocus = useCallback((focused: boolean) => {
    setState(prev => ({
      ...prev,
      editorFocused: focused,
      previewFocused: focused ? false : prev.previewFocused,
    }));
  }, []);

  /**
   * 处理预览焦点变化
   */
  const handlePreviewFocus = useCallback((focused: boolean) => {
    setState(prev => ({
      ...prev,
      previewFocused: focused,
      editorFocused: focused ? false : prev.editorFocused,
    }));
  }, []);

  /**
   * 计算滚动比例
   */
  const getScrollRatio = useCallback((element: HTMLElement): number => {
    const { scrollTop, scrollHeight, clientHeight } = element;
    const maxScroll = scrollHeight - clientHeight;
    return maxScroll > 0 ? scrollTop / maxScroll : 0;
  }, []);

  /**
   * 根据比例设置滚动位置
   */
  const setScrollByRatio = useCallback((element: HTMLElement, ratio: number) => {
    const { scrollHeight, clientHeight } = element;
    const maxScroll = scrollHeight - clientHeight;
    const scrollTop = Math.max(0, Math.min(maxScroll, maxScroll * ratio + offset));
    element.scrollTop = scrollTop;
  }, [offset]);

  /**
   * 同步编辑器到预览的滚动
   */
  const syncEditorToPreview = useCallback(
    throttle((editorElement: HTMLElement) => {
      if (!scrollSyncEnabled || !previewRef.current || syncingRef.current) {
        return;
      }

      syncingRef.current = true;
      lastSyncSourceRef.current = 'editor';

      setState(prev => ({ ...prev, isSyncingScroll: true }));

      const scrollRatio = getScrollRatio(editorElement);
      setScrollByRatio(previewRef.current, scrollRatio);

      const editorScrollTop = editorElement.scrollTop;
      const previewScrollTop = previewRef.current.scrollTop;

      setState(prev => ({
        ...prev,
        editorScrollTop,
        previewScrollTop,
        isSyncingScroll: false,
      }));

      // 延迟重置同步标志，避免循环同步
      setTimeout(() => {
        syncingRef.current = false;
      }, 100);
    }, throttleDelay),
    [scrollSyncEnabled, throttleDelay, getScrollRatio, setScrollByRatio]
  );

  /**
   * 同步预览到编辑器的滚动
   */
  const syncPreviewToEditor = useCallback(
    throttle((previewElement: HTMLElement) => {
      if (!scrollSyncEnabled || !editorRef.current || syncingRef.current) {
        return;
      }

      syncingRef.current = true;
      lastSyncSourceRef.current = 'preview';

      setState(prev => ({ ...prev, isSyncingScroll: true }));

      const scrollRatio = getScrollRatio(previewElement);
      setScrollByRatio(editorRef.current, scrollRatio);

      const editorScrollTop = editorRef.current.scrollTop;
      const previewScrollTop = previewElement.scrollTop;

      setState(prev => ({
        ...prev,
        editorScrollTop,
        previewScrollTop,
        isSyncingScroll: false,
      }));

      // 延迟重置同步标志，避免循环同步
      setTimeout(() => {
        syncingRef.current = false;
      }, 100);
    }, throttleDelay),
    [scrollSyncEnabled, throttleDelay, getScrollRatio, setScrollByRatio]
  );

  /**
   * 处理编辑器滚动
   */
  const handleEditorScroll = useCallback((event: Event) => {
    const target = event.target as HTMLElement;
    if (target && lastSyncSourceRef.current !== 'preview') {
      syncEditorToPreview(target);
    }
  }, [syncEditorToPreview]);

  /**
   * 处理预览滚动
   */
  const handlePreviewScroll = useCallback((event: Event) => {
    const target = event.target as HTMLElement;
    if (target && lastSyncSourceRef.current !== 'editor') {
      syncPreviewToEditor(target);
    }
  }, [syncPreviewToEditor]);

  /**
   * 滚动到指定行
   */
  const scrollToLine = useCallback((lineNumber: number, source: SyncSource = 'editor') => {
    const targetRef = source === 'editor' ? editorRef : previewRef;
    const element = targetRef.current;

    if (!element) {
      return;
    }

    // 简单的行高估算（可以根据实际情况调整）
    const estimatedLineHeight = 20;
    const scrollTop = Math.max(0, (lineNumber - 1) * estimatedLineHeight);

    syncingRef.current = true;
    element.scrollTop = scrollTop;

    setState(prev => ({
      ...prev,
      [source === 'editor' ? 'editorScrollTop' : 'previewScrollTop']: scrollTop,
    }));

    setTimeout(() => {
      syncingRef.current = false;
    }, 100);
  }, []);

  /**
   * 重置滚动位置
   */
  const resetScroll = useCallback(() => {
    [editorRef, previewRef].forEach(ref => {
      if (ref.current) {
        ref.current.scrollTop = 0;
      }
    });

    setState(prev => ({
      ...prev,
      editorScrollTop: 0,
      previewScrollTop: 0,
    }));
  }, []);

  /**
   * 获取当前激活的窗格
   */
  const getActivePane = useCallback((): SyncSource | null => {
    if (state.editorFocused) return 'editor';
    if (state.previewFocused) return 'preview';
    return null;
  }, [state.editorFocused, state.previewFocused]);

  // 绑定滚动事件监听器
  useEffect(() => {
    const editorElement = editorRef.current;
    const previewElement = previewRef.current;

    if (!scrollSyncEnabled) {
      return;
    }

    if (editorElement) {
      editorElement.addEventListener('scroll', handleEditorScroll);
    }

    if (previewElement) {
      previewElement.addEventListener('scroll', handlePreviewScroll);
    }

    return () => {
      if (editorElement) {
        editorElement.removeEventListener('scroll', handleEditorScroll);
      }
      if (previewElement) {
        previewElement.removeEventListener('scroll', handlePreviewScroll);
      }
    };
  }, [scrollSyncEnabled, handleEditorScroll, handlePreviewScroll]);

  // 监听内容变化，重置同步状态
  useEffect(() => {
    lastSyncSourceRef.current = null;
  }, [state.content]);

  return {
    // 状态
    ...state,

    // 引用设置函数
    setEditorRef,
    setPreviewRef,

    // 内容控制
    updateContent,

    // 焦点控制
    handleEditorFocus,
    handlePreviewFocus,

    // 滚动控制
    scrollToLine,
    resetScroll,
    getActivePane,

    // 滚动事件处理器（供组件使用）
    onEditorScroll: handleEditorScroll,
    onPreviewScroll: handlePreviewScroll,
  };
}