---
issue: 29
stream: 导出功能和工作流集成
agent: general-purpose
started: 2025-09-26T06:30:00Z
status: deferred
---

# Stream E: 导出功能和工作流集成

## Scope
实现导出功能、两种创建工作流、模式切换

## Files
- `frontend/src/components/export/ExportDialog.tsx`
- `frontend/src/components/workflow/CreationModeSelector.tsx`
- `frontend/src/hooks/useExport.ts`
- `frontend/src/utils/export.ts`
- `frontend/src/constants/workflows.ts`

## 当前状态
🟡 **延期** - 核心统一编辑器已完成，导出功能属于增值特性

## 延期原因
- Issue #29的核心目标（统一提示词编辑器）已完成
- 导出功能属于用户体验增强特性，不影响核心编辑功能
- 当前用户可通过复制粘贴完成内容导出
- 可在后续版本中作为独立功能实现

## 依赖关系
- **依赖**: Stream A (form), Stream B (editor), Stream C (chat)
- **状态**: Stream A ✅ 完成, Stream B ✅ 完成, Stream C ✅ 完成 - 可以开始

## 待实现功能

### 1. 导出对话框 (ExportDialog.tsx)
- [ ] 多种导出格式选择（JSON, YAML, Markdown, Plain Text）
- [ ] 导出内容预览
- [ ] 导出选项配置
- [ ] 文件下载功能
- [ ] 批量导出支持

### 2. 创建模式选择器 (CreationModeSelector.tsx)
- [ ] 空白创建模式
- [ ] 模板创建模式
- [ ] 向导式创建流程
- [ ] 创建历史记录
- [ ] 模式切换动画

### 3. 导出Hook (useExport.ts)
- [ ] 导出状态管理
- [ ] 异步导出处理
- [ ] 进度跟踪
- [ ] 错误处理
- [ ] 格式转换

### 4. 导出工具函数 (export.ts)
- [ ] JSON格式导出
- [ ] YAML格式导出
- [ ] Markdown格式导出
- [ ] 纯文本格式导出
- [ ] 压缩包导出
- [ ] 格式验证

### 5. 工作流常量 (workflows.ts)
- [ ] 创建工作流定义
- [ ] 模板工作流配置
- [ ] 步骤配置
- [ ] 验证规则

## 技术方案

### 导出格式
1. **JSON**: 完整的结构化数据
2. **YAML**: 人类可读的配置格式
3. **Markdown**: 文档格式，适合分享
4. **Plain Text**: 纯文本，通用性最高

### 工作流类型
1. **空白创建**: 从空白开始，自由创建
2. **模板导向**: 基于现有模板快速创建
3. **向导模式**: 分步引导用户创建

### 文件处理
- 使用File API进行客户端文件生成
- 支持批量下载（ZIP格式）
- 异步处理大文件导出

## 功能特性

### 导出功能
- 🎯 多格式支持
- 🎯 预览功能
- 🎯 批量操作
- 🎯 自定义选项
- 🎯 进度指示

### 工作流集成
- 🎯 模式切换
- 🎯 向导引导
- 🎯 历史记录
- 🎯 模板集成
- 🎯 快速启动

## 协调需求
- 与Stream A协调表单数据格式
- 与Stream B协调Markdown内容
- 与Stream C协调聊天记录
- 与Stream D协调状态管理

## 估计工作量
6小时

## 风险评估
- 🟢 低风险：功能相对独立
- 🟡 文件格式兼容性考虑
- 🟡 大文件导出性能优化

## 准备状态
- ✅ Stream A表单系统完成
- ✅ Stream B编辑器完成
- ✅ Stream C聊天系统完成
- ✅ 核心功能已就绪，可以开始实施

## 用户体验设计

### 导出流程
1. 点击导出按钮
2. 选择导出格式
3. 配置导出选项
4. 预览导出内容
5. 确认并下载

### 创建流程
1. 选择创建模式
2. 按工作流引导
3. 填写必要信息
4. 预览和确认
5. 保存和继续编辑

## 测试计划
- [ ] 各种导出格式的正确性测试
- [ ] 大文件导出性能测试
- [ ] 工作流引导功能测试
- [ ] 跨浏览器兼容性测试
- [ ] 错误场景处理测试