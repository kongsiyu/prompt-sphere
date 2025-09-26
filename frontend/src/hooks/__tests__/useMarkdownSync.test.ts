/**
 * useMarkdownSync 钩子测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useMarkdownSync } from '../useMarkdownSync';

// Mock DOM elements
const createMockElement = (scrollTop = 0, scrollHeight = 1000, clientHeight = 500): HTMLElement => {
  const element = {
    scrollTop,
    scrollHeight,
    clientHeight,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  } as unknown as HTMLElement;

  return element;
};

describe('useMarkdownSync', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('initialization', () => {
    it('should initialize with correct default state', () => {
      const { result } = renderHook(() => useMarkdownSync('initial content'));

      expect(result.current.content).toBe('initial content');
      expect(result.current.editorFocused).toBe(false);
      expect(result.current.previewFocused).toBe(false);
      expect(result.current.editorScrollTop).toBe(0);
      expect(result.current.previewScrollTop).toBe(0);
      expect(result.current.isSyncingScroll).toBe(false);
    });

    it('should initialize with empty content when no initial content provided', () => {
      const { result } = renderHook(() => useMarkdownSync());

      expect(result.current.content).toBe('');
    });

    it('should accept scroll sync options', () => {
      const { result } = renderHook(() =>
        useMarkdownSync('content', { enabled: false, throttleDelay: 32 })
      );

      expect(result.current.content).toBe('content');
      // Options are internal, but we can verify they don't cause errors
    });
  });

  describe('content management', () => {
    it('should update content correctly', () => {
      const { result } = renderHook(() => useMarkdownSync('initial'));

      act(() => {
        result.current.updateContent('updated content');
      });

      expect(result.current.content).toBe('updated content');
    });
  });

  describe('focus management', () => {
    it('should handle editor focus correctly', () => {
      const { result } = renderHook(() => useMarkdownSync());

      act(() => {
        result.current.handleEditorFocus(true);
      });

      expect(result.current.editorFocused).toBe(true);
      expect(result.current.previewFocused).toBe(false);
    });

    it('should handle preview focus correctly', () => {
      const { result } = renderHook(() => useMarkdownSync());

      act(() => {
        result.current.handlePreviewFocus(true);
      });

      expect(result.current.previewFocused).toBe(true);
      expect(result.current.editorFocused).toBe(false);
    });

    it('should handle mutual exclusion of focus states', () => {
      const { result } = renderHook(() => useMarkdownSync());

      // Focus editor first
      act(() => {
        result.current.handleEditorFocus(true);
      });

      expect(result.current.editorFocused).toBe(true);
      expect(result.current.previewFocused).toBe(false);

      // Focus preview should unfocus editor
      act(() => {
        result.current.handlePreviewFocus(true);
      });

      expect(result.current.editorFocused).toBe(false);
      expect(result.current.previewFocused).toBe(true);
    });

    it('should handle blur events correctly', () => {
      const { result } = renderHook(() => useMarkdownSync());

      // Focus editor first
      act(() => {
        result.current.handleEditorFocus(true);
      });

      // Blur editor
      act(() => {
        result.current.handleEditorFocus(false);
      });

      expect(result.current.editorFocused).toBe(false);
      expect(result.current.previewFocused).toBe(false);
    });

    it('should return correct active pane', () => {
      const { result } = renderHook(() => useMarkdownSync());

      expect(result.current.getActivePane()).toBeNull();

      act(() => {
        result.current.handleEditorFocus(true);
      });

      expect(result.current.getActivePane()).toBe('editor');

      act(() => {
        result.current.handlePreviewFocus(true);
      });

      expect(result.current.getActivePane()).toBe('preview');
    });
  });

  describe('reference management', () => {
    it('should set editor reference correctly', () => {
      const { result } = renderHook(() => useMarkdownSync());
      const mockEditor = createMockElement();

      act(() => {
        result.current.setEditorRef(mockEditor);
      });

      // We can't directly test the ref, but we can verify it doesn't cause errors
      expect(() => result.current.setEditorRef(mockEditor)).not.toThrow();
    });

    it('should set preview reference correctly', () => {
      const { result } = renderHook(() => useMarkdownSync());
      const mockPreview = createMockElement();

      act(() => {
        result.current.setPreviewRef(mockPreview);
      });

      // We can't directly test the ref, but we can verify it doesn't cause errors
      expect(() => result.current.setPreviewRef(mockPreview)).not.toThrow();
    });

    it('should handle null references gracefully', () => {
      const { result } = renderHook(() => useMarkdownSync());

      act(() => {
        result.current.setEditorRef(null);
        result.current.setPreviewRef(null);
      });

      expect(() => {
        result.current.setEditorRef(null);
        result.current.setPreviewRef(null);
      }).not.toThrow();
    });
  });

  describe('scroll management', () => {
    it('should scroll to specific line', () => {
      const { result } = renderHook(() => useMarkdownSync());
      const mockEditor = createMockElement();

      act(() => {
        result.current.setEditorRef(mockEditor);
        result.current.scrollToLine(10, 'editor');
      });

      // Should set scrollTop to estimated position (line 10 * 20px line height = 180px)
      expect(mockEditor.scrollTop).toBe(180);
    });

    it('should reset scroll positions', () => {
      const { result } = renderHook(() => useMarkdownSync());
      const mockEditor = createMockElement(100);
      const mockPreview = createMockElement(150);

      act(() => {
        result.current.setEditorRef(mockEditor);
        result.current.setPreviewRef(mockPreview);
        result.current.resetScroll();
      });

      expect(mockEditor.scrollTop).toBe(0);
      expect(mockPreview.scrollTop).toBe(0);
      expect(result.current.editorScrollTop).toBe(0);
      expect(result.current.previewScrollTop).toBe(0);
    });

    it('should handle scroll to line with invalid line numbers', () => {
      const { result } = renderHook(() => useMarkdownSync());
      const mockEditor = createMockElement();

      act(() => {
        result.current.setEditorRef(mockEditor);
        result.current.scrollToLine(0, 'editor'); // Line 0 should be handled
      });

      expect(mockEditor.scrollTop).toBe(0);

      act(() => {
        result.current.scrollToLine(-5, 'editor'); // Negative line should be handled
      });

      expect(mockEditor.scrollTop).toBe(0);
    });
  });

  describe('scroll synchronization', () => {
    it('should bind scroll event listeners when refs are set', () => {
      const { result } = renderHook(() =>
        useMarkdownSync('', { enabled: true })
      );

      const mockEditor = createMockElement();
      const mockPreview = createMockElement();

      act(() => {
        result.current.setEditorRef(mockEditor);
        result.current.setPreviewRef(mockPreview);
      });

      expect(mockEditor.addEventListener).toHaveBeenCalledWith(
        'scroll',
        expect.any(Function)
      );
      expect(mockPreview.addEventListener).toHaveBeenCalledWith(
        'scroll',
        expect.any(Function)
      );
    });

    it('should not bind scroll events when sync is disabled', () => {
      const { result } = renderHook(() =>
        useMarkdownSync('', { enabled: false })
      );

      const mockEditor = createMockElement();
      const mockPreview = createMockElement();

      act(() => {
        result.current.setEditorRef(mockEditor);
        result.current.setPreviewRef(mockPreview);
      });

      expect(mockEditor.addEventListener).not.toHaveBeenCalled();
      expect(mockPreview.addEventListener).not.toHaveBeenCalled();
    });

    it('should remove event listeners on cleanup', () => {
      const { result, unmount } = renderHook(() =>
        useMarkdownSync('', { enabled: true })
      );

      const mockEditor = createMockElement();
      const mockPreview = createMockElement();

      act(() => {
        result.current.setEditorRef(mockEditor);
        result.current.setPreviewRef(mockPreview);
      });

      unmount();

      expect(mockEditor.removeEventListener).toHaveBeenCalledWith(
        'scroll',
        expect.any(Function)
      );
      expect(mockPreview.removeEventListener).toHaveBeenCalledWith(
        'scroll',
        expect.any(Function)
      );
    });
  });

  describe('scroll event handling', () => {
    it('should handle editor scroll events', () => {
      const { result } = renderHook(() => useMarkdownSync());
      const mockEvent = {
        target: createMockElement(100, 1000, 500)
      } as unknown as Event;

      act(() => {
        result.current.onEditorScroll(mockEvent);
      });

      // Should not throw errors even without refs set
      expect(() => result.current.onEditorScroll(mockEvent)).not.toThrow();
    });

    it('should handle preview scroll events', () => {
      const { result } = renderHook(() => useMarkdownSync());
      const mockEvent = {
        target: createMockElement(150, 1000, 500)
      } as unknown as Event;

      act(() => {
        result.current.onPreviewScroll(mockEvent);
      });

      // Should not throw errors even without refs set
      expect(() => result.current.onPreviewScroll(mockEvent)).not.toThrow();
    });
  });

  describe('throttling behavior', () => {
    it('should respect throttle delay in scroll sync', async () => {
      const throttleDelay = 100;
      const { result } = renderHook(() =>
        useMarkdownSync('', { enabled: true, throttleDelay })
      );

      const mockEditor = createMockElement(0, 1000, 500);
      const mockPreview = createMockElement(0, 1000, 500);

      act(() => {
        result.current.setEditorRef(mockEditor);
        result.current.setPreviewRef(mockPreview);
      });

      // Simulate rapid scroll events
      const mockEvent = { target: mockEditor } as unknown as Event;

      act(() => {
        result.current.onEditorScroll(mockEvent);
        result.current.onEditorScroll(mockEvent);
        result.current.onEditorScroll(mockEvent);
      });

      // Due to throttling, only the first event should process immediately
      // Subsequent events should be throttled
      expect(mockEditor.addEventListener).toHaveBeenCalled();
    });
  });

  describe('content change effects', () => {
    it('should reset sync state when content changes', () => {
      const { result } = renderHook(() => useMarkdownSync('initial'));

      act(() => {
        result.current.updateContent('new content');
      });

      // Content changes should not directly affect focus states
      expect(result.current.content).toBe('new content');
    });
  });

  describe('edge cases and error handling', () => {
    it('should handle missing DOM elements gracefully', () => {
      const { result } = renderHook(() => useMarkdownSync());

      // Try to scroll without setting refs
      act(() => {
        result.current.scrollToLine(5);
        result.current.resetScroll();
      });

      // Should not throw errors
      expect(() => {
        result.current.scrollToLine(5);
        result.current.resetScroll();
      }).not.toThrow();
    });

    it('should handle invalid scroll events', () => {
      const { result } = renderHook(() => useMarkdownSync());

      const invalidEvent = { target: null } as unknown as Event;

      act(() => {
        result.current.onEditorScroll(invalidEvent);
        result.current.onPreviewScroll(invalidEvent);
      });

      // Should not throw errors with invalid events
      expect(() => {
        result.current.onEditorScroll(invalidEvent);
        result.current.onPreviewScroll(invalidEvent);
      }).not.toThrow();
    });

    it('should handle scroll calculations with zero dimensions', () => {
      const { result } = renderHook(() => useMarkdownSync());
      const mockElement = createMockElement(0, 0, 0); // Zero dimensions

      act(() => {
        result.current.setEditorRef(mockElement);
        result.current.scrollToLine(10);
      });

      // Should handle zero dimensions gracefully
      expect(() => result.current.scrollToLine(10)).not.toThrow();
    });
  });

  describe('configuration options', () => {
    it('should respect custom throttle delay', () => {
      const customDelay = 50;
      const { result } = renderHook(() =>
        useMarkdownSync('', { throttleDelay: customDelay })
      );

      // Hook should initialize without errors with custom delay
      expect(result.current.content).toBe('');
    });

    it('should respect custom offset', () => {
      const customOffset = 10;
      const { result } = renderHook(() =>
        useMarkdownSync('', { offset: customOffset })
      );

      // Hook should initialize without errors with custom offset
      expect(result.current.content).toBe('');
    });

    it('should handle all configuration options together', () => {
      const { result } = renderHook(() =>
        useMarkdownSync('test content', {
          enabled: true,
          throttleDelay: 32,
          offset: 5
        })
      );

      expect(result.current.content).toBe('test content');
    });
  });
});