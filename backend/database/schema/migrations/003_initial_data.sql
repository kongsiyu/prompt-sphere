-- Migration: 003_initial_data.sql
-- Description: Insert initial data including admin user and sample templates
-- Created: 2025-09-22
-- Author: Database Schema Design (Stream A)

-- Migration metadata
INSERT INTO schema_migrations (version, description, applied_at) VALUES
('003', 'Insert initial data and sample content', NOW())
ON DUPLICATE KEY UPDATE applied_at = applied_at;

SET AUTOCOMMIT = 0;
START TRANSACTION;

-- =====================================================
-- INITIAL ADMIN USER
-- =====================================================

-- Create admin user (password: admin123 - CHANGE IN PRODUCTION!)
INSERT INTO users (id, email, password_hash, full_name, role, is_active, email_verified, preferences)
VALUES (
    UUID(),
    'admin@promptsphere.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3fp6joq/EO', -- admin123
    'System Administrator',
    'admin',
    TRUE,
    TRUE,
    JSON_OBJECT(
        'theme', 'dark',
        'language', 'en',
        'notifications', JSON_OBJECT('email', true, 'push', false),
        'ai_settings', JSON_OBJECT(
            'default_model', 'gpt-4',
            'temperature', 0.7,
            'max_tokens', 2000
        )
    )
) ON DUPLICATE KEY UPDATE email = email;

-- Get admin user ID for template creation
SET @admin_id = (SELECT id FROM users WHERE email = 'admin@promptsphere.com' LIMIT 1);

-- =====================================================
-- SAMPLE TEMPLATES
-- =====================================================

-- Code Review Template
INSERT INTO templates (
    id, name, description, content, system_prompt, category, tags, is_public, created_by
) VALUES (
    UUID(),
    'Code Review Assistant',
    'Template for comprehensive code review with AI assistance focusing on quality, security, and best practices.',
    'Please review the following code for:
- Code quality and readability
- Security vulnerabilities
- Performance issues
- Best practices adherence
- Potential bugs or edge cases

Code to review:
```{language}
{code}
```

Additional context: {context}',
    'You are an expert code reviewer with extensive experience in software development. Provide constructive, actionable feedback focusing on code quality, security, performance, and best practices. Be thorough but concise, and suggest specific improvements where possible.',
    'Development',
    JSON_ARRAY('code-review', 'development', 'quality-assurance', 'security'),
    TRUE,
    @admin_id
);

-- Technical Documentation Template
INSERT INTO templates (
    id, name, description, content, system_prompt, category, tags, is_public, created_by
) VALUES (
    UUID(),
    'Technical Documentation Writer',
    'Generate comprehensive technical documentation for code, APIs, and systems.',
    'Create technical documentation for the following:

Subject: {subject}
Type: {doc_type}
Audience: {audience}
Detail Level: {detail_level}

Content to document:
{content}

Requirements:
- Clear, concise explanations
- Proper formatting with headers and sections
- Code examples where appropriate
- Prerequisites and dependencies
- Troubleshooting section if applicable',
    'You are a technical writer specializing in creating clear, comprehensive documentation for software systems. Write documentation that is accessible to the target audience while being thorough and accurate. Use proper markdown formatting and include practical examples.',
    'Documentation',
    JSON_ARRAY('documentation', 'technical-writing', 'api-docs', 'guides'),
    TRUE,
    @admin_id
);

-- Data Analysis Template
INSERT INTO templates (
    id, name, description, content, system_prompt, category, tags, is_public, created_by
) VALUES (
    UUID(),
    'Data Analysis Assistant',
    'Analyze datasets and generate insights with statistical analysis and visualizations.',
    'Analyze the following dataset and provide insights:

Dataset Description: {dataset_description}
Analysis Goal: {analysis_goal}
Data Sample:
{data_sample}

Please provide:
1. Initial data observations
2. Statistical summary
3. Key insights and patterns
4. Visualization recommendations
5. Potential next steps for analysis

Focus areas: {focus_areas}',
    'You are a data analyst with expertise in statistical analysis, data visualization, and business intelligence. Provide clear, actionable insights from data while explaining your methodology. Suggest appropriate visualizations and statistical tests.',
    'Analytics',
    JSON_ARRAY('data-analysis', 'statistics', 'visualization', 'insights'),
    TRUE,
    @admin_id
);

-- Creative Writing Template
INSERT INTO templates (
    id, name, description, content, system_prompt, category, tags, is_public, created_by
) VALUES (
    UUID(),
    'Creative Writing Assistant',
    'Generate creative content including stories, poetry, and creative copy.',
    'Create a {content_type} with the following specifications:

Theme/Topic: {theme}
Style: {style}
Tone: {tone}
Length: {length}
Target Audience: {audience}

Additional Requirements:
{requirements}

Inspiration or Reference Material:
{inspiration}',
    'You are a creative writer with expertise in various forms of creative expression. Write engaging, original content that captures the specified style and tone. Be imaginative while staying true to the requirements.',
    'Creative',
    JSON_ARRAY('creative-writing', 'storytelling', 'content-creation', 'copy'),
    TRUE,
    @admin_id
);

-- Business Strategy Template
INSERT INTO templates (
    id, name, description, content, system_prompt, category, tags, is_public, created_by
) VALUES (
    UUID(),
    'Business Strategy Advisor',
    'Develop business strategies, analyze market opportunities, and create business plans.',
    'Provide business strategy advice for the following scenario:

Company/Industry: {company_industry}
Current Situation: {current_situation}
Challenge/Opportunity: {challenge_opportunity}
Goals: {goals}
Timeline: {timeline}
Resources Available: {resources}

Please analyze and provide:
1. Situation assessment
2. Strategic options
3. Recommended approach
4. Implementation plan
5. Risk assessment
6. Success metrics',
    'You are a business strategy consultant with expertise in market analysis, strategic planning, and business development. Provide practical, actionable advice based on established business frameworks and current market conditions.',
    'Business',
    JSON_ARRAY('strategy', 'business-planning', 'market-analysis', 'consulting'),
    TRUE,
    @admin_id
);

