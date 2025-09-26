/**
 * 提示词编辑器主页面
 * 统一的提示词创建和编辑界面，包含左右分栏布局和AI助手聊天功能
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { cn } from '@/utils/cn';
import { SplitLayout } from '@/components/layout/SplitLayout';
import { MetadataForm } from '@/components/forms/MetadataForm';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ChatInterface } from '@/components/chat';
import { PromptFormData, EditorViewState, AutoSaveState } from '@/types/prompt';
import { AgentType, ChatMode } from '@/types/chat';
import { Edit3, MessageSquare, Eye, Save, ArrowLeft, Bot, CheckCircle, Zap, RefreshCw } from 'lucide-react';
import MDEditor from '@uiw/react-md-editor';
import '@uiw/react-md-editor/markdown-editor.css';

interface PromptEditorProps {
  /** 编辑器模式 */
  mode?: 'create' | 'edit';
}

/**
 * PromptEditor 提示词编辑器页面
 *
 * @example
 * ```tsx
 * // 创建新提示词
 * <PromptEditor mode="create" />
 *
 * // 编辑现有提示词 (URL: /prompts/:id/edit)
 * <PromptEditor mode="edit" />
 * ```
 */
export const PromptEditor: React.FC<PromptEditorProps> = ({ mode = 'create' }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // 表单数据状态
  const [formData, setFormData] = useState<Partial<PromptFormData>>({
    title: '',
    description: '',
    role: '',
    tone: '',
    capabilities: [],
    constraints: [],
    content: '',
    tags: [],
    language: 'zh',
    isTemplate: false,
  });

  // 编辑器视图状态
  const [viewState, setViewState] = useState<EditorViewState>({
    leftPanelExpanded: true,
    rightPanelExpanded: true,
    splitPosition: 50,
    showPreview: false,
    activeTab: 'metadata',
    isMobile: false,
  });

  // 自动保存状态
  const [autoSaveState, setAutoSaveState] = useState<AutoSaveState>({
    enabled: true,
    interval: 30000, // 30秒
    lastSaved: undefined,
    status: 'saved',
    error: undefined,
  });

  // 聊天相关状态
  const [chatEnabled, setChatEnabled] = useState(true);
  const [currentAgent, setCurrentAgent] = useState<AgentType>('pe_engineer');
  const [currentMode, setCurrentMode] = useState<ChatMode>('create');

  // 加载状态
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // 检查是否为移动端
  const checkIsMobile = useCallback(() => {
    const isMobile = window.innerWidth < 768;
    setViewState(prev => ({ ...prev, isMobile }));
  }, []);

  useEffect(() => {
    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);
    return () => window.removeEventListener('resize', checkIsMobile);
  }, [checkIsMobile]);

  // 加载现有提示词数据（编辑模式）
  useEffect(() => {
    if (mode === 'edit' && id) {
      loadPromptData(id);
    }
  }, [mode, id]);

  // 根据编辑器模式设置聊天模式
  useEffect(() => {
    if (mode === 'edit' && formData.content) {
      setCurrentMode('optimize');
    } else {
      setCurrentMode('create');
    }
  }, [mode, formData.content]);

  // 自动保存功能
  useEffect(() => {
    if (!autoSaveState.enabled) return;

    const timer = setInterval(() => {
      if (autoSaveState.status === 'dirty') {
        handleAutoSave();
      }
    }, autoSaveState.interval);

    return () => clearInterval(timer);
  }, [autoSaveState.enabled, autoSaveState.interval, autoSaveState.status]);

  // 加载提示词数据
  const loadPromptData = async (promptId: string) => {
    setLoading(true);
    try {
      // TODO: 调用API加载提示词数据
      // const response = await promptAPI.getById(promptId);
      // setFormData(response.data);
      console.log('Loading prompt data for ID:', promptId);

      // 模拟加载数据
      setTimeout(() => {
        setFormData({
          title: '示例提示词',
          description: '这是一个示例提示词的描述',
          role: 'AI助手',
          tone: 'professional',
          capabilities: ['问答', '分析'],
          constraints: ['保持专业', '简洁明了'],
          content: '# 示例提示词\n\n你是一个专业的AI助手，请根据用户的问题提供准确的回答。',
          tags: ['示例', '助手'],
          language: 'zh',
          isTemplate: false,
        });
        setLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Failed to load prompt data:', error);
      setLoading(false);
    }
  };

  // 处理表单数据变化
  const handleFormDataChange = useCallback((newData: Partial<PromptFormData>) => {
    setFormData(newData);
    setAutoSaveState(prev => ({ ...prev, status: 'dirty' }));
  }, []);

  // 自动保存
  const handleAutoSave = async () => {
    setAutoSaveState(prev => ({ ...prev, status: 'saving' }));

    try {
      // TODO: 调用API保存草稿
      // await promptAPI.saveDraft(formData);
      console.log('Auto-saving draft...');

      setAutoSaveState(prev => ({
        ...prev,
        status: 'saved',
        lastSaved: new Date(),
        error: undefined,
      }));
    } catch (error) {
      console.error('Auto-save failed:', error);
      setAutoSaveState(prev => ({
        ...prev,
        status: 'error',
        error: '自动保存失败',
      }));
    }
  };

  // 手动保存
  const handleSave = async () => {
    setSaving(true);

    try {
      if (mode === 'create') {
        // TODO: 调用API创建新提示词
        // const response = await promptAPI.create(formData);
        console.log('Creating new prompt...');
      } else {
        // TODO: 调用API更新现有提示词
        // await promptAPI.update(id, formData);
        console.log('Updating prompt...');
      }

      setAutoSaveState(prev => ({
        ...prev,
        status: 'saved',
        lastSaved: new Date(),
      }));

      // 保存成功后可以跳转或显示提示
      // navigate('/prompts');
    } catch (error) {
      console.error('Save failed:', error);
    } finally {
      setSaving(false);
    }
  };

  // 重置表单
  const handleReset = () => {
    setFormData({
      title: '',
      description: '',
      role: '',
      tone: '',
      capabilities: [],
      constraints: [],
      content: '',
      tags: [],
      language: 'zh',
      isTemplate: false,
    });
  };

  // 处理分割位置变化
  const handleSplitPositionChange = (position: number) => {
    setViewState(prev => ({ ...prev, splitPosition: position }));
  };

  // 处理AI助手的回复
  const handlePromptUpdate = useCallback((newPromptContent: string) => {
    handleFormDataChange({
      ...formData,
      content: newPromptContent
    });
  }, [formData, handleFormDataChange]);

  // 处理Agent变化
  const handleAgentChange = useCallback((agent: AgentType) => {
    setCurrentAgent(agent);
  }, []);

  // 处理模式变化
  const handleModeChange = useCallback((mode: ChatMode) => {
    setCurrentMode(mode);
  }, []);

  // 生成当前提示词上下文
  const generatePromptContext = useCallback(() => {
    const context = [];

    if (formData.title) context.push(`标题: ${formData.title}`);
    if (formData.description) context.push(`描述: ${formData.description}`);
    if (formData.role) context.push(`角色: ${formData.role}`);
    if (formData.tone) context.push(`语调: ${formData.tone}`);
    if (formData.capabilities && formData.capabilities.length > 0) {
      context.push(`能力: ${formData.capabilities.join(', ')}`);
    }
    if (formData.constraints && formData.constraints.length > 0) {
      context.push(`约束: ${formData.constraints.join(', ')}`);
    }
    if (formData.content) context.push(`当前内容:\n${formData.content}`);

    return context.join('\n');
  }, [formData]);

  // 渲染左侧面板内容
  const renderLeftPanel = () => {
    const { isMobile, activeTab } = viewState;

    return (
      <div className="flex flex-col h-full">
        {/* 移动端标签页切换 */}
        {isMobile && (
          <div className="flex border-b">
            <button
              className={cn(
                'flex-1 px-4 py-2 text-sm font-medium transition-colors',
                activeTab === 'metadata'
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
              )}
              onClick={() => setViewState(prev => ({ ...prev, activeTab: 'metadata' }))}
            >
              元数据
            </button>
            <button
              className={cn(
                'flex-1 px-4 py-2 text-sm font-medium transition-colors',
                activeTab === 'content'
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
              )}
              onClick={() => setViewState(prev => ({ ...prev, activeTab: 'content' }))}
            >
              内容编辑
            </button>
          </div>
        )}

        {/* 元数据表单 */}
        {(!isMobile || activeTab === 'metadata') && (
          <div className={cn('flex-1 min-h-0', isMobile && 'h-full')}>
            <MetadataForm
              formData={formData}
              onChange={handleFormDataChange}
              onSave={handleSave}
              onReset={handleReset}
              saving={saving}
              autoSaveStatus={autoSaveState.status}
              showSaveButton={!isMobile}
              showResetButton={!isMobile}
            />
          </div>
        )}

        {/* 内容编辑区（桌面端显示在下方，移动端单独显示） */}
        {(!isMobile || activeTab === 'content') && (
          <div className={cn(isMobile ? 'flex-1' : 'h-80 border-t')}>
            <Card className="h-full">
              <div className="flex items-center justify-between p-3 border-b">
                <div className="flex items-center gap-2">
                  <Edit3 className="w-4 h-4 text-primary" />
                  <h3 className="text-sm font-medium">提示词内容</h3>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setViewState(prev => ({ ...prev, showPreview: !prev.showPreview }))}
                  >
                    <Eye className="w-4 h-4" />
                    {viewState.showPreview ? '编辑' : '预览'}
                  </Button>
                </div>
              </div>

              <div className="h-[calc(100%-57px)]">
                <MDEditor
                  value={formData.content || ''}
                  onChange={(value) => handleFormDataChange({ ...formData, content: value || '' })}
                  preview={viewState.showPreview ? 'preview' : 'edit'}
                  hideToolbar={false}
                  data-color-mode="light"
                  height="100%"
                />
              </div>
            </Card>
          </div>
        )}
      </div>
    );
  };

  // 渲染右侧面板（聊天界面）
  const renderRightPanel = () => {
    if (!chatEnabled) {
      return (
        <Card className="h-full flex flex-col">
          <div className="flex items-center gap-2 p-4 border-b">
            <MessageSquare className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold">AI 助手对话</h2>
            <div className="ml-auto">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setChatEnabled(true)}
              >
                启用聊天
              </Button>
            </div>
          </div>

          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            <div className="text-center space-y-2">
              <MessageSquare className="w-12 h-12 mx-auto opacity-50" />
              <p className="text-sm">聊天功能已禁用</p>
              <p className="text-xs">点击上方按钮启用 AI 助手</p>
            </div>
          </div>
        </Card>
      );
    }

    return (
      <div className="h-full">
        <ChatInterface
          defaultAgent={currentAgent}
          defaultMode={currentMode}
          layout="embedded"
          showAgentSelector={true}
          showModeSelector={true}
          showSessionList={false}
          enableFullscreen={false}
          promptContext={generatePromptContext()}
          onPromptUpdate={handlePromptUpdate}
          onAgentChange={handleAgentChange}
          onModeChange={handleModeChange}
          onClose={() => setChatEnabled(false)}
          className="h-full"
        />
      </div>
    );
  };

  // 渲染模式切换按钮
  const renderModeButtons = () => {
    if (!chatEnabled) return null;

    const modes = [
      {
        key: 'create' as ChatMode,
        name: '创建',
        icon: <Zap className="w-4 h-4" />,
        description: '创建新提示词'
      },
      {
        key: 'optimize' as ChatMode,
        name: '优化',
        icon: <RefreshCw className="w-4 h-4" />,
        description: '优化现有提示词'
      },
      {
        key: 'quality_check' as ChatMode,
        name: '检查',
        icon: <CheckCircle className="w-4 h-4" />,
        description: '质量检查'
      }
    ];

    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 dark:bg-gray-800 border-b">
        <span className="text-sm text-gray-600 dark:text-gray-400">助手模式:</span>
        {modes.map(({ key, name, icon, description }) => (
          <Button
            key={key}
            size="sm"
            variant={currentMode === key ? "primary" : "outline"}
            onClick={() => handleModeChange(key)}
            className="flex items-center gap-2"
            title={description}
          >
            {icon}
            {name}
          </Button>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto" />
          <p className="text-sm text-muted-foreground">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* 页面头部 */}
      <div className="flex items-center justify-between p-4 border-b bg-background">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(-1)}
            leftIcon={<ArrowLeft className="w-4 h-4" />}
          >
            返回
          </Button>
          <div>
            <h1 className="text-lg font-semibold">
              {mode === 'create' ? '创建提示词' : '编辑提示词'}
            </h1>
            <p className="text-sm text-muted-foreground">
              {formData.title || '未命名提示词'}
            </p>
          </div>
        </div>

        {/* 自动保存状态指示器 */}
        <div className="flex items-center gap-3">
          {autoSaveState.status === 'saving' && (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <div className="animate-spin w-3 h-3 border border-gray-300 border-t-gray-600 rounded-full" />
              保存中...
            </div>
          )}
          {autoSaveState.lastSaved && autoSaveState.status === 'saved' && (
            <div className="text-sm text-green-600">
              已保存 {new Date(autoSaveState.lastSaved).toLocaleTimeString()}
            </div>
          )}

          {/* 移动端操作按钮 */}
          {viewState.isMobile && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleReset}
              >
                重置
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSave}
                loading={saving}
                leftIcon={<Save className="w-4 h-4" />}
              >
                保存
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* 模式切换按钮 */}
      {renderModeButtons()}

      {/* 主要内容区域 */}
      <div className="flex-1">
        <SplitLayout
          leftPanel={renderLeftPanel()}
          rightPanel={renderRightPanel()}
          defaultSplitPosition={viewState.isMobile ? 100 : 50}
          minLeftWidth={30}
          maxLeftWidth={70}
          resizable={!viewState.isMobile}
          onSplitPositionChange={handleSplitPositionChange}
          className="h-full"
        />
      </div>
    </div>
  );
};

export default PromptEditor;