-- Migration: 002_triggers_and_views.sql
-- Description: Add triggers for automatic updates and views for common queries
-- Created: 2025-09-22
-- Author: Database Schema Design (Stream A)

-- Migration metadata
INSERT INTO schema_migrations (version, description, applied_at) VALUES
('002', 'Add triggers and views', NOW())
ON DUPLICATE KEY UPDATE applied_at = applied_at;

SET AUTOCOMMIT = 0;
START TRANSACTION;

-- =====================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================

-- Update template usage count when used in prompts
DELIMITER ;;
CREATE TRIGGER tr_prompts_template_usage
AFTER INSERT ON prompts
FOR EACH ROW
BEGIN
    IF NEW.template_id IS NOT NULL THEN
        UPDATE templates
        SET usage_count = usage_count + 1
        WHERE id = NEW.template_id;
    END IF;
END;;
DELIMITER ;

-- Update conversation message count and last activity
DELIMITER ;;
CREATE TRIGGER tr_prompts_conversation_update
AFTER INSERT ON prompts
FOR EACH ROW
BEGIN
    UPDATE conversations
    SET
        total_messages = total_messages + 1,
        total_tokens = total_tokens + COALESCE(NEW.token_count_total, 0),
        total_cost = total_cost + COALESCE(NEW.cost, 0),
        last_activity_at = NOW()
    WHERE id = NEW.conversation_id;
END;;
DELIMITER ;

-- Update template ratings when rating is added
DELIMITER ;;
CREATE TRIGGER tr_template_ratings_avg_insert
AFTER INSERT ON template_ratings
FOR EACH ROW
BEGIN
    UPDATE templates
    SET
        rating_avg = (
            SELECT AVG(rating)
            FROM template_ratings
            WHERE template_id = NEW.template_id
        ),
        rating_count = (
            SELECT COUNT(*)
            FROM template_ratings
            WHERE template_id = NEW.template_id
        )
    WHERE id = NEW.template_id;
END;;
DELIMITER ;

-- Update template ratings when rating is updated
DELIMITER ;;
CREATE TRIGGER tr_template_ratings_avg_update
AFTER UPDATE ON template_ratings
FOR EACH ROW
BEGIN
    UPDATE templates
    SET
        rating_avg = (
            SELECT AVG(rating)
            FROM template_ratings
            WHERE template_id = NEW.template_id
        ),
        rating_count = (
            SELECT COUNT(*)
            FROM template_ratings
            WHERE template_id = NEW.template_id
        )
    WHERE id = NEW.template_id;
END;;
DELIMITER ;

-- Update template ratings when rating is deleted
DELIMITER ;;
CREATE TRIGGER tr_template_ratings_avg_delete
AFTER DELETE ON template_ratings
FOR EACH ROW
BEGIN
    UPDATE templates
    SET
        rating_avg = (
            SELECT AVG(rating)
            FROM template_ratings
            WHERE template_id = OLD.template_id
        ),
        rating_count = (
            SELECT COUNT(*)
            FROM template_ratings
            WHERE template_id = OLD.template_id
        )
    WHERE id = OLD.template_id;
END;;
DELIMITER ;

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Active users with recent activity
CREATE VIEW v_active_users AS
SELECT
    u.*,
    COUNT(DISTINCT c.id) as conversation_count,
    COUNT(DISTINCT p.id) as prompt_count,
    MAX(c.last_activity_at) as last_conversation_activity
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id AND c.deleted_at IS NULL
LEFT JOIN prompts p ON c.id = p.conversation_id AND p.deleted_at IS NULL
WHERE u.deleted_at IS NULL
    AND u.is_active = TRUE
GROUP BY u.id;

-- Popular templates with ratings
CREATE VIEW v_popular_templates AS
SELECT
    t.*,
    u.full_name as creator_name,
    COALESCE(t.rating_avg, 0) as avg_rating,
    t.rating_count,
    t.usage_count
FROM templates t
LEFT JOIN users u ON t.created_by = u.id
WHERE t.deleted_at IS NULL
    AND t.is_public = TRUE
