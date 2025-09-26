/**
 * 通用表单字段组件
 * 支持多种字段类型、验证、标签和帮助文本
 */

import React, { forwardRef, useState } from 'react';
import { cn } from '@/utils/cn';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { X, Plus, ChevronDown } from 'lucide-react';
import { FormFieldConfig, ValidationRule } from '@/types/prompt';

interface FormFieldProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange'> {
  /** 字段配置 */
  config: FormFieldConfig;
  /** 字段值 */
  value: any;
  /** 值变化回调 */
  onChange: (value: any) => void;
  /** 错误信息 */
  error?: string;
  /** 是否禁用 */
  disabled?: boolean;
  /** 容器样式类名 */
  containerClassName?: string;
}

/**
 * TagsInput 标签输入组件
 */
const TagsInput: React.FC<{
  value: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  disabled?: boolean;
  maxLength?: number;
  className?: string;
}> = ({ value = [], onChange, placeholder, disabled, maxLength, className }) => {
  const [inputValue, setInputValue] = useState('');

  const addTag = (tag: string) => {
    const trimmedTag = tag.trim();
    if (trimmedTag && !value.includes(trimmedTag)) {
      const newTags = [...value, trimmedTag];
      if (!maxLength || newTags.length <= maxLength) {
        onChange(newTags);
      }
    }
    setInputValue('');
  };

  const removeTag = (tagToRemove: string) => {
    onChange(value.filter(tag => tag !== tagToRemove));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      if (inputValue.trim()) {
        addTag(inputValue);
      }
    } else if (e.key === 'Backspace' && !inputValue && value.length > 0) {
      removeTag(value[value.length - 1]);
    }
  };

  return (
    <div className={cn('w-full', className)}>
      <div className="flex flex-wrap gap-2 mb-2">
        {value.map((tag, index) => (
          <div
            key={index}
            className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-sm"
          >
            <span>{tag}</span>
            {!disabled && (
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="hover:text-blue-600 transition-colors"
                aria-label={`删除标签 ${tag}`}
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        ))}
      </div>
      <Input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full"
      />
      <p className="text-xs text-muted-foreground mt-1">
        按回车键或逗号添加标签{maxLength && ` (最多${maxLength}个)`}
      </p>
    </div>
  );
};

/**
 * MultiSelect 多选组件
 */
const MultiSelect: React.FC<{
  value: string[];
  onChange: (values: string[]) => void;
  options: Array<{ value: string; label: string }>;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}> = ({ value = [], onChange, options, placeholder, disabled, className }) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleOption = (optionValue: string) => {
    if (value.includes(optionValue)) {
      onChange(value.filter(v => v !== optionValue));
    } else {
      onChange([...value, optionValue]);
    }
  };

  const selectedLabels = options
    .filter(option => value.includes(option.value))
    .map(option => option.label)
    .join(', ');

  return (
    <div className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          'flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm',
          'justify-between items-center',
          'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-0',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'hover:bg-accent hover:text-accent-foreground transition-colors'
        )}
      >
        <span className={cn('truncate', !selectedLabels && 'text-muted-foreground')}>
          {selectedLabels || placeholder}
        </span>
        <ChevronDown className={cn('h-4 w-4 transition-transform', isOpen && 'rotate-180')} />
      </button>

      {isOpen && (
        <>
          {/* 遮罩层 */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          {/* 选项下拉框 */}
          <div className="absolute top-full left-0 right-0 z-20 mt-1 bg-background border border-input rounded-md shadow-lg max-h-60 overflow-y-auto">
            {options.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => toggleOption(option.value)}
                className={cn(
                  'w-full px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground',
                  'transition-colors flex items-center justify-between',
                  value.includes(option.value) && 'bg-primary/10 text-primary'
                )}
              >
                <span>{option.label}</span>
                {value.includes(option.value) && (
                  <div className="w-4 h-4 rounded bg-primary flex items-center justify-center">
                    <svg className="w-3 h-3 text-primary-foreground" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

/**
 * FormField 通用表单字段组件
 *
 * @example
 * ```tsx
 * <FormField
 *   config={{
 *     name: 'title',
 *     label: '标题',
 *     type: 'text',
 *     placeholder: '请输入标题',
 *     required: true
 *   }}
 *   value={formData.title}
 *   onChange={(value) => setFormData({ ...formData, title: value })}
 * />
 * ```
 */
export const FormField = forwardRef<HTMLDivElement, FormFieldProps>(
  ({ config, value, onChange, error, disabled = false, containerClassName, className, ...props }, ref) => {
    const {
      name,
      label,
      type,
      placeholder,
      helpText,
      required,
      options = [],
      maxLength,
      minLength,
      rows = 3,
    } = config;

    const fieldId = `field-${name}`;
    const isDisabled = disabled || config.disabled;

    // 渲染不同类型的表单字段
    const renderField = () => {
      switch (type) {
        case 'textarea':
          return (
            <textarea
              id={fieldId}
              value={value || ''}
              onChange={(e) => onChange(e.target.value)}
              placeholder={placeholder}
              disabled={isDisabled}
              rows={rows}
              maxLength={maxLength}
              minLength={minLength}
              className={cn(
                'flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm',
                'transition-all duration-200 resize-y',
                'placeholder:text-muted-foreground',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-0',
                'disabled:cursor-not-allowed disabled:opacity-50',
                error && 'border-red-500 focus-visible:ring-red-500',
                className
              )}
              {...(props as any)}
            />
          );

        case 'tags':
          return (
            <TagsInput
              value={value || []}
              onChange={onChange}
              placeholder={placeholder}
              disabled={isDisabled}
              maxLength={maxLength}
              className={className}
            />
          );

        case 'select':
          return (
            <select
              id={fieldId}
              value={value || ''}
              onChange={(e) => onChange(e.target.value)}
              disabled={isDisabled}
              className={cn(
                'flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-0',
                'disabled:cursor-not-allowed disabled:opacity-50',
                error && 'border-red-500 focus-visible:ring-red-500',
                className
              )}
            >
              <option value="">{placeholder}</option>
              {options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          );

        case 'multiselect':
          return (
            <MultiSelect
              value={value || []}
              onChange={onChange}
              options={options}
              placeholder={placeholder}
              disabled={isDisabled}
              className={className}
            />
          );

        case 'text':
        default:
          return (
            <Input
              id={fieldId}
              type="text"
              value={value || ''}
              onChange={(e) => onChange(e.target.value)}
              placeholder={placeholder}
              disabled={isDisabled}
              maxLength={maxLength}
              status={error ? 'error' : 'default'}
              className={className}
              {...(props as any)}
            />
          );
      }
    };

    return (
      <div ref={ref} className={cn('w-full', containerClassName)}>
        {/* 字段标签 */}
        {label && (
          <label
            htmlFor={fieldId}
            className="mb-1.5 block text-sm font-medium text-foreground"
          >
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}

        {/* 字段输入 */}
        {renderField()}

        {/* 帮助文本和错误信息 */}
        {(helpText || error) && (
          <div className="mt-1.5 space-y-1">
            {error && (
              <p className="text-xs text-red-500">{error}</p>
            )}
            {helpText && !error && (
              <p className="text-xs text-muted-foreground">{helpText}</p>
            )}
          </div>
        )}

        {/* 字符计数（适用于文本类型字段） */}
        {(type === 'text' || type === 'textarea') && maxLength && (
          <p className="mt-1 text-xs text-muted-foreground text-right">
            {String(value || '').length}/{maxLength}
          </p>
        )}
      </div>
    );
  }
);

FormField.displayName = 'FormField';

export default FormField;