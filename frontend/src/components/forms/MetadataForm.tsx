/**
 * 元数据表单组件
 * 包含角色、语调、能力、约束等提示词元数据字段
 */

import React, { useMemo } from 'react';
import { cn } from '@/utils/cn';
import { FormField } from './FormField';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { PromptFormData, FormFieldConfig } from '@/types/prompt';
import { useFormValidation, defaultPromptValidationRules } from '@/hooks/useFormValidation';
import { Save, RotateCcw, FileText } from 'lucide-react';

interface MetadataFormProps {
  /** 表单数据 */
  formData: Partial<PromptFormData>;
  /** 表单数据变化回调 */
  onChange: (data: Partial<PromptFormData>) => void;
  /** 保存回调 */
  onSave?: () => void;
  /** 重置回调 */
  onReset?: () => void;
  /** 是否只读 */
  readonly?: boolean;
  /** 是否显示保存按钮 */
  showSaveButton?: boolean;
  /** 是否显示重置按钮 */
  showResetButton?: boolean;
  /** 容器样式类名 */
  className?: string;
  /** 是否正在保存 */
  saving?: boolean;
  /** 自动保存状态 */
  autoSaveStatus?: 'saved' | 'saving' | 'dirty' | 'error';
}

// 预定义的语调选项
const toneOptions = [
  { value: 'professional', label: '专业的' },
  { value: 'friendly', label: '友好的' },
  { value: 'formal', label: '正式的' },
  { value: 'casual', label: '随意的' },
  { value: 'authoritative', label: '权威的' },
  { value: 'empathetic', label: '理解的' },
  { value: 'enthusiastic', label: '热情的' },
  { value: 'analytical', label: '分析性的' },
  { value: 'creative', label: '创造性的' },
  { value: 'supportive', label: '支持的' },
];

// 预定义的语言选项
const languageOptions = [
  { value: 'zh', label: '中文' },
  { value: 'en', label: 'English' },
];

/**
 * MetadataForm 元数据表单组件
 *
 * @example
 * ```tsx
 * <MetadataForm
 *   formData={promptData}
 *   onChange={setPromptData}
 *   onSave={handleSave}
 *   showSaveButton
 *   showResetButton
 * />
 * ```
 */