ORDER BY t.usage_count DESC, t.rating_avg DESC;

-- Conversation summary with statistics
CREATE VIEW v_conversation_summary AS
SELECT
    c.*,
    u.full_name as owner_name,
    COUNT(p.id) as message_count,
    SUM(p.token_count_total) as total_tokens_used,
    SUM(p.cost) as total_cost,
    AVG(p.response_time_ms) as avg_response_time,
    MAX(p.created_at) as last_message_at
FROM conversations c
LEFT JOIN users u ON c.user_id = u.id
LEFT JOIN prompts p ON c.id = p.conversation_id AND p.deleted_at IS NULL
WHERE c.deleted_at IS NULL
GROUP BY c.id;

-- User activity dashboard
CREATE VIEW v_user_dashboard AS
SELECT
    u.id as user_id,
    u.full_name,
    u.email,
    u.last_login_at,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT CASE WHEN c.status = 'active' THEN c.id END) as active_conversations,
    COUNT(DISTINCT p.id) as total_prompts,
    SUM(COALESCE(p.token_count_total, 0)) as total_tokens_used,
    SUM(COALESCE(p.cost, 0)) as total_cost,
    COUNT(DISTINCT t.id) as templates_created,
    COUNT(DISTINCT tr.id) as templates_rated,
    MAX(c.last_activity_at) as last_activity_at
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id AND c.deleted_at IS NULL
LEFT JOIN prompts p ON c.id = p.conversation_id AND p.deleted_at IS NULL
LEFT JOIN templates t ON u.id = t.created_by AND t.deleted_at IS NULL
LEFT JOIN template_ratings tr ON u.id = tr.user_id
WHERE u.deleted_at IS NULL
GROUP BY u.id;

-- Template performance analytics
CREATE VIEW v_template_analytics AS
SELECT
    t.id,
    t.name,
    t.category,
    t.created_by,
    u.full_name as creator_name,
    t.usage_count,
    t.rating_avg,
    t.rating_count,
    COUNT(DISTINCT p.id) as prompt_usage_count,
    AVG(p.response_time_ms) as avg_response_time,
    AVG(p.token_count_total) as avg_tokens_per_use,
    SUM(p.cost) as total_cost_generated,
    COUNT(DISTINCT p.user_rating) as user_feedback_count,
    AVG(p.user_rating) as avg_user_rating
FROM templates t
LEFT JOIN users u ON t.created_by = u.id
LEFT JOIN prompts p ON t.id = p.template_id AND p.deleted_at IS NULL AND p.status = 'completed'
WHERE t.deleted_at IS NULL
GROUP BY t.id;

-- Security audit view
CREATE VIEW v_security_audit AS
SELECT
    al.id,
    al.user_id,
    u.email,
    u.full_name,
    al.action,
    al.entity_type,
    al.severity,
    al.ip_address,
    al.user_agent,
    al.created_at,
    al.custom_metadata
FROM audit_logs al
LEFT JOIN users u ON al.user_id = u.id
WHERE al.severity IN ('HIGH', 'CRITICAL')
   OR al.action IN ('LOGIN', 'LOGOUT', 'DELETE')
   OR al.category = 'security'
ORDER BY al.created_at DESC;

-- System usage statistics
CREATE VIEW v_system_stats AS
SELECT
    'users' as metric,
    COUNT(*) as total_count,
    COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_count,
    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) as created_last_30_days
FROM users
UNION ALL
SELECT
    'conversations' as metric,
    COUNT(*) as total_count,
    COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_count,
    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) as created_last_30_days
FROM conversations
UNION ALL
SELECT
    'templates' as metric,
    COUNT(*) as total_count,
    COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_count,
    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) as created_last_30_days
FROM templates
UNION ALL
SELECT
    'prompts' as metric,
    COUNT(*) as total_count,
    COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_count,
    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) as created_last_30_days
FROM prompts;

COMMIT;

-- Verify migration
SELECT 'Migration 002 completed successfully' as status;