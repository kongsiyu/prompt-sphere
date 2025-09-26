/**
 * 提示词编辑器主页面
 * 统一的提示词创建和编辑界面，包含左右分栏布局
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { cn } from '@/utils/cn';
import { SplitLayout } from '@/components/layout/SplitLayout';
import { MetadataForm } from '@/components/forms/MetadataForm';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { PromptFormData, EditorViewState, AutoSaveState } from '@/types/prompt';
import { Edit3, MessageSquare, Eye, Save, ArrowLeft } from 'lucide-react';
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
    } catch (error) {
      console.error('Failed to load prompt data:', error);
    } finally {
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

  // 渲染右侧面板（聊天界面占位）
  const renderRightPanel = () => {
    return (
      <Card className="h-full flex flex-col">
        <div className="flex items-center gap-2 p-4 border-b">
          <MessageSquare className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold">AI 助手对话</h2>
        </div>

        <div className="flex-1 flex items-center justify-center text-muted-foreground">
          <div className="text-center space-y-2">
            <MessageSquare className="w-12 h-12 mx-auto opacity-50" />
            <p className="text-sm">聊天界面即将推出</p>
            <p className="text-xs">将与 PE Engineer 和 PEQA 智能助手集成</p>
          </div>
        </div>

        <div className="p-4 border-t">
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled className="flex-1">
              创建模式
            </Button>
            <Button variant="outline" size="sm" disabled className="flex-1">
              优化模式
            </Button>
            <Button variant="outline" size="sm" disabled className="flex-1">
              质量检查
            </Button>
          </div>
        </div>
      </Card>
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