---
name: ai-system-prompt-generator
status: in-progress
created: 2025-09-22T06:59:00Z
updated: 2025-09-22T14:55:53Z
progress: 10%
prd: .claude/prds/ai-system-prompt-generator.md
github: https://github.com/kongsiyu/prompt-sphere/issues/2
---

# Epic: AI System Prompt Generator

## Overview

A React/Python web application that leverages LLM APIs to transform natural language descriptions into high-quality AI agent prompts. The system uses a two-stage approach: NLP parsing to generate dynamic forms, followed by conversational optimization with dual AI roles (PE Engineer + PEQA) for quality assurance. Built with Python backend for optimal AI performance and FastAPI for modern, high-performance API development.

## Architecture Decisions

- **Frontend**: React with TypeScript for type safety and component reusability
- **Backend**: Python with FastAPI for high-performance API layer and superior AI ecosystem integration
- **AI Framework**: LangChain Python for agent development and LLM orchestration (full feature set)
- **LLM Provider**: 阿里百炼平台接入Qwen大模型 (Alibaba DashScope Python SDK)
- **Database**: MySQL with SQLAlchemy ORM for structured data, Redis for session/cache management
- **Authentication**: JWT-based auth with 钉钉登录 (python-jose + DingTalk OAuth integration)
- **Task Processing**: Celery with Redis for async AI processing and long-running tasks
- **API Documentation**: FastAPI automatic OpenAPI/Swagger generation
- **Design Pattern**: Clean Architecture with domain-driven design for AI agent orchestration

## Technical Approach

### Frontend Components
- **PromptWizard**: Multi-step form component with dynamic field generation
- **ConversationInterface**: Chat-like UI for iterative prompt optimization
- **PromptEditor**: Rich text editor with markdown preview and export
- **QualityDashboard**: Display PEQA scores and improvement suggestions
- **TemplateLibrary**: Browsable collection of prompt templates

### Backend Services (Python/FastAPI)
- **AIAgentService**: LangChain Python agents for PE Engineer and PEQA roles using Qwen models
- **DashScopeService**: 阿里百炼Python SDK integration and request management
- **ParsingService**: Natural language analysis and dynamic form schema generation via LangChain
- **PromptService**: Version management, optimization logic, and conversation history
- **ExportService**: Markdown generation with metadata injection and templating
- **AuthService**: 钉钉OAuth integration with JWT token management (python-jose)
- **TaskService**: Celery-based async processing for long-running AI operations

### Infrastructure
- **Container Deployment**: Docker with Kubernetes for scalability
- **API Gateway**: Rate limiting and request routing (FastAPI built-in middleware)
- **Task Queue**: Redis as message broker for Celery workers
- **Monitoring**: Application performance and AI API usage tracking (Prometheus + Grafana)
- **Security**: Data encryption at rest/transit, audit logging, Pydantic data validation
- **Documentation**: Auto-generated OpenAPI/Swagger docs via FastAPI

## Implementation Strategy

### Development Phases
1. **Core Engine** (Month 1-2): FastAPI foundation, LangChain Python integration, basic AI agent setup
2. **User Interface** (Month 2-3): React components, API integration, conversation flow
3. **Quality System** (Month 3-4): PEQA agent implementation, scoring algorithms, async optimization
4. **Enterprise Features** (Month 4-6): 钉钉Auth, collaboration features, template management

### Risk Mitigation
- **AI Reliability**: Implement circuit breakers and fallback responses via LangChain error handling
- **Performance**: Celery async processing with Redis for long-running AI operations
- **Cost Control**: AI API usage monitoring and request optimization with caching
- **Python Dependencies**: Virtual environment management and dependency pinning

### Testing Approach
- **Unit Tests**: pytest for core business logic and AI service abstractions
- **Integration Tests**: End-to-end prompt generation workflows with FastAPI TestClient
- **Load Tests**: Concurrent user scenarios and AI API rate limits using locust
- **Quality Tests**: PEQA scoring accuracy and consistency validation with test datasets

## Task Breakdown Preview

High-level task categories that will be created:
- [ ] **AI Integration Layer**: LLM API abstraction, PE/PEQA role implementation
- [ ] **Core Parsing Engine**: Natural language analysis and form generation logic
- [ ] **Frontend Application**: React components, routing, state management
- [ ] **Conversation System**: Multi-turn optimization interface and version tracking
- [ ] **Quality Assurance**: PEQA scoring system and improvement recommendations
- [ ] **Data Layer**: MySQL database schema, models, and persistence logic
- [ ] **Authentication System**: 钉钉OAuth integration and user authorization
- [ ] **Export & Templates**: Markdown generation and template management
- [ ] **Infrastructure Setup**: Deployment, monitoring, and security configuration
- [ ] **Testing & Validation**: Comprehensive test suite and quality validation

## Dependencies

### External Service Dependencies
- **LLM API Provider**: 阿里百炼DashScope API with Qwen models for prompt generation and QA
- **Authentication Provider**: 钉钉OAuth API for user authentication and profile management
- **Cloud Platform**: 阿里云 for hosting, MySQL RDS, and Redis instances
- **Container Registry**: 阿里云容器镜像服务 for Docker image storage

### Internal Team Dependencies
- **UX/UI Design**: Component mockups and user experience flows
- **Security Review**: Data handling, authentication, and compliance validation
- **DevOps**: Infrastructure setup, CI/CD pipelines, deployment automation
- **Product Validation**: User acceptance testing and feature prioritization

### Critical Path Items
1. 阿里百炼DashScope API access and Qwen model integration
2. 钉钉OAuth application registration and API access
3. UI/UX design completion for core workflows
4. MySQL database schema design and migration strategy

## Success Criteria (Technical)

### Performance Benchmarks
- **API Response Time**: ≤ 3s for parsing, ≤ 5s for form generation
- **Concurrent Users**: Support 100+ simultaneous sessions
- **Uptime**: 99.5% availability during business hours
- **AI API Efficiency**: ≤ 3 LLM calls per prompt optimization cycle

### Quality Gates
- **Code Coverage**: ≥ 80% unit test coverage for core business logic
- **Security Scan**: Zero high-severity vulnerabilities
- **Performance**: Load testing validation for target user capacity
- **Accessibility**: WCAG 2.1 AA compliance for public-facing components

### Acceptance Criteria
- **E2E Workflow**: Complete prompt generation from description to export
- **Quality Scoring**: PEQA system produces consistent 85+ quality scores
- **Multi-language**: Chinese/English interface support
- **Enterprise Integration**: 钉钉OAuth authentication and audit logging

## Estimated Effort

### Overall Timeline
- **MVP Development**: 4 months (Core features + basic UI)
- **Feature Complete**: 6 months (Templates, collaboration, advanced QA)
- **Enterprise Ready**: 8 months (Security, compliance, production deployment)

### Resource Requirements
- **Frontend Developer**: 2 engineers (React, TypeScript, UI/UX implementation)
- **Backend Developer**: 2 engineers (Python, FastAPI, LangChain, AI integration)
- **DevOps Engineer**: 1 engineer (Infrastructure, deployment, monitoring)
- **QA Engineer**: 1 engineer (pytest, testing, validation, quality assurance)

### Critical Path Items
1. **Python Backend Setup** (Month 1): FastAPI + 阿里百炼DashScope Python SDK + LangChain foundation
2. **Core Parsing Logic** (Month 1-2): LangChain Python agents for form generation
3. **Frontend Framework** (Month 2-3): React UI development with FastAPI integration
4. **Quality System** (Month 3-4): PEQA agent implementation and async scoring
5. **钉钉Authentication** (Month 4-5): python-jose OAuth integration for production readiness

## Tasks Created
- [ ] #3 - Project Setup and Environment Configuration (parallel: false)
- [ ] #4 - MySQL Database Schema Design and Setup (parallel: true)
- [ ] #5 - 阿里百炼DashScope API Integration (parallel: true)
- [ ] #6 - LangChain Framework Setup and Agent Architecture (parallel: false)
- [ ] #7 - PE Engineer Agent Implementation (parallel: true)
- [ ] #8 - PEQA Quality Assessment Agent Implementation (parallel: true)
- [ ] #9 - Backend API Server and Core Services Setup (parallel: false)
- [ ] #10 - 钉钉OAuth Authentication Implementation (parallel: true)
- [ ] #11 - Prompt Management and Versioning System (parallel: true)
- [ ] #12 - Frontend React Application Setup and Routing (parallel: true)

Total tasks: 10
Parallel tasks: 7
Sequential tasks: 3
