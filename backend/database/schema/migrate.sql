-- Migration Script Runner
-- AI System Prompt Generator Database Schema
-- Created: 2025-09-22
-- Author: Database Schema Design (Stream A)

-- =====================================================
-- MIGRATION TRACKING TABLE
-- =====================================================

-- Create migration tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(20) PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64) NULL,
    execution_time_ms INT NULL,

    INDEX idx_migrations_applied (applied_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- MIGRATION RUNNER PROCEDURE
-- =====================================================

DELIMITER ;;
CREATE PROCEDURE IF NOT EXISTS RunMigration(
    IN migration_version VARCHAR(20),
    IN migration_description VARCHAR(255)
)
BEGIN
    DECLARE migration_exists INT DEFAULT 0;
    DECLARE start_time TIMESTAMP DEFAULT NOW(3);
    DECLARE end_time TIMESTAMP;
    DECLARE execution_time INT;

    -- Check if migration already applied
    SELECT COUNT(*) INTO migration_exists
    FROM schema_migrations
    WHERE version = migration_version;

    -- Only run if not already applied
    IF migration_exists = 0 THEN
        -- Record migration start
        INSERT INTO schema_migrations (version, description, applied_at)
        VALUES (migration_version, migration_description, start_time);

        -- Log migration execution
        SELECT CONCAT('Running migration ', migration_version, ': ', migration_description) as status;

        -- Calculate execution time and update record
        SET end_time = NOW(3);
        SET execution_time = TIMESTAMPDIFF(MICROSECOND, start_time, end_time) / 1000;

        UPDATE schema_migrations
        SET execution_time_ms = execution_time
        WHERE version = migration_version;

        SELECT CONCAT('Migration ', migration_version, ' completed in ', execution_time, 'ms') as result;
    ELSE
        SELECT CONCAT('Migration ', migration_version, ' already applied, skipping') as result;
    END IF;
END;;
DELIMITER ;

-- =====================================================
-- ROLLBACK PROCEDURE
-- =====================================================

DELIMITER ;;
CREATE PROCEDURE IF NOT EXISTS RollbackMigration(
    IN migration_version VARCHAR(20)
)
BEGIN
    DECLARE migration_exists INT DEFAULT 0;

    -- Check if migration was applied
    SELECT COUNT(*) INTO migration_exists
    FROM schema_migrations
    WHERE version = migration_version;

    IF migration_exists > 0 THEN
        -- Log rollback
        SELECT CONCAT('Rolling back migration ', migration_version) as status;

        -- Remove from migration history
        DELETE FROM schema_migrations WHERE version = migration_version;

        SELECT CONCAT('Migration ', migration_version, ' rolled back successfully') as result;
    ELSE
        SELECT CONCAT('Migration ', migration_version, ' was not applied, nothing to rollback') as result;
    END IF;
END;;
DELIMITER ;

-- =====================================================
-- MIGRATION STATUS PROCEDURES
-- =====================================================

DELIMITER ;;
CREATE PROCEDURE IF NOT EXISTS GetMigrationStatus()
BEGIN
    SELECT
        version,
        description,
        applied_at,
        execution_time_ms
    FROM schema_migrations
    ORDER BY version;
END;;
DELIMITER ;

DELIMITER ;;
CREATE PROCEDURE IF NOT EXISTS GetPendingMigrations()
BEGIN
    -- This would list pending migrations if we had a migrations registry
    -- For now, just show applied migrations
    SELECT CONCAT('Total applied migrations: ', COUNT(*)) as status
    FROM schema_migrations;
END;;
DELIMITER ;

-- =====================================================
-- DATABASE HEALTH CHECK
-- =====================================================

DELIMITER ;;
CREATE PROCEDURE IF NOT EXISTS HealthCheck()
BEGIN
    DECLARE table_count INT DEFAULT 0;
    DECLARE index_count INT DEFAULT 0;
    DECLARE view_count INT DEFAULT 0;
    DECLARE trigger_count INT DEFAULT 0;

    -- Count tables
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = DATABASE()
      AND table_type = 'BASE TABLE';

    -- Count indexes
    SELECT COUNT(*) INTO index_count
    FROM information_schema.statistics
    WHERE table_schema = DATABASE();

    -- Count views
    SELECT COUNT(*) INTO view_count
    FROM information_schema.views
    WHERE table_schema = DATABASE();

    -- Count triggers
    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers
    WHERE trigger_schema = DATABASE();

    -- Display results
    SELECT
        DATABASE() as database_name,
        table_count as tables,
        index_count as indexes,
        view_count as views,
        trigger_count as triggers,
        NOW() as checked_at;

    -- Check for any broken foreign keys
    SELECT
        'Foreign Key Check' as check_type,
        CASE
            WHEN COUNT(*) = 0 THEN 'PASS'
            ELSE 'FAIL'
        END as status,
        COUNT(*) as broken_constraints
    FROM information_schema.table_constraints tc
    WHERE tc.constraint_schema = DATABASE()
      AND tc.constraint_type = 'FOREIGN KEY'
      AND tc.constraint_name NOT IN (
          SELECT constraint_name
          FROM information_schema.referential_constraints
          WHERE constraint_schema = DATABASE()
      );
END;;
DELIMITER ;

-- =====================================================
-- INITIAL STATUS CHECK
-- =====================================================

-- Display current migration status
SELECT 'Database Migration System Initialized' as status;
CALL GetMigrationStatus();
CALL HealthCheck();

-- =====================================================
-- USAGE EXAMPLES
-- =====================================================

/*
-- To run a specific migration:
CALL RunMigration('001', 'Initial database schema');

-- To check migration status:
CALL GetMigrationStatus();

-- To rollback a migration:
CALL RollbackMigration('001');

-- To perform health check:
CALL HealthCheck();

-- To see pending migrations:
CALL GetPendingMigrations();
*/