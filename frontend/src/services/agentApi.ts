/**
 * Agent API 服务
 * 封装 PE Engineer 和 PEQA 的 API 调用，包括错误处理和重试机制
 */

import {
  AgentType,
  ChatMode,
  AgentRequest,
  AgentResponse,
  AgentMetadata
} from '@/types/chat';

// API 配置
const API_CONFIG = {
  baseUrl: process.env.REACT_APP_API_BASE_URL || 'http://localhost:3001/api',
  timeout: 30000, // 30秒超时
  retryAttempts: 3,
  retryDelay: 1000, // 1秒
};

// Agent 端点配置
const AGENT_ENDPOINTS = {
  pe_engineer: '/agents/pe-engineer',
  peqa: '/agents/peqa'
};

// 错误类型
export class AgentApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public agent: AgentType,
    public details?: any
  ) {
    super(message);
    this.name = 'AgentApiError';
  }
}

/**
 * HTTP 请求工具函数
 */
async function makeRequest<T>(
  url: string,
  options: RequestInit,
  timeout: number = API_CONFIG.timeout
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMessage = `HTTP Error: ${response.status}`;
      let errorDetails;

      try {
        errorDetails = await response.json();
        errorMessage = errorDetails.message || errorMessage;
      } catch {
        // 忽略 JSON 解析错误
      }

      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('请求超时');
    }

    throw error;
  }
}

/**
 * 重试机制
 */
async function withRetry<T>(
  operation: () => Promise<T>,
  maxAttempts: number = API_CONFIG.retryAttempts,
  delay: number = API_CONFIG.retryDelay
): Promise<T> {
  let lastError: Error;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      // 如果不是网络错误或者是最后一次尝试，直接抛出错误
      if (attempt === maxAttempts || !isRetryableError(lastError)) {
        throw lastError;
      }

      // 等待后重试
      await new Promise(resolve => setTimeout(resolve, delay * attempt));
    }
  }

  throw lastError!;
}

/**
 * 判断错误是否可重试
 */
function isRetryableError(error: Error): boolean {
  const retryableMessages = [
    '请求超时',
    'Network Error',
    'fetch failed',
    'Failed to fetch'
  ];

  return retryableMessages.some(msg => error.message.includes(msg));
}

/**
 * PE Engineer API 调用
 */
export async function callPEEngineer(request: AgentRequest): Promise<AgentResponse> {
  const startTime = Date.now();

  try {
    // 在实际实现中，这里会调用真实的 PE Engineer API
    // 现在使用模拟实现
    const response = await withRetry(async () => {
      // 模拟网络延迟
      await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 2000));

      // 模拟偶尔的网络错误
      if (Math.random() < 0.1) {
        throw new Error('Network Error');
      }

      return mockPEEngineerResponse(request);
    });

    const processingTime = Date.now() - startTime;

    return {
      ...response,
      metadata: {
        ...response.metadata,
        processingTime
      }
    };

  } catch (error) {
    throw new AgentApiError(
      error instanceof Error ? error.message : 'PE Engineer 调用失败',
      'PE_ENGINEER_ERROR',
      'pe_engineer',
      error
    );
  }
}

/**
 * PEQA API 调用
 */
export async function callPEQA(request: AgentRequest): Promise<AgentResponse> {
  const startTime = Date.now();

  try {
    // 在实际实现中，这里会调用真实的 PEQA API
    // 现在使用模拟实现
    const response = await withRetry(async () => {
      // 模拟网络延迟
      await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 1500));

      // 模拟偶尔的网络错误
      if (Math.random() < 0.1) {
        throw new Error('Network Error');
      }

      return mockPEQAResponse(request);
    });

    const processingTime = Date.now() - startTime;

    return {
      ...response,
      metadata: {
        ...response.metadata,
        processingTime
      }
    };

  } catch (error) {
    throw new AgentApiError(
      error instanceof Error ? error.message : 'PEQA 调用失败',
      'PEQA_ERROR',
      'peqa',
      error
    );
  }
}

/**
 * 通用 Agent 调用接口
 */
export async function callAgent(request: AgentRequest): Promise<AgentResponse> {
  switch (request.agent) {
    case 'pe_engineer':
      return callPEEngineer(request);
    case 'peqa':
      return callPEQA(request);
    default:
      throw new AgentApiError(
        `不支持的 Agent 类型: ${request.agent}`,
        'UNSUPPORTED_AGENT',
        request.agent
      );
  }
}

/**
 * 模拟 PE Engineer 响应
 */
function mockPEEngineerResponse(request: AgentRequest): AgentResponse {
  const { message, mode, metadata } = request;

  // 根据模式生成不同的响应
  let responseMessage = '';
  let suggestions: string[] = [];

  switch (mode) {
    case 'create':
      responseMessage = `基于您的需求 "${message}"，我为您创建了一个提示词模板。这个模板包含了清晰的角色定义、任务描述和输出格式要求。建议您根据具体场景进一步调整参数。`;
      suggestions = [
        '添加具体的示例',
        '调整语气和风格',
        '增加约束条件',
        '优化输出格式'
      ];
      break;

    case 'optimize':
      responseMessage = `我已经分析了您的提示词 "${message}"，并提出了以下优化建议：1. 增强角色定义的具体性；2. 明确任务的边界和约束；3. 改进输出格式的结构化程度；4. 添加质量控制机制。`;
      suggestions = [
        '应用优化建议',
        '测试优化效果',
        '进一步细化',
        '保存优化版本'
      ];
      break;

    default:
      responseMessage = `我收到了您的消息："${message}"。作为 PE Engineer，我可以帮助您创建、优化和改进提示词。请告诉我您的具体需求。`;
      suggestions = [
        '创建新提示词',
        '优化现有提示词',
        '分析提示词效果'
      ];
  }

  const confidence = 0.85 + Math.random() * 0.1;

  const agentMetadata: AgentMetadata = {
    confidence,
    version: '1.0.0',
    sources: ['PE Engineering Best Practices', 'Prompt Design Patterns'],
    reasoning: '基于提示词工程的最佳实践和设计模式生成响应'
  };

  return {
    success: true,
    message: responseMessage,
    agent: 'pe_engineer',
    mode,
    metadata: agentMetadata,
    suggestions
  };
}

