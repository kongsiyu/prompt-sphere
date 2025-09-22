-- Migration: 001_initial_schema.sql
-- Description: Initial database schema for AI System Prompt Generator
-- Created: 2025-09-22
-- Author: Database Schema Design (Stream A)

-- Migration metadata
INSERT INTO schema_migrations (version, description, applied_at) VALUES
('001', 'Initial database schema', NOW())
ON DUPLICATE KEY UPDATE applied_at = applied_at;

-- Set session parameters
SET FOREIGN_KEY_CHECKS = 1;
SET AUTOCOMMIT = 0;

START TRANSACTION;

-- =====================================================
-- USERS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('admin', 'user', 'viewer') NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verification_token VARCHAR(255) NULL,
    password_reset_token VARCHAR(255) NULL,
    password_reset_expires DATETIME NULL,
    last_login_at DATETIME NULL,
    login_attempts INT NOT NULL DEFAULT 0,
    locked_until DATETIME NULL,
    preferences JSON NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,

    INDEX idx_users_email (email),
    INDEX idx_users_active (is_active),
    INDEX idx_users_created (created_at),
    INDEX idx_users_deleted (deleted_at),
    INDEX idx_users_email_verified (email_verified),
    INDEX idx_users_last_login (last_login_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TEMPLATES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS templates (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    content TEXT NOT NULL,
    system_prompt TEXT NULL,
    category VARCHAR(100) NULL,
    tags JSON NULL DEFAULT '[]',
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    usage_count INT NOT NULL DEFAULT 0,
    rating_avg DECIMAL(3,2) NULL DEFAULT NULL,
    rating_count INT NOT NULL DEFAULT 0,
    created_by CHAR(36) NOT NULL,
    version INT NOT NULL DEFAULT 1,
    parent_template_id CHAR(36) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,

    FOREIGN KEY fk_templates_created_by (created_by)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY fk_templates_parent (parent_template_id)
        REFERENCES templates(id) ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_templates_created_by (created_by),
    INDEX idx_templates_public (is_public),
    INDEX idx_templates_category (category),
    INDEX idx_templates_usage (usage_count),
    INDEX idx_templates_rating (rating_avg, rating_count),
    INDEX idx_templates_created (created_at),
    INDEX idx_templates_deleted (deleted_at),
    INDEX idx_templates_parent (parent_template_id),
    FULLTEXT INDEX ft_templates_search (name, description, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- CONVERSATIONS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS conversations (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    context JSON NULL DEFAULT '{}',
    status ENUM('active', 'archived', 'paused', 'completed') NOT NULL DEFAULT 'active',
    total_messages INT NOT NULL DEFAULT 0,
    total_tokens INT NOT NULL DEFAULT 0,
    total_cost DECIMAL(10,6) NOT NULL DEFAULT 0.000000,
    last_activity_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    settings JSON NULL DEFAULT '{}',
    shared BOOLEAN NOT NULL DEFAULT FALSE,
    share_token VARCHAR(255) NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,

    FOREIGN KEY fk_conversations_user_id (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,

    INDEX idx_conversations_user_id (user_id),
    INDEX idx_conversations_status (status),
    INDEX idx_conversations_activity (last_activity_at),
    INDEX idx_conversations_created (created_at),
    INDEX idx_conversations_deleted (deleted_at),
    INDEX idx_conversations_shared (shared),
    INDEX idx_conversations_share_token (share_token),
    FULLTEXT INDEX ft_conversations_search (title, description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- PROMPTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS prompts (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    conversation_id CHAR(36) NOT NULL,
    template_id CHAR(36) NULL,
    version INT NOT NULL DEFAULT 1,
    parent_prompt_id CHAR(36) NULL,
    sequence_number INT NOT NULL,

    content TEXT NOT NULL,
    system_prompt TEXT NULL,
    user_input TEXT NOT NULL,

    ai_response TEXT NULL,
    response_time_ms INT NULL,
    token_count_input INT NULL,
    token_count_output INT NULL,
    token_count_total INT NULL,
    cost DECIMAL(10,6) NULL DEFAULT 0.000000,

    model_used VARCHAR(100) NULL,
    model_version VARCHAR(50) NULL,
    temperature DECIMAL(3,2) NULL,
    max_tokens INT NULL,

    status ENUM('pending', 'processing', 'completed', 'failed', 'cancelled') NOT NULL DEFAULT 'pending',
    error_message TEXT NULL,
    metadata JSON NULL DEFAULT '{}',

    user_rating TINYINT NULL CHECK (user_rating BETWEEN 1 AND 5),
    user_feedback TEXT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,

    FOREIGN KEY fk_prompts_conversation_id (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY fk_prompts_template_id (template_id)
        REFERENCES templates(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY fk_prompts_parent (parent_prompt_id)
        REFERENCES prompts(id) ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_prompts_conversation_id (conversation_id),
    INDEX idx_prompts_template_id (template_id),
    INDEX idx_prompts_status (status),
    INDEX idx_prompts_sequence (conversation_id, sequence_number),
    INDEX idx_prompts_created (created_at),
    INDEX idx_prompts_deleted (deleted_at),
    INDEX idx_prompts_rating (user_rating),
    INDEX idx_prompts_model (model_used),
    INDEX idx_prompts_parent (parent_prompt_id),
    INDEX idx_prompts_tokens (token_count_total),
    INDEX idx_prompts_cost (cost),
    FULLTEXT INDEX ft_prompts_search (content, user_input, ai_response)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- AUDIT_LOGS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NULL,
    session_id VARCHAR(255) NULL,

    entity_type VARCHAR(100) NOT NULL,
    entity_id CHAR(36) NULL,
    action ENUM('CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'EXPORT', 'SHARE') NOT NULL,

    old_values JSON NULL,
    new_values JSON NULL,
    changes JSON NULL,

    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    request_id VARCHAR(255) NULL,
    endpoint VARCHAR(255) NULL,
    method ENUM('GET', 'POST', 'PUT', 'PATCH', 'DELETE') NULL,

    metadata JSON NULL DEFAULT '{}',
    severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'LOW',
    category VARCHAR(50) NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY fk_audit_logs_user_id (user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,

    INDEX idx_audit_logs_user_id (user_id),
    INDEX idx_audit_logs_entity (entity_type, entity_id),
    INDEX idx_audit_logs_action (action),
    INDEX idx_audit_logs_created (created_at),
    INDEX idx_audit_logs_ip (ip_address),
    INDEX idx_audit_logs_severity (severity),
    INDEX idx_audit_logs_category (category),
    INDEX idx_audit_logs_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TEMPLATE_RATINGS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS template_ratings (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    template_id CHAR(36) NOT NULL,
    user_id CHAR(36) NOT NULL,
    rating TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    feedback TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY fk_template_ratings_template (template_id)
        REFERENCES templates(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY fk_template_ratings_user (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,

    UNIQUE KEY uk_template_ratings (template_id, user_id),

    INDEX idx_template_ratings_template (template_id),
    INDEX idx_template_ratings_user (user_id),
    INDEX idx_template_ratings_rating (rating),
    INDEX idx_template_ratings_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- CONVERSATION_PARTICIPANTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS conversation_participants (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    conversation_id CHAR(36) NOT NULL,
    user_id CHAR(36) NOT NULL,
    role ENUM('owner', 'collaborator', 'viewer') NOT NULL DEFAULT 'viewer',
    permissions JSON NOT NULL DEFAULT '{"read": true, "write": false, "admin": false}',
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP NULL,

    FOREIGN KEY fk_conv_participants_conv (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY fk_conv_participants_user (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,

    UNIQUE KEY uk_conversation_participants (conversation_id, user_id),

    INDEX idx_conv_participants_conv (conversation_id),
    INDEX idx_conv_participants_user (user_id),
    INDEX idx_conv_participants_role (role),
    INDEX idx_conv_participants_joined (joined_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMIT;

-- Verify migration
SELECT 'Migration 001 completed successfully' as status;