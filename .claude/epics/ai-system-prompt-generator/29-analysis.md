---
issue: 29
title: Unified Prompt Creation and Editing Interface
analyzed: 2025-09-25T14:24:07Z
estimated_hours: 48
parallelization_factor: 3.2
---

# Parallel Work Analysis: Issue #29

## Overview
实现核心的统一提示词创建和编辑界面，采用左右分栏布局设计。左侧包含元数据表单和Markdown编辑器，右侧集成PE Engineer和PEQA双Agent对话界面，支持创建、优化和质量评估三种模式。这是一个复杂的前端任务，具有很好的并行化潜力。

## Parallel Streams

### Stream A: 左侧面板基础架构
**Scope**: 实现分栏布局、元数据表单组件和基础UI架构
**Files**:
- `frontend/src/pages/PromptEditor/index.tsx`
- `frontend/src/components/layout/SplitLayout.tsx`
- `frontend/src/components/forms/MetadataForm.tsx`
- `frontend/src/components/forms/FormField.tsx`
- `frontend/src/hooks/useFormValidation.ts`
- `frontend/src/types/prompt.ts`
**Agent Type**: frontend-specialist
**Can Start**: immediately
**Estimated Hours**: 12
**Dependencies**: none

### Stream B: Markdown编辑器和预览系统
**Scope**: 集成Markdown编辑器、实时预览、自动保存功能
**Files**:
- `frontend/src/components/editor/MarkdownEditor.tsx`
- `frontend/src/components/editor/MarkdownPreview.tsx`
- `frontend/src/hooks/useAutoSave.ts`
- `frontend/src/hooks/useMarkdownSync.ts`
- `frontend/src/utils/markdown.ts`
**Agent Type**: frontend-specialist
**Can Start**: immediately
**Estimated Hours**: 10
**Dependencies**: none

### Stream C: 聊天界面和Agent集成
**Scope**: 构建聊天界面、WebSocket连接、消息历史管理
**Files**:
- `frontend/src/components/chat/ChatInterface.tsx`
- `frontend/src/components/chat/MessageList.tsx`
- `frontend/src/components/chat/MessageInput.tsx`
- `frontend/src/components/chat/TypingIndicator.tsx`
- `frontend/src/hooks/useWebSocket.ts`
- `frontend/src/hooks/useChat.ts`
- `frontend/src/services/agentApi.ts`
**Agent Type**: frontend-specialist
**Can Start**: after basic layout is ready
**Estimated Hours**: 14
**Dependencies**: Stream A (layout structure)

### Stream D: 状态管理和数据同步
**Scope**: 实现统一状态管理、表单与聊天数据同步、API集成
**Files**:
- `frontend/src/stores/promptEditorStore.ts`
- `frontend/src/hooks/usePromptEditor.ts`
- `frontend/src/services/promptApi.ts`
- `frontend/src/utils/dataSync.ts`
- `frontend/src/types/api.ts`
**Agent Type**: frontend-specialist
**Can Start**: after Stream A & B have basic structure
**Estimated Hours**: 8
**Dependencies**: Stream A (form structure), Stream B (editor interface)

### Stream E: 导出功能和工作流集成
**Scope**: 实现导出功能、两种创建工作流、模式切换
**Files**:
- `frontend/src/components/export/ExportDialog.tsx`
- `frontend/src/components/workflow/CreationModeSelector.tsx`
- `frontend/src/hooks/useExport.ts`
- `frontend/src/utils/export.ts`
- `frontend/src/constants/workflows.ts`
**Agent Type**: frontend-specialist
**Can Start**: after core functionality is implemented
**Estimated Hours**: 6
**Dependencies**: Stream A (form), Stream B (editor), Stream C (chat)

### Stream F: 页面框架和索引页
**Scope**: 实现主应用程序框架（头部、菜单、底部）和空白索引页
**Files**:
- `frontend/src/components/layout/AppLayout.tsx`
- `frontend/src/layouts/AppLayout.tsx`
- `frontend/src/pages/Dashboard/index.tsx`
- `frontend/src/router/index.tsx` (更新路由)
**Agent Type**: general-purpose
**Can Start**: immediately
**Estimated Hours**: 4
**Dependencies**: none
**Status**: ✅ 已完成

## Coordination Points

### Shared Files
以下文件可能需要多个流协调修改:
- `frontend/src/types/prompt.ts` - Stream A & D (类型定义)
- `frontend/src/pages/PromptEditor/index.tsx` - Stream A & C (主要组件集成)
- `package.json` - Stream B & C (添加依赖)
- `frontend/src/hooks/usePromptEditor.ts` - Stream C & D (状态管理集成)

### Sequential Requirements
必须按顺序执行的步骤:
1. 基础布局和表单结构 (Stream A) → 聊天界面集成 (Stream C)
2. 表单和编辑器基础 (Stream A & B) → 状态管理 (Stream D)
3. 核心功能完成 (Stream A, B, C, D) → 导出和工作流 (Stream E)

## Conflict Risk Assessment
- **Low Risk**: Stream B (编辑器) 相对独立，冲突少
- **Medium Risk**: Stream A & C 需要在主页面组件上协调
- **High Risk**: Stream D 涉及状态管理，可能影响所有其他流

## Parallelization Strategy

**Recommended Approach**: hybrid

**执行策略**:
1. **Phase 1**: 同时启动Stream A (布局)、Stream B (编辑器)和 Stream F (页面框架) ✅ 已完成
2. **Phase 2**: Stream A 基础完成后，启动Stream C (聊天界面)
3. **Phase 3**: Stream A & B 完成基础结构后，启动Stream D (状态管理)
4. **Phase 4**: 核心功能就绪后，启动Stream E (导出和工作流)
5. **Integration**: 最终集成所有组件到主页面

## Expected Timeline

With parallel execution:
- Wall time: 15 hours (最长路径: Stream A → Stream C → Stream E + 集成时间)
- Total work: 54 hours (包含 Stream F 的 4 小时)
- Efficiency gain: 72%

Without parallel execution:
- Wall time: 54 hours

## Notes
- 这是一个复杂的前端任务，需要仔细的组件设计和状态管理
- WebSocket集成需要与后端API协调，确保连接稳定性
- 双语支持(中英文)需要在所有组件中考虑
- 响应式设计对分栏布局尤其重要
- 建议使用TypeScript进行严格类型检查
- 考虑使用Storybook进行组件开发和测试
- 自动保存功能需要防抖处理，避免频繁API调用
- 聊天界面需要考虑消息流的性能优化
- 状态管理建议使用Zustand或Redux Toolkit以保持简洁