/**
 * 模拟 PEQA 响应
 */
function mockPEQAResponse(request: AgentRequest): AgentResponse {
  const { message, mode, metadata } = request;

  let responseMessage = '';
  let suggestions: string[] = [];

  switch (mode) {
    case 'quality_check':
      const qualityScore = Math.floor(75 + Math.random() * 20);
      responseMessage = `质量评估完成！您的提示词 "${message}" 得分：${qualityScore}/100。主要优势：结构清晰、目标明确。改进建议：1. 增加更多约束条件；2. 提供具体示例；3. 优化输出格式；4. 加强错误处理。`;
      suggestions = [
        '查看详细评估报告',
        '应用改进建议',
        '重新评估',
        '对比其他版本'
      ];
      break;

    case 'optimize':
      responseMessage = `从质量保证角度分析，您的提示词有以下优化空间：1. 可测试性 - 添加可验证的成功标准；2. 鲁棒性 - 增强错误处理能力；3. 一致性 - 确保输出格式统一；4. 可维护性 - 模块化设计便于更新。`;
      suggestions = [
        '实施质量优化',
        '添加测试用例',
        '制定评估标准',
        '建立版本控制'
      ];
      break;

    default:
      responseMessage = `作为 PEQA (Prompt Engineering Quality Assurance) 专家，我专注于提示词的质量评估和保证。我可以帮您：1. 质量检查和评分；2. 识别潜在问题；3. 提供优化建议；4. 制定质量标准。`;
      suggestions = [
        '开始质量评估',
        '设置质量标准',
        '查看评估历史'
      ];
  }

  const confidence = 0.90 + Math.random() * 0.08;

  const agentMetadata: AgentMetadata = {
    confidence,
    version: '1.0.0',
    sources: ['Quality Assurance Guidelines', 'Prompt Testing Framework'],
    reasoning: '基于质量保证标准和测试框架进行评估'
  };

  return {
    success: true,
    message: responseMessage,
    agent: 'peqa',
    mode,
    metadata: agentMetadata,
    suggestions
  };
}

/**
 * 健康检查 API
 */
export async function healthCheck(): Promise<{ status: string; agents: Record<AgentType, boolean> }> {
  try {
    // 在实际实现中，这里会调用真实的健康检查端点
    await new Promise(resolve => setTimeout(resolve, 500));

    return {
      status: 'healthy',
      agents: {
        pe_engineer: true,
        peqa: true
      }
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      agents: {
        pe_engineer: false,
        peqa: false
      }
    };
  }
}

/**
 * 获取 Agent 能力信息
 */
export async function getAgentCapabilities(agent: AgentType): Promise<{
  name: string;
  description: string;
  supportedModes: ChatMode[];
  features: string[];
  version: string;
}> {
  // 模拟 API 调用
  await new Promise(resolve => setTimeout(resolve, 300));

  const capabilities = {
    pe_engineer: {
      name: 'PE Engineer',
      description: '专业的提示词工程师，擅长创建和优化高质量提示词',
      supportedModes: ['create', 'optimize'] as ChatMode[],
      features: [
        '提示词模板生成',
        '提示词结构优化',
        '参数调优建议',
        '最佳实践指导',
        '多轮对话设计',
        'Few-shot 示例生成'
      ],
      version: '1.0.0'
    },
    peqa: {
      name: 'PEQA',
      description: '提示词质量保证专家，专注于质量评估和改进建议',
      supportedModes: ['quality_check', 'optimize'] as ChatMode[],
      features: [
        '质量评分和分析',
        '问题识别和诊断',
        '测试用例生成',
        '性能基准测试',
        '一致性验证',
        '最佳实践审查'
      ],
      version: '1.0.0'
    }
  };

  return capabilities[agent];
}

/**
 * 批量调用多个 Agent
 */
export async function callMultipleAgents(
  requests: AgentRequest[]
): Promise<AgentResponse[]> {
  const promises = requests.map(request => callAgent(request));

  try {
    return await Promise.all(promises);
  } catch (error) {
    // 部分失败的处理
    const results = await Promise.allSettled(promises);

    return results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        const request = requests[index];
        return {
          success: false,
          agent: request.agent,
          mode: request.mode,
          error: {
            code: 'CALL_FAILED',
            message: result.reason.message || '调用失败',
            details: result.reason
          }
        };
      }
    });
  }
}

export default {
  callAgent,
  callPEEngineer,
  callPEQA,
  healthCheck,
  getAgentCapabilities,
  callMultipleAgents,
  AgentApiError
};