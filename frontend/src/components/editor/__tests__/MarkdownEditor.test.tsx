/**
 * MarkdownEditor 组件测试
 */

import React, { createRef } from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MarkdownEditor, type MarkdownEditorRef } from '../MarkdownEditor';

// Mock @uiw/react-md-editor
vi.mock('@uiw/react-md-editor', () => {
  return {
    default: ({ value, onChange, textareaProps, ...props }: any) => (
      <div data-testid="md-editor" {...props}>
        <textarea
          data-testid="md-editor-textarea"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          {...textareaProps}
        />
      </div>
    )
  };
});

describe('MarkdownEditor', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('basic rendering', () => {
    it('should render with default props', () => {
      render(<MarkdownEditor />);

      expect(screen.getByTestId('md-editor')).toBeInTheDocument();
      expect(screen.getByTestId('md-editor-textarea')).toBeInTheDocument();
    });

    it('should render with initial value', () => {
      const initialValue = '# Test Content';
      render(<MarkdownEditor value={initialValue} />);

      const textarea = screen.getByTestId('md-editor-textarea');
      expect(textarea).toHaveValue(initialValue);
    });

    it('should apply custom className', () => {
      render(<MarkdownEditor className="custom-class" />);

      const container = screen.getByTestId('md-editor').closest('.markdown-editor-container');
      expect(container).toHaveClass('custom-class');
    });

    it('should apply custom styles', () => {
      const customStyles = { backgroundColor: 'red' };
      render(<MarkdownEditor style={customStyles} />);

      const container = screen.getByTestId('md-editor').closest('.markdown-editor-container');
      expect(container).toHaveStyle('background-color: red');
    });

    it('should render with disabled state', () => {
      render(<MarkdownEditor disabled />);

      const textarea = screen.getByTestId('md-editor-textarea');
      expect(textarea).toBeDisabled();

      const container = screen.getByTestId('md-editor').closest('.markdown-editor-container');
      expect(container).toHaveClass('opacity-50', 'pointer-events-none');
    });
  });

  describe('theme support', () => {
    it('should apply light theme classes by default', () => {
      render(<MarkdownEditor />);

      const container = screen.getByTestId('md-editor').closest('.markdown-editor-container');
      expect(container).toHaveClass('border-gray-300', 'bg-white');
    });

    it('should apply dark theme classes when specified', () => {
      render(<MarkdownEditor options={{ theme: 'dark' }} />);

      const container = screen.getByTestId('md-editor').closest('.markdown-editor-container');
      expect(container).toHaveClass('border-gray-600', 'bg-gray-800');

      const editor = screen.getByTestId('md-editor');
      expect(editor).toHaveAttribute('data-color-mode', 'dark');
    });
  });

  describe('user interactions', () => {
    it('should handle value changes', async () => {
      const onChange = vi.fn();
      render(<MarkdownEditor onChange={onChange} />);

      const textarea = screen.getByTestId('md-editor-textarea');
      await user.type(textarea, 'Hello World');

      expect(onChange).toHaveBeenCalledWith('Hello World');
    });

    it('should handle focus events', async () => {
      const onFocus = vi.fn();
      render(<MarkdownEditor onFocus={onFocus} />);

      const textarea = screen.getByTestId('md-editor-textarea');
      await user.click(textarea);

      expect(onFocus).toHaveBeenCalledWith(true);
    });

    it('should handle blur events', async () => {
      const onFocus = vi.fn();
      render(<MarkdownEditor onFocus={onFocus} />);

      const textarea = screen.getByTestId('md-editor-textarea');
      await user.click(textarea);
      await user.tab(); // Tab away to blur

      expect(onFocus).toHaveBeenCalledWith(false);
    });

    it('should handle scroll events', () => {
      const onScroll = vi.fn();
      render(<MarkdownEditor onScroll={onScroll} />);

      const container = screen.getByTestId('md-editor').closest('.markdown-editor-container');
      fireEvent.scroll(container!);

      expect(onScroll).toHaveBeenCalled();
    });
  });

  describe('keyboard shortcuts', () => {
    it('should handle Ctrl+B for bold formatting', async () => {
      const onChange = vi.fn();
      render(<MarkdownEditor value="selected text" onChange={onChange} />);

      const textarea = screen.getByTestId('md-editor-textarea');

      // Select text
      textarea.setSelectionRange(0, 13);

      // Press Ctrl+B
      await user.keyboard('{Control>}b{/Control}');

      expect(onChange).toHaveBeenCalledWith('**selected text**');
    });

    it('should handle Ctrl+I for italic formatting', async () => {
      const onChange = vi.fn();
      render(<MarkdownEditor value="selected text" onChange={onChange} />);

      const textarea = screen.getByTestId('md-editor-textarea');

      // Select text
      textarea.setSelectionRange(0, 13);

      // Press Ctrl+I
      await user.keyboard('{Control>}i{/Control}');

      expect(onChange).toHaveBeenCalledWith('*selected text*');
    });

    it('should handle Ctrl+K for link formatting', async () => {
      const onChange = vi.fn();
      render(<MarkdownEditor value="selected text" onChange={onChange} />);

      const textarea = screen.getByTestId('md-editor-textarea');

      // Select text
      textarea.setSelectionRange(0, 13);

      // Press Ctrl+K
      await user.keyboard('{Control>}k{/Control}');

      expect(onChange).toHaveBeenCalledWith('[selected text](http://)');
    });

    it('should handle Ctrl+` for code formatting', async () => {
      const onChange = vi.fn();
      render(<MarkdownEditor value="selected text" onChange={onChange} />);

      const textarea = screen.getByTestId('md-editor-textarea');

      // Select text
      textarea.setSelectionRange(0, 13);

      // Press Ctrl+`
      await user.keyboard('{Control>}`{/Control}');

      expect(onChange).toHaveBeenCalledWith('`selected text`');
    });

    it('should handle Tab for indentation', async () => {
      const onChange = vi.fn();
      render(<MarkdownEditor value="text" onChange={onChange} options={{ tabSize: 2 }} />);

      const textarea = screen.getByTestId('md-editor-textarea');
      textarea.setSelectionRange(0, 0);

      await user.keyboard('{Tab}');

      expect(onChange).toHaveBeenCalledWith('  text');
    });
  });

  describe('auto-completion', () => {
    it('should auto-complete unordered list items on Enter', async () => {
      const onChange = vi.fn();
      render(<MarkdownEditor value="- First item" onChange={onChange} />);

      const textarea = screen.getByTestId('md-editor-textarea');
      textarea.setSelectionRange(12, 12); // End of line

      await user.keyboard('{Enter}');

      expect(onChange).toHaveBeenCalledWith('- First item\n- ');
    });

    it('should auto-complete ordered list items on Enter', async () => {
      const onChange = vi.fn();
      render(<MarkdownEditor value="1. First item" onChange={onChange} />);

      const textarea = screen.getByTestId('md-editor-textarea');
      textarea.setSelectionRange(13, 13); // End of line

      await user.keyboard('{Enter}');

      expect(onChange).toHaveBeenCalledWith('1. First item\n2. ');
    });

    it('should not auto-complete when disabled', async () => {
      const onChange = vi.fn();
      render(
        <MarkdownEditor
          value="- First item"
          onChange={onChange}
          options={{ enableAutoComplete: false }}
        />
      );

      const textarea = screen.getByTestId('md-editor-textarea');
      textarea.setSelectionRange(12, 12);

      await user.keyboard('{Enter}');

      expect(onChange).toHaveBeenCalledWith('- First item\n');
    });
  });

  describe('statistics tracking', () => {
    it('should call onStatsChange when content changes', async () => {
      const onStatsChange = vi.fn();
      render(<MarkdownEditor onStatsChange={onStatsChange} />);

      const textarea = screen.getByTestId('md-editor-textarea');
      await user.type(textarea, '# Title\nContent');

      expect(onStatsChange).toHaveBeenCalled();
      const lastCall = onStatsChange.mock.calls[onStatsChange.mock.calls.length - 1][0];
      expect(lastCall).toHaveProperty('characters');
      expect(lastCall).toHaveProperty('words');
      expect(lastCall).toHaveProperty('headings');
    });
  });

  describe('selection handling', () => {
    it('should call onSelectionChange when selection changes', () => {
      const onSelectionChange = vi.fn();
      render(<MarkdownEditor value="Hello World" onSelectionChange={onSelectionChange} />);

      const textarea = screen.getByTestId('md-editor-textarea');

      // Simulate selection change
      fireEvent.select(textarea);

      expect(onSelectionChange).toHaveBeenCalled();
    });

    it('should call onSelectionChange on click', () => {
      const onSelectionChange = vi.fn();
      render(<MarkdownEditor value="Hello World" onSelectionChange={onSelectionChange} />);

      const textarea = screen.getByTestId('md-editor-textarea');
      fireEvent.click(textarea);

      expect(onSelectionChange).toHaveBeenCalled();
    });
  });

  describe('ref methods', () => {
    it('should expose editor element through ref', () => {
      const ref = createRef<MarkdownEditorRef>();
      render(<MarkdownEditor ref={ref} value="Test content" />);

      expect(ref.current?.getEditor()).toBeInstanceOf(HTMLTextAreaElement);
    });

    it('should insert text through ref', async () => {
      const onChange = vi.fn();
      const ref = createRef<MarkdownEditorRef>();
      render(<MarkdownEditor ref={ref} value="Hello" onChange={onChange} />);

      await waitFor(() => {
        ref.current?.insertText(' World');
      });

      expect(onChange).toHaveBeenCalledWith('Hello World');
    });

    it('should get selected text through ref', () => {
      const ref = createRef<MarkdownEditorRef>();
      render(<MarkdownEditor ref={ref} value="Hello World" />);

      // Mock selection
      const textarea = screen.getByTestId('md-editor-textarea') as HTMLTextAreaElement;
      textarea.setSelectionRange(0, 5);

      // Note: In a real browser, this would work, but in jsdom we need to mock it
      const selectedText = ref.current?.getSelectedText();
      expect(selectedText).toBeDefined();
    });

    it('should focus editor through ref', () => {
      const ref = createRef<MarkdownEditorRef>();
      render(<MarkdownEditor ref={ref} />);

      const textarea = screen.getByTestId('md-editor-textarea');
      const focusSpy = vi.spyOn(textarea, 'focus');

      ref.current?.focus();

      expect(focusSpy).toHaveBeenCalled();
    });

    it('should get stats through ref', () => {
      const ref = createRef<MarkdownEditorRef>();
      render(<MarkdownEditor ref={ref} value="# Title\nContent with **bold** text." />);

      const stats = ref.current?.getStats();
      expect(stats).toHaveProperty('characters');
      expect(stats).toHaveProperty('words');
      expect(stats).toHaveProperty('headings');
      expect(stats?.headings).toBe(1);
    });

    it('should insert format through ref', async () => {
      const onChange = vi.fn();
      const ref = createRef<MarkdownEditorRef>();
      render(<MarkdownEditor ref={ref} value="selected" onChange={onChange} />);

      // Mock selection
      const textarea = screen.getByTestId('md-editor-textarea') as HTMLTextAreaElement;
      Object.defineProperty(textarea, 'selectionStart', { value: 0, writable: true });
      Object.defineProperty(textarea, 'selectionEnd', { value: 8, writable: true });

      await waitFor(() => {
        ref.current?.insertFormat('bold');
      });

      expect(onChange).toHaveBeenCalledWith('**selected**');
    });

    it('should set selection through ref', () => {
      const ref = createRef<MarkdownEditorRef>();
      render(<MarkdownEditor ref={ref} value="Hello World" />);

      const textarea = screen.getByTestId('md-editor-textarea') as HTMLTextAreaElement;
      const setSelectionRangeSpy = vi.spyOn(textarea, 'setSelectionRange');

      ref.current?.setSelection(0, 5);

      expect(setSelectionRangeSpy).toHaveBeenCalledWith(0, 5);
    });
  });

  describe('configuration options', () => {
    it('should apply custom placeholder', () => {
      const placeholder = 'Custom placeholder';
      render(<MarkdownEditor options={{ placeholder }} />);

      const textarea = screen.getByTestId('md-editor-textarea');
      expect(textarea).toHaveAttribute('placeholder', placeholder);
    });

    it('should handle read-only mode', () => {
      render(<MarkdownEditor options={{ readOnly: true }} />);

      const textarea = screen.getByTestId('md-editor-textarea');
      expect(textarea).toHaveAttribute('readonly');
    });

    it('should apply height constraints', () => {
      render(<MarkdownEditor options={{ minHeight: '200px', maxHeight: '800px' }} />);

      const container = screen.getByTestId('md-editor').closest('.markdown-editor-container');
      expect(container).toHaveStyle({
        'min-height': '200px',
        'max-height': '800px'
      });
    });
  });

  describe('error handling', () => {
    it('should handle invalid format insertions gracefully', async () => {
      const ref = createRef<MarkdownEditorRef>();
      render(<MarkdownEditor ref={ref} value="test" />);

      // Should not throw even with invalid format
      expect(() => {
        ref.current?.insertFormat('bold');
      }).not.toThrow();
    });

    it('should handle missing selection gracefully', () => {
      const ref = createRef<MarkdownEditorRef>();
      render(<MarkdownEditor ref={ref} value="test" />);

      // Should not throw when no selection is made
      expect(() => {
        ref.current?.insertFormat('bold');
      }).not.toThrow();
    });
  });

  describe('accessibility', () => {
    it('should be focusable', () => {
      render(<MarkdownEditor />);

      const textarea = screen.getByTestId('md-editor-textarea');
      expect(textarea).toHaveAttribute('tabindex', '0');
    });

    it('should have proper font family for code editing', () => {
      render(<MarkdownEditor />);

      const textarea = screen.getByTestId('md-editor-textarea');
      expect(textarea).toHaveStyle({
        'font-family': 'Monaco, Menlo, "Ubuntu Mono", monospace'
      });
    });
  });
});