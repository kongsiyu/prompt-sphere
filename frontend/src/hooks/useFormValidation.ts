/**
 * 表单验证钩子
 * 提供通用的表单验证逻辑
 */

import { useState, useCallback, useMemo } from 'react';
import { ValidationRule, PromptFormData } from '@/types/prompt';

export interface UseFormValidationOptions {
  /** 验证规则配置 */
  validationRules: Record<keyof PromptFormData, ValidationRule[]>;
  /** 是否在值改变时立即验证 */
  validateOnChange?: boolean;
  /** 是否在失去焦点时验证 */
  validateOnBlur?: boolean;
}

export interface FormErrors {
  [key: string]: string | undefined;
}

/**
 * 验证单个字段的值
 */
const validateField = (value: any, rules: ValidationRule[]): string | undefined => {
  for (const rule of rules) {
    switch (rule.type) {
      case 'required':
        if (value === undefined || value === null || value === '') {
          return rule.message;
        }
        if (Array.isArray(value) && value.length === 0) {
          return rule.message;
        }
        break;

      case 'minLength':
        if (typeof value === 'string' && value.length < rule.value) {
          return rule.message;
        }
        if (Array.isArray(value) && value.length < rule.value) {
          return rule.message;
        }
        break;

      case 'maxLength':
        if (typeof value === 'string' && value.length > rule.value) {
          return rule.message;
        }
        if (Array.isArray(value) && value.length > rule.value) {
          return rule.message;
        }
        break;

      case 'pattern':
        if (typeof value === 'string' && rule.value instanceof RegExp && !rule.value.test(value)) {
          return rule.message;
        }
        break;

      case 'custom':
        if (rule.validator && !rule.validator(value)) {
          return rule.message;
        }
        break;

      default:
        break;
    }
  }

  return undefined;
};

/**
 * 表单验证钩子
 *
 * @example
 * ```tsx
 * const validationRules: Record<keyof PromptFormData, ValidationRule[]> = {
 *   title: [
 *     { type: 'required', message: '标题不能为空' },
 *     { type: 'maxLength', value: 100, message: '标题不能超过100个字符' }
 *   ],
 *   role: [
 *     { type: 'required', message: '角色不能为空' }
 *   ],
 *   // ... 其他字段
 * };
 *
 * const {
 *   errors,
 *   validateField,
 *   validateForm,
 *   clearErrors,
 *   hasErrors,
 *   isValid
 * } = useFormValidation({ validationRules });
 * ```
 */
export const useFormValidation = ({
  validationRules,
  validateOnChange = false,
  validateOnBlur = true,
}: UseFormValidationOptions) => {
  const [errors, setErrors] = useState<FormErrors>({});
  const [touchedFields, setTouchedFields] = useState<Set<string>>(new Set());

  // 验证单个字段
  const validateSingleField = useCallback((fieldName: keyof PromptFormData, value: any): string | undefined => {
    const rules = validationRules[fieldName];
    if (!rules) return undefined;

    return validateField(value, rules);
  }, [validationRules]);

  // 验证并设置字段错误
  const validateAndSetFieldError = useCallback((fieldName: keyof PromptFormData, value: any): boolean => {
    const error = validateSingleField(fieldName, value);

    setErrors(prev => ({
      ...prev,
      [fieldName]: error,
    }));

    return !error;
  }, [validateSingleField]);

  // 验证整个表单
  const validateForm = useCallback((formData: Partial<PromptFormData>): boolean => {
    const newErrors: FormErrors = {};
    let isFormValid = true;

    Object.keys(validationRules).forEach((fieldName) => {
      const value = formData[fieldName as keyof PromptFormData];
      const error = validateSingleField(fieldName as keyof PromptFormData, value);

      if (error) {
        newErrors[fieldName] = error;
        isFormValid = false;
      }
    });

    setErrors(newErrors);
    return isFormValid;
  }, [validationRules, validateSingleField]);

  // 处理字段值变化
  const handleFieldChange = useCallback((fieldName: keyof PromptFormData, value: any) => {
    // 标记字段为已触摸
    setTouchedFields(prev => new Set(prev).add(fieldName));

    // 如果启用了实时验证，立即验证字段
    if (validateOnChange) {
      validateAndSetFieldError(fieldName, value);
    } else {
      // 如果字段之前有错误，清除错误
      if (errors[fieldName]) {
        setErrors(prev => ({
          ...prev,
          [fieldName]: undefined,
        }));
      }
    }
  }, [validateOnChange, validateAndSetFieldError, errors]);

  // 处理字段失去焦点
  const handleFieldBlur = useCallback((fieldName: keyof PromptFormData, value: any) => {
    setTouchedFields(prev => new Set(prev).add(fieldName));

    if (validateOnBlur) {
      validateAndSetFieldError(fieldName, value);
    }
  }, [validateOnBlur, validateAndSetFieldError]);

  // 清除错误
  const clearErrors = useCallback((fieldNames?: (keyof PromptFormData)[]) => {
    if (fieldNames) {
      setErrors(prev => {
        const newErrors = { ...prev };
        fieldNames.forEach(fieldName => {
          delete newErrors[fieldName];
        });
        return newErrors;
      });
    } else {
      setErrors({});
      setTouchedFields(new Set());
    }
  }, []);

  // 设置特定字段的错误
  const setFieldError = useCallback((fieldName: keyof PromptFormData, error: string | undefined) => {
    setErrors(prev => ({
      ...prev,
      [fieldName]: error,
    }));
  }, []);

  // 检查是否有错误
  const hasErrors = useMemo(() => {
    return Object.values(errors).some(error => error !== undefined);
  }, [errors]);

  // 检查表单是否有效（所有必填字段都已填写且无错误）
  const isValid = useMemo(() => {
    return !hasErrors;
  }, [hasErrors]);

  // 获取字段错误（只有在字段被触摸后才显示错误）
  const getFieldError = useCallback((fieldName: keyof PromptFormData): string | undefined => {
    const isTouched = touchedFields.has(fieldName);
    return isTouched ? errors[fieldName] : undefined;
  }, [errors, touchedFields]);

  // 检查字段是否被触摸
  const isFieldTouched = useCallback((fieldName: keyof PromptFormData): boolean => {
    return touchedFields.has(fieldName);
  }, [touchedFields]);

  // 重置表单验证状态
  const resetValidation = useCallback(() => {
    setErrors({});
    setTouchedFields(new Set());
  }, []);

  return {
    errors,
    touchedFields,
    validateField: validateAndSetFieldError,
    validateForm,
    clearErrors,
    setFieldError,
    handleFieldChange,
    handleFieldBlur,
    getFieldError,
    isFieldTouched,
    resetValidation,
    hasErrors,
    isValid,
  };
};

export default useFormValidation;

/**
 * 预定义的提示词表单验证规则
 */
export const defaultPromptValidationRules: Record<keyof PromptFormData, ValidationRule[]> = {
  title: [
    { type: 'required', message: '标题不能为空' },
    { type: 'minLength', value: 2, message: '标题至少需要2个字符' },
    { type: 'maxLength', value: 100, message: '标题不能超过100个字符' },
  ],
  description: [
    { type: 'required', message: '描述不能为空' },
    { type: 'minLength', value: 10, message: '描述至少需要10个字符' },
    { type: 'maxLength', value: 500, message: '描述不能超过500个字符' },
  ],
  role: [
    { type: 'required', message: '角色定义不能为空' },
    { type: 'minLength', value: 5, message: '角色定义至少需要5个字符' },
    { type: 'maxLength', value: 200, message: '角色定义不能超过200个字符' },
  ],
  tone: [
    { type: 'required', message: '语调风格不能为空' },
    { type: 'minLength', value: 2, message: '语调风格至少需要2个字符' },
    { type: 'maxLength', value: 100, message: '语调风格不能超过100个字符' },
  ],
  capabilities: [
    { type: 'required', message: '能力描述不能为空' },
    {
      type: 'custom',
      message: '至少需要添加1个能力',
      validator: (value: string[]) => Array.isArray(value) && value.length > 0,
    },
    {
      type: 'custom',
      message: '最多可以添加10个能力',
      validator: (value: string[]) => Array.isArray(value) && value.length <= 10,
    },
  ],
  constraints: [
    {
      type: 'custom',
      message: '最多可以添加10个约束',
      validator: (value: string[]) => !value || value.length <= 10,
    },
  ],
  content: [
    { type: 'required', message: '提示词内容不能为空' },
    { type: 'minLength', value: 20, message: '提示词内容至少需要20个字符' },
    { type: 'maxLength', value: 10000, message: '提示词内容不能超过10000个字符' },
  ],
  tags: [
    {
      type: 'custom',
      message: '最多可以添加20个标签',
      validator: (value: string[]) => !value || value.length <= 20,
    },
  ],
  language: [],
  isTemplate: [],
};