/**
 * useAutoSave 钩子测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAutoSave } from '../useAutoSave';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    length: 0,
    key: () => null,
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('useAutoSave', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('basic functionality', () => {
    it('should initialize with correct default state', () => {
      const { result } = renderHook(() => useAutoSave('initial data'));

      expect(result.current.isSaving).toBe(false);
      expect(result.current.hasUnsavedChanges).toBe(false);
      expect(result.current.lastSavedAt).toBeNull();
      expect(result.current.lastSavedData).toBeNull();
      expect(result.current.saveError).toBeNull();
    });

    it('should detect unsaved changes when data changes', async () => {
      const { result, rerender } = renderHook(
        ({ data }) => useAutoSave(data),
        { initialProps: { data: 'initial' } }
      );

      expect(result.current.hasUnsavedChanges).toBe(false);

      rerender({ data: 'changed' });

      await act(async () => {
        await vi.runOnlyPendingTimersAsync();
      });

      expect(result.current.hasUnsavedChanges).toBe(true);
    });

    it('should call onSave after delay when data changes', async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);
      const delay = 1000;

      const { rerender } = renderHook(
        ({ data }) => useAutoSave(data, { onSave, delay }),
        { initialProps: { data: 'initial' } }
      );

      rerender({ data: 'changed' });

      // Should not save immediately
      expect(onSave).not.toHaveBeenCalled();

      // Should save after delay
      await act(async () => {
        vi.advanceTimersByTime(delay);
        await vi.runOnlyPendingTimersAsync();
      });

      expect(onSave).toHaveBeenCalledWith('changed');
    });

    it('should reset unsaved changes after successful save', async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);

      const { result, rerender } = renderHook(
        ({ data }) => useAutoSave(data, { onSave, delay: 100 }),
        { initialProps: { data: 'initial' } }
      );

      rerender({ data: 'changed' });

      await act(async () => {
        vi.advanceTimersByTime(100);
        await vi.runOnlyPendingTimersAsync();
      });

      expect(result.current.hasUnsavedChanges).toBe(false);
      expect(result.current.lastSavedData).toBe('changed');
      expect(result.current.lastSavedAt).toBeInstanceOf(Date);
    });
  });

  describe('error handling', () => {
    it('should handle save errors correctly', async () => {
      const saveError = new Error('Save failed');
      const onSave = vi.fn().mockRejectedValue(saveError);
      const onSaveError = vi.fn();

      const { result, rerender } = renderHook(
        ({ data }) => useAutoSave(data, { onSave, onSaveError, delay: 100 }),
        { initialProps: { data: 'initial' } }
      );

      rerender({ data: 'changed' });

      await act(async () => {
        vi.advanceTimersByTime(100);
        await vi.runOnlyPendingTimersAsync();
      });

      expect(result.current.saveError).toBe(saveError);
      expect(result.current.hasUnsavedChanges).toBe(true); // Should remain true on error
      expect(onSaveError).toHaveBeenCalledWith(saveError, 'changed');
    });

    it('should handle non-Error objects as save errors', async () => {
      const onSave = vi.fn().mockRejectedValue('String error');

      const { result, rerender } = renderHook(
        ({ data }) => useAutoSave(data, { onSave, delay: 100 }),
        { initialProps: { data: 'initial' } }
      );

      rerender({ data: 'changed' });

      await act(async () => {
        vi.advanceTimersByTime(100);
        await vi.runOnlyPendingTimersAsync();
      });

      expect(result.current.saveError).toBeInstanceOf(Error);
      expect(result.current.saveError?.message).toBe('保存失败');
    });
  });

  describe('local storage functionality', () => {
    it('should save to local storage when enabled', async () => {
      const storageKey = 'test-key';
      const onSave = vi.fn().mockResolvedValue(undefined);

      const { rerender } = renderHook(
        ({ data }) => useAutoSave(data, {
          onSave,
          storageKey,
          enableLocalStorage: true,
          delay: 100
        }),
        { initialProps: { data: 'initial' } }
      );

      rerender({ data: 'changed' });

      await act(async () => {
        vi.advanceTimersByTime(100);
        await vi.runOnlyPendingTimersAsync();
      });

      expect(localStorageMock.getItem(storageKey)).toBe('"changed"');
      expect(localStorageMock.getItem(`${storageKey}_timestamp`)).toBeTruthy();
    });

    it('should restore from local storage', () => {
      const storageKey = 'test-key';
      localStorageMock.setItem(storageKey, '"stored data"');

      const { result } = renderHook(() =>
        useAutoSave('initial', { storageKey, enableLocalStorage: true })
      );

      const restored = result.current.restoreFromLocalStorage();
      expect(restored).toBe('stored data');
    });

    it('should handle local storage serialization errors gracefully', () => {
      const storageKey = 'test-key';

      const { result } = renderHook(() =>
        useAutoSave('initial', {
          storageKey,
          enableLocalStorage: true,
          serialize: () => { throw new Error('Serialization error'); }
        })
      );

      // Should not throw and should handle the error gracefully
      expect(() => result.current.restoreFromLocalStorage()).not.toThrow();
    });

    it('should clear local storage when requested', () => {
      const storageKey = 'test-key';
      localStorageMock.setItem(storageKey, '"test data"');
      localStorageMock.setItem(`${storageKey}_timestamp`, '123456789');

      const { result } = renderHook(() =>
        useAutoSave('initial', { storageKey, enableLocalStorage: true })
      );

      act(() => {
        result.current.clearLocalStorage();
      });

      expect(localStorageMock.getItem(storageKey)).toBeNull();
      expect(localStorageMock.getItem(`${storageKey}_timestamp`)).toBeNull();
    });
  });

  describe('manual save functionality', () => {
    it('should save immediately when saveNow is called', async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);

      const { result } = renderHook(() =>
        useAutoSave('test data', { onSave })
      );

      await act(async () => {
        await result.current.saveNow();
      });

      expect(onSave).toHaveBeenCalledWith('test data');
      expect(result.current.lastSavedData).toBe('test data');
    });

    it('should reset save state when requested', () => {
      const { result } = renderHook(() =>
        useAutoSave('initial', {}, )
      );

      // Simulate an error state
      act(() => {
        // This would normally be set internally, but we'll test the reset functionality
        result.current.resetSaveState();
      });

      expect(result.current.hasUnsavedChanges).toBe(false);
      expect(result.current.saveError).toBeNull();
    });
  });

  describe('debouncing behavior', () => {
    it('should debounce multiple rapid changes', async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);
      const delay = 1000;

      const { rerender } = renderHook(
        ({ data }) => useAutoSave(data, { onSave, delay }),
        { initialProps: { data: 'initial' } }
      );

      // Make multiple rapid changes
      rerender({ data: 'change1' });
      vi.advanceTimersByTime(500);
      rerender({ data: 'change2' });
      vi.advanceTimersByTime(500);
      rerender({ data: 'change3' });

      // Should not have saved yet
      expect(onSave).not.toHaveBeenCalled();

      // Should save only the final change after full delay
      await act(async () => {
        vi.advanceTimersByTime(delay);
        await vi.runOnlyPendingTimersAsync();
      });

      expect(onSave).toHaveBeenCalledTimes(1);
      expect(onSave).toHaveBeenCalledWith('change3');
    });
  });

  describe('configuration options', () => {
    it('should respect the enabled option', async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);

      const { rerender } = renderHook(
        ({ data }) => useAutoSave(data, { onSave, enabled: false, delay: 100 }),
        { initialProps: { data: 'initial' } }
      );

      rerender({ data: 'changed' });

      await act(async () => {
        vi.advanceTimersByTime(100);
        await vi.runOnlyPendingTimersAsync();
      });

      expect(onSave).not.toHaveBeenCalled();
    });

    it('should use custom serialization functions', async () => {
      const serialize = vi.fn((data) => `custom:${data}`);
      const deserialize = vi.fn((data) => data.replace('custom:', ''));
      const storageKey = 'test-key';
      const onSave = vi.fn().mockResolvedValue(undefined);

      const { rerender } = renderHook(
        ({ data }) => useAutoSave(data, {
          onSave,
          storageKey,
          enableLocalStorage: true,
          serialize,
          deserialize,
          delay: 100
        }),
        { initialProps: { data: 'initial' } }
      );

      rerender({ data: 'changed' });

      await act(async () => {
        vi.advanceTimersByTime(100);
        await vi.runOnlyPendingTimersAsync();
      });

      expect(serialize).toHaveBeenCalledWith('changed');
      expect(localStorageMock.getItem(storageKey)).toBe('custom:changed');
    });

    it('should call success callback on successful save', async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);
      const onSaveSuccess = vi.fn();

      const { rerender } = renderHook(
        ({ data }) => useAutoSave(data, { onSave, onSaveSuccess, delay: 100 }),
        { initialProps: { data: 'initial' } }
      );

      rerender({ data: 'changed' });

      await act(async () => {
        vi.advanceTimersByTime(100);
        await vi.runOnlyPendingTimersAsync();
      });

      expect(onSaveSuccess).toHaveBeenCalledWith('changed');
    });
  });

  describe('performance and edge cases', () => {
    it('should not save when data has not actually changed', async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);

      const { result, rerender } = renderHook(
        ({ data }) => useAutoSave(data, { onSave, delay: 100 }),
        { initialProps: { data: 'initial' } }
      );

      // First change and save
      rerender({ data: 'changed' });

      await act(async () => {
        vi.advanceTimersByTime(100);
        await vi.runOnlyPendingTimersAsync();
      });

      expect(onSave).toHaveBeenCalledTimes(1);

      // Rerender with same data - should not trigger save
      rerender({ data: 'changed' });

      await act(async () => {
        vi.advanceTimersByTime(100);
        await vi.runOnlyPendingTimersAsync();
      });

      expect(onSave).toHaveBeenCalledTimes(1); // Still only 1 call
      expect(result.current.hasUnsavedChanges).toBe(false);
    });

    it('should handle saving state correctly during async operations', async () => {
      let resolvePromise: (value?: unknown) => void;
      const savePromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      const onSave = vi.fn().mockReturnValue(savePromise);

      const { result, rerender } = renderHook(
        ({ data }) => useAutoSave(data, { onSave, delay: 100 }),
        { initialProps: { data: 'initial' } }
      );

      rerender({ data: 'changed' });

      await act(async () => {
        vi.advanceTimersByTime(100);
        await vi.runOnlyPendingTimersAsync();
      });

      expect(result.current.isSaving).toBe(true);

      await act(async () => {
        resolvePromise!();
        await savePromise;
      });

      expect(result.current.isSaving).toBe(false);
    });
  });
});