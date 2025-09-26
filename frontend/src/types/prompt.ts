/**
 * 提示词相关类型定义
 */

/** 提示词元数据 */
export interface PromptMetadata {
  /** 角色定义 */
  role: string;
  /** 语调风格 */
  tone: string;
  /** 能力描述 */
  capabilities: string[];
  /** 约束条件 */
  constraints: string[];
  /** 版本号 */
  version?: string;
  /** 标签 */
  tags?: string[];
  /** 语言 */
  language?: 'zh' | 'en';
  /** 创建时间 */
  createdAt?: Date;
  /** 更新时间 */
  updatedAt?: Date;
}

/** 提示词内容 */
export interface PromptContent {
  /** markdown格式的提示词内容 */
  content: string;
  /** 纯文本内容（用于预览） */
  plainText?: string;
}

/** 完整的提示词数据 */
export interface Prompt {
  /** 唯一标识符 */
  id: string;
  /** 提示词标题 */
  title: string;
  /** 提示词描述 */
  description: string;
  /** 元数据 */
  metadata: PromptMetadata;
  /** 内容 */
  content: PromptContent;
  /** 是否为模板 */
  isTemplate?: boolean;
  /** 模板参数（如果是模板） */
  templateParams?: string[];
  /** 状态 */
  status: 'draft' | 'published' | 'archived';
  /** 所有者 */
  ownerId?: string;
  /** 创建时间 */
  createdAt: Date;
  /** 更新时间 */
  updatedAt: Date;
}

/** 提示词表单数据 */
export interface PromptFormData {
  /** 标题 */
  title: string;
  /** 描述 */
  description: string;
  /** 角色 */
  role: string;
  /** 语调 */
  tone: string;
  /** 能力 */
  capabilities: string[];
  /** 约束 */
  constraints: string[];
  /** 内容 */
  content: string;
  /** 标签 */
  tags?: string[];
  /** 语言 */
  language?: 'zh' | 'en';
  /** 是否为模板 */
  isTemplate?: boolean;
}

/** 表单验证规则 */
export interface PromptFormValidation {
  /** 字段名 */
  field: keyof PromptFormData;
  /** 验证规则 */
  rules: ValidationRule[];
}

/** 验证规则类型 */
export interface ValidationRule {
  /** 规则类型 */
  type: 'required' | 'minLength' | 'maxLength' | 'pattern' | 'custom';
  /** 规则值 */
  value?: any;
  /** 错误消息 */
  message: string;
  /** 自定义验证函数 */
  validator?: (value: any) => boolean;
}

/** 表单字段配置 */
export interface FormFieldConfig {
  /** 字段名 */
  name: keyof PromptFormData;
  /** 标签 */
  label: string;
  /** 字段类型 */
  type: 'text' | 'textarea' | 'tags' | 'select' | 'multiselect';
  /** 占位符 */
  placeholder?: string;
  /** 帮助文本 */
  helpText?: string;
  /** 是否必填 */
  required?: boolean;
  /** 选项（适用于select和multiselect） */
  options?: Array<{ value: string; label: string }>;
  /** 最大长度 */
  maxLength?: number;
  /** 最小长度 */
  minLength?: number;
  /** 行数（适用于textarea） */
  rows?: number;
  /** 是否禁用 */
  disabled?: boolean;
  /** 验证规则 */
  validation?: ValidationRule[];
}

/** 会话消息类型 */
export interface ConversationMessage {
  /** 消息ID */
  id: string;
  /** 发送者类型 */
  sender: 'user' | 'pe_engineer' | 'peqa' | 'system';
  /** 消息内容 */
  content: string;
  /** 时间戳 */
  timestamp: Date;
  /** 消息类型 */
  type: 'text' | 'prompt_suggestion' | 'quality_feedback' | 'error' | 'status';
  /** 相关的提示词数据（如果适用） */
  promptData?: Partial<PromptFormData>;
  /** 元数据 */
  metadata?: Record<string, any>;
}

/** 会话状态 */
export interface ConversationState {
  /** 会话ID */
  id: string;
  /** 消息列表 */
  messages: ConversationMessage[];
  /** 当前模式 */
  mode: 'create' | 'optimize' | 'quality_check';
  /** 是否正在加载 */
  isLoading: boolean;
  /** 连接状态 */
  connectionStatus: 'connected' | 'disconnected' | 'connecting' | 'error';
  /** 错误信息 */
  error?: string;
}

/** 编辑器视图状态 */
export interface EditorViewState {
  /** 左侧面板是否展开 */
  leftPanelExpanded: boolean;
  /** 右侧面板是否展开 */
  rightPanelExpanded: boolean;
  /** 分割位置（百分比） */
  splitPosition: number;
  /** 是否显示预览 */
  showPreview: boolean;
  /** 活动标签页 */
  activeTab: 'metadata' | 'content' | 'preview';
  /** 是否为移动端视图 */
  isMobile: boolean;
}

/** 自动保存状态 */
export interface AutoSaveState {
  /** 是否启用自动保存 */
  enabled: boolean;
  /** 自动保存间隔（毫秒） */
  interval: number;
  /** 最后保存时间 */
  lastSaved?: Date;
  /** 保存状态 */
  status: 'saved' | 'saving' | 'dirty' | 'error';
  /** 错误信息 */
  error?: string;
}