-- Educational Content Template
INSERT INTO templates (
    id, name, description, content, system_prompt, category, tags, is_public, created_by
) VALUES (
    UUID(),
    'Educational Content Creator',
    'Create educational materials, lesson plans, and learning content for various subjects.',
    'Create educational content for:

Subject: {subject}
Learning Level: {learning_level}
Learning Objectives: {learning_objectives}
Duration: {duration}
Format: {format}

Content Requirements:
- Clear learning outcomes
- Structured presentation
- Interactive elements where appropriate
- Assessment or practice questions
- Additional resources

Specific Topics to Cover:
{topics}

Special Considerations: {considerations}',
    'You are an educational content specialist with expertise in curriculum design and instructional methodology. Create engaging, well-structured learning materials that facilitate understanding and retention. Adapt content to the appropriate learning level.',
    'Education',
    JSON_ARRAY('education', 'curriculum', 'learning', 'teaching'),
    TRUE,
    @admin_id
);

-- =====================================================
-- SAMPLE AUDIT LOG ENTRIES
-- =====================================================

-- Log admin user creation
INSERT INTO audit_logs (
    id, user_id, entity_type, entity_id, action, new_values, severity, category, metadata
) VALUES (
    UUID(),
    @admin_id,
    'users',
    @admin_id,
    'CREATE',
    JSON_OBJECT('email', 'admin@promptsphere.com', 'role', 'admin', 'full_name', 'System Administrator'),
    'LOW',
    'system_initialization',
    JSON_OBJECT('source', 'initial_migration', 'automated', true)
);

-- Log template creation
INSERT INTO audit_logs (
    id, user_id, entity_type, action, severity, category, metadata
) VALUES (
    UUID(),
    @admin_id,
    'templates',
    'CREATE',
    'LOW',
    'system_initialization',
    JSON_OBJECT('source', 'initial_migration', 'template_count', 6, 'automated', true)
);

-- =====================================================
-- SAMPLE CONVERSATION AND PROMPTS
-- =====================================================

-- Create a sample conversation
SET @conversation_id = UUID();
INSERT INTO conversations (
    id, user_id, title, description, context, settings
) VALUES (
    @conversation_id,
    @admin_id,
    'Welcome to PromptSphere',
    'Sample conversation demonstrating the platform capabilities',
    JSON_OBJECT(
        'purpose', 'demonstration',
        'features_showcased', JSON_ARRAY('templates', 'conversations', 'ai_interaction')
    ),
    JSON_OBJECT(
        'ai_model', 'gpt-3.5-turbo',
        'temperature', 0.7,
        'max_tokens', 1500
    )
);

-- Create sample prompts
INSERT INTO prompts (
    id, conversation_id, template_id, sequence_number, content, user_input, ai_response,
    response_time_ms, token_count_input, token_count_output, token_count_total,
    model_used, status, user_rating
) VALUES (
    UUID(),
    @conversation_id,
    NULL,
    1,
    'Welcome to PromptSphere! This is an AI-powered prompt management system.',
    'Tell me about the capabilities of this platform.',
    'PromptSphere is a comprehensive AI prompt management platform that offers:\n\n1. **Template Library**: Pre-built, customizable prompt templates for various use cases\n2. **Conversation Management**: Organized chat histories with context preservation\n3. **Collaboration Features**: Share conversations and templates with team members\n4. **Analytics & Insights**: Track usage, costs, and performance metrics\n5. **Version Control**: Template versioning and prompt iteration tracking\n\nThe platform is designed to help teams and individuals work more effectively with AI by providing structure, organization, and collaboration tools around prompt engineering.',
    1250,
    25,
    95,
    120,
    'gpt-3.5-turbo',
    'completed',
    5
);

-- =====================================================
-- SYSTEM CONFIGURATION
-- =====================================================

-- Create system configuration table for runtime settings
CREATE TABLE IF NOT EXISTS system_config (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    config_key VARCHAR(255) NOT NULL UNIQUE,
    config_value JSON NOT NULL,
    description TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_system_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, description) VALUES
('app_version', '"1.0.0"', 'Current application version'),
('schema_version', '"1.0.0"', 'Current database schema version'),
('default_ai_model', '"gpt-3.5-turbo"', 'Default AI model for new conversations'),
('max_conversation_length', '100', 'Maximum number of prompts per conversation'),
('template_approval_required', 'false', 'Whether public templates require approval'),
('user_registration_open', 'true', 'Whether new user registration is allowed'),
('audit_retention_days', '365', 'Number of days to retain audit logs'),
('max_file_upload_size', '10485760', 'Maximum file upload size in bytes (10MB)'),
('rate_limits', JSON_OBJECT(
    'prompts_per_hour', 100,
    'templates_per_day', 10,
    'conversations_per_day', 50
), 'API rate limits for different operations');

COMMIT;

-- Verify migration and display summary
SELECT 'Migration 003 completed successfully' as status;

SELECT
    'Initial data summary:' as summary,
    (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL) as users_created,
    (SELECT COUNT(*) FROM templates WHERE deleted_at IS NULL) as templates_created,
    (SELECT COUNT(*) FROM conversations WHERE deleted_at IS NULL) as conversations_created,
    (SELECT COUNT(*) FROM prompts WHERE deleted_at IS NULL) as prompts_created,
    (SELECT COUNT(*) FROM system_config) as config_entries;