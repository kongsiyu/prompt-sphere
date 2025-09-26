/**
 * 自动保存钩子
 * 提供防抖的自动保存功能，支持本地存储和远程保存
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { debounce } from '../utils/markdown';

/**
 * 自动保存配置选项
 */
export interface AutoSaveOptions {
  /** 自动保存延迟时间（毫秒），默认 3000 */
  delay?: number;
  /** 是否启用自动保存，默认 true */
  enabled?: boolean;
  /** 保存函数，返回 Promise 表示保存操作 */
  onSave?: (data: any) => Promise<void>;
  /** 本地存储键名，用于本地备份 */
  storageKey?: string;
  /** 是否启用本地存储，默认 true */
  enableLocalStorage?: boolean;
  /** 保存成功回调 */
  onSaveSuccess?: (data: any) => void;
  /** 保存失败回调 */
  onSaveError?: (error: Error, data: any) => void;
  /** 数据序列化函数，默认使用 JSON.stringify */
  serialize?: (data: any) => string;
  /** 数据反序列化函数，默认使用 JSON.parse */
  deserialize?: (data: string) => any;
}

/**
 * 自动保存状态
 */
export interface AutoSaveState {
  /** 是否正在保存 */
  isSaving: boolean;
  /** 是否有未保存的更改 */
  hasUnsavedChanges: boolean;
  /** 最后保存时间 */
  lastSavedAt: Date | null;
  /** 最后保存的数据 */
  lastSavedData: any;
  /** 保存错误信息 */
  saveError: Error | null;
}

/**
 * 默认序列化函数
 */
const defaultSerialize = (data: any): string => {
  try {
    return JSON.stringify(data);
  } catch (error) {
    console.warn('序列化数据失败:', error);
    return '';
  }
};

/**
 * 默认反序列化函数
 */
const defaultDeserialize = (data: string): any => {
  try {
    return JSON.parse(data);
  } catch (error) {
    console.warn('反序列化数据失败:', error);
    return null;
  }
};

/**
 * 自动保存钩子
 *
 * @param data - 要保存的数据
 * @param options - 自动保存配置选项
 * @returns 自动保存状态和控制函数
 */
export function useAutoSave<T = any>(
  data: T,
  options: AutoSaveOptions = {}
) {
  const {
    delay = 3000,
    enabled = true,
    onSave,
    storageKey,
    enableLocalStorage = true,
    onSaveSuccess,
    onSaveError,
    serialize = defaultSerialize,
    deserialize = defaultDeserialize,
  } = options;

  const [state, setState] = useState<AutoSaveState>({
    isSaving: false,
    hasUnsavedChanges: false,
    lastSavedAt: null,
    lastSavedData: null,
    saveError: null,
  });

  // 使用 ref 来存储最新的状态，避免闭包问题
  const stateRef = useRef(state);
  const dataRef = useRef<T>(data);
  const lastSavedDataRef = useRef<T | null>(null);

  // 更新 ref
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  useEffect(() => {
    dataRef.current = data;
  }, [data]);

  /**
   * 保存到本地存储
   */
  const saveToLocalStorage = useCallback((saveData: T): void => {
    if (!enableLocalStorage || !storageKey) {
      return;
    }

    try {
      const serializedData = serialize(saveData);
      localStorage.setItem(storageKey, serializedData);
      localStorage.setItem(`${storageKey}_timestamp`, Date.now().toString());
    } catch (error) {
      console.warn('保存到本地存储失败:', error);
    }
  }, [enableLocalStorage, storageKey, serialize]);

  /**
   * 从本地存储恢复数据
   */
  const restoreFromLocalStorage = useCallback((): T | null => {
    if (!enableLocalStorage || !storageKey) {
      return null;
    }

    try {
      const storedData = localStorage.getItem(storageKey);
      if (!storedData) {
        return null;
      }

      return deserialize(storedData);
    } catch (error) {
      console.warn('从本地存储恢复数据失败:', error);
      return null;
    }
  }, [enableLocalStorage, storageKey, deserialize]);

  /**
   * 获取本地存储的时间戳
   */
  const getLocalStorageTimestamp = useCallback((): number | null => {
    if (!enableLocalStorage || !storageKey) {
      return null;
    }

    try {
      const timestamp = localStorage.getItem(`${storageKey}_timestamp`);
      return timestamp ? parseInt(timestamp, 10) : null;
    } catch (error) {
      console.warn('获取本地存储时间戳失败:', error);
      return null;
    }
  }, [enableLocalStorage, storageKey]);

  /**
   * 执行保存操作
   */
  const performSave = useCallback(async (saveData: T): Promise<void> => {
    setState(prev => ({
      ...prev,
      isSaving: true,
      saveError: null,
    }));

    try {
      // 保存到本地存储（作为备份）
      saveToLocalStorage(saveData);

      // 如果有远程保存函数，执行远程保存
      if (onSave) {
        await onSave(saveData);
      }

      // 保存成功
      const now = new Date();
      setState(prev => ({
        ...prev,
        isSaving: false,
        hasUnsavedChanges: false,
        lastSavedAt: now,
        lastSavedData: saveData,
        saveError: null,
      }));

      lastSavedDataRef.current = saveData;

      // 调用成功回调
      onSaveSuccess?.(saveData);
    } catch (error) {
      const saveError = error instanceof Error ? error : new Error('保存失败');

      setState(prev => ({
        ...prev,
        isSaving: false,
        saveError,
      }));

      // 调用错误回调
      onSaveError?.(saveError, saveData);
    }
  }, [onSave, saveToLocalStorage, onSaveSuccess, onSaveError]);

  /**
   * 防抖的保存函数
   */
  const debouncedSave = useCallback(
    debounce((saveData: T) => {
      performSave(saveData);
    }, delay),
    [performSave, delay]
  );

  /**
   * 立即保存函数
   */
  const saveNow = useCallback(async (): Promise<void> => {
    const currentData = dataRef.current;
    await performSave(currentData);
  }, [performSave]);

  /**
   * 重置保存状态
   */
  const resetSaveState = useCallback((): void => {
    setState(prev => ({
      ...prev,
      hasUnsavedChanges: false,
      saveError: null,
    }));
  }, []);

  /**
   * 清除本地存储
   */
  const clearLocalStorage = useCallback((): void => {
    if (!enableLocalStorage || !storageKey) {
      return;
    }

    try {
      localStorage.removeItem(storageKey);
      localStorage.removeItem(`${storageKey}_timestamp`);
    } catch (error) {
      console.warn('清除本地存储失败:', error);
    }
  }, [enableLocalStorage, storageKey]);

  // 监听数据变化，触发自动保存
  useEffect(() => {
    if (!enabled) {
      return;
    }

    // 检查数据是否真的发生了变化
    const hasChanged = lastSavedDataRef.current === null ||
      serialize(data) !== serialize(lastSavedDataRef.current);

    if (hasChanged && !state.isSaving) {
      setState(prev => ({
        ...prev,
        hasUnsavedChanges: true,
      }));

      // 触发防抖保存
      debouncedSave(data);
    }
  }, [data, enabled, serialize, debouncedSave, state.isSaving]);

  // 组件卸载时尝试保存未保存的更改
  useEffect(() => {
    return () => {
      if (stateRef.current.hasUnsavedChanges && !stateRef.current.isSaving) {
        // 同步保存到本地存储
        if (enableLocalStorage && storageKey) {
          try {
            const serializedData = serialize(dataRef.current);
            localStorage.setItem(storageKey, serializedData);
            localStorage.setItem(`${storageKey}_timestamp`, Date.now().toString());
          } catch (error) {
            console.warn('组件卸载时保存到本地存储失败:', error);
          }
        }
      }
    };
  }, [enableLocalStorage, storageKey, serialize]);

  // 监听页面关闭事件，尝试保存
  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (stateRef.current.hasUnsavedChanges) {
        event.preventDefault();
        event.returnValue = '您有未保存的更改，确定要离开吗？';
        return '您有未保存的更改，确定要离开吗？';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  return {
    ...state,
    saveNow,
    resetSaveState,
    restoreFromLocalStorage,
    getLocalStorageTimestamp,
    clearLocalStorage,
  };
}