export const MetadataForm: React.FC<MetadataFormProps> = ({
  formData,
  onChange,
  onSave,
  onReset,
  readonly = false,
  showSaveButton = true,
  showResetButton = true,
  className,
  saving = false,
  autoSaveStatus = 'saved',
}) => {
  // 表单验证
  const {
    getFieldError,
    handleFieldChange,
    handleFieldBlur,
    validateForm,
    hasErrors,
  } = useFormValidation({
    validationRules: defaultPromptValidationRules,
    validateOnChange: false,
    validateOnBlur: true,
  });

  // 表单字段配置
  const fieldConfigs: FormFieldConfig[] = useMemo(() => [
    {
      name: 'title',
      label: '标题',
      type: 'text',
      placeholder: '请输入提示词标题',
      required: true,
      maxLength: 100,
      helpText: '简短而描述性的标题，便于识别和搜索',
    },
    {
      name: 'description',
      label: '描述',
      type: 'textarea',
      placeholder: '请描述这个提示词的用途和功能',
      required: true,
      maxLength: 500,
      rows: 3,
      helpText: '详细描述提示词的作用、适用场景和预期效果',
    },
    {
      name: 'role',
      label: '角色定义',
      type: 'textarea',
      placeholder: '请定义AI应该扮演的角色，如：你是一位专业的技术顾问...',
      required: true,
      maxLength: 200,
      rows: 2,
      helpText: '明确AI的身份和专业背景，影响回答的风格和角度',
    },
    {
      name: 'tone',
      label: '语调风格',
      type: 'select',
      placeholder: '请选择语调风格',
      required: true,
      options: toneOptions,
      helpText: '选择合适的语调以匹配使用场景和用户期望',
    },
    {
      name: 'capabilities',
      label: '能力描述',
      type: 'tags',
      placeholder: '输入能力描述，按回车添加',
      required: true,
      maxLength: 10,
      helpText: '列出AI在这个角色下应该具备的主要能力和技能',
    },
    {
      name: 'constraints',
      label: '约束条件',
      type: 'tags',
      placeholder: '输入约束条件，按回车添加',
      required: false,
      maxLength: 10,
      helpText: '设定AI的行为限制和不应该做的事情',
    },
    {
      name: 'tags',
      label: '标签',
      type: 'tags',
      placeholder: '输入标签，按回车添加',
      required: false,
      maxLength: 20,
      helpText: '添加相关标签，便于分类和搜索',
    },
    {
      name: 'language',
      label: '主要语言',
      type: 'select',
      placeholder: '请选择主要语言',
      required: false,
      options: languageOptions,
      helpText: '指定提示词的主要使用语言',
    },
  ], []);

  // 处理字段值变化
  const handleChange = (fieldName: keyof PromptFormData, value: any) => {
    handleFieldChange(fieldName, value);

    const newData = {
      ...formData,
      [fieldName]: value,
    };
    onChange(newData);
  };

  // 处理字段失去焦点
  const handleBlur = (fieldName: keyof PromptFormData, value: any) => {
    handleFieldBlur(fieldName, value);
  };

  // 处理保存
  const handleSave = () => {
    const isValid = validateForm(formData);
    if (isValid && onSave) {
      onSave();
    }
  };

  // 渲染自动保存状态
  const renderAutoSaveStatus = () => {
    const statusConfig = {
      saved: { text: '已保存', className: 'text-green-600', icon: '✓' },
      saving: { text: '保存中...', className: 'text-blue-600', icon: '⏳' },
      dirty: { text: '有未保存的更改', className: 'text-yellow-600', icon: '●' },
      error: { text: '保存失败', className: 'text-red-600', icon: '✗' },
    };

    const config = statusConfig[autoSaveStatus];

    return (
      <div className={cn('flex items-center gap-1 text-xs', config.className)}>
        <span>{config.icon}</span>
        <span>{config.text}</span>
      </div>
    );
  };

  return (
    <Card className={cn('h-full flex flex-col', className)}>
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold">提示词元数据</h2>
        </div>
        {renderAutoSaveStatus()}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-6">
          {fieldConfigs.map((config) => (
            <FormField
              key={config.name}
              config={config}
              value={formData[config.name]}
              onChange={(value) => handleChange(config.name, value)}
              error={getFieldError(config.name)}
              disabled={readonly}
              onBlur={() => handleBlur(config.name, formData[config.name])}
            />
          ))}

          {/* 模板选项 */}
          <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg">
            <input
              type="checkbox"
              id="isTemplate"
              checked={formData.isTemplate || false}
              onChange={(e) => handleChange('isTemplate', e.target.checked)}
              disabled={readonly}
              className="rounded border-gray-300 text-primary focus:ring-primary"
            />
            <label htmlFor="isTemplate" className="text-sm font-medium">
              标记为模板
            </label>
            <p className="text-xs text-muted-foreground ml-2">
              模板可以被其他用户复用和修改
            </p>
          </div>
        </div>
      </div>

      {/* 操作按钮 */}
      {!readonly && (showSaveButton || showResetButton) && (
        <div className="flex items-center justify-between gap-3 p-4 border-t">
          <div className="flex gap-2">
            {showResetButton && (
              <Button
                variant="outline"
                size="sm"
                onClick={onReset}
                leftIcon={<RotateCcw className="w-4 h-4" />}
              >
                重置
              </Button>
            )}
          </div>

          {showSaveButton && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleSave}
              disabled={hasErrors || saving}
              loading={saving}
              leftIcon={<Save className="w-4 h-4" />}
            >
              {saving ? '保存中...' : '保存'}
            </Button>
          )}
        </div>
      )}
    </Card>
  );
};

export default MetadataForm;