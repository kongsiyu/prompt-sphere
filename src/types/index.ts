// Common types for the AI System Prompt Generator

export interface SystemPrompt {
  id: string
  title: string
  content: string
  description?: string
  category?: string
  tags: string[]
  createdAt: Date
  updatedAt: Date
}

export interface PromptCategory {
  id: string
  name: string
  description?: string
  color?: string
}

export type PromptFilter = {
  search?: string
  category?: string
  tags?: string[]
}