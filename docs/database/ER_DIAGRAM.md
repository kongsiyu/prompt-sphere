# AI System Prompt Generator - Entity Relationship Diagram

## Overview
This document describes the database schema for the AI System Prompt Generator application, including entity relationships, constraints, and design decisions.

## Entity Relationship Diagram

```
┌─────────────────┐         ┌─────────────────┐
│     USERS       │         │   TEMPLATES     │
│─────────────────│         │─────────────────│
│ id (UUID) PK    │         │ id (UUID) PK    │
│ email           │         │ name            │
│ password_hash   │         │ description     │
│ full_name       │         │ content         │
│ role            │         │ category        │
│ is_active       │         │ is_public       │
│ email_verified  │         │ usage_count     │
│ last_login_at   │         │ created_by FK   │───┐
│ created_at      │         │ created_at      │   │
│ updated_at      │         │ updated_at      │   │
│ deleted_at      │         │ deleted_at      │   │
└─────────────────┘         └─────────────────┘   │
         │                           │            │
         │                           └────────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────┐
│   CONVERSATIONS │
│─────────────────│
│ id (UUID) PK    │
│ user_id FK      │
│ title           │
│ context         │
│ status          │
│ total_messages  │
│ created_at      │
│ updated_at      │
│ deleted_at      │
└─────────────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────┐         ┌─────────────────┐
│     PROMPTS     │         │   AUDIT_LOGS    │
│─────────────────│         │─────────────────│
│ id (UUID) PK    │         │ id (UUID) PK    │
│ conversation_id │         │ user_id FK      │
│ template_id FK  │         │ entity_type     │
│ version         │         │ entity_id       │
│ content         │         │ action          │
│ system_prompt   │         │ old_values      │
│ user_input      │         │ new_values      │
│ ai_response     │         │ ip_address      │
│ response_time   │         │ user_agent      │
│ token_count     │         │ created_at      │
│ model_used      │         │ metadata        │
│ status          │         └─────────────────┘
│ created_at      │                   │
│ updated_at      │                   │
│ deleted_at      │                   │
└─────────────────┘                   │
         │                            │
         │ N:1                        │ N:1
         └────────────────────────────┘
```

## Entity Descriptions

### Users
Core user management table with authentication and profile information.
- **Primary Key**: UUID for scalability and security
- **Unique Constraints**: email
- **Soft Delete**: Implemented via deleted_at timestamp
- **Security**: Passwords are hashed using bcrypt

### Templates
Reusable prompt templates that can be shared between users.
- **Primary Key**: UUID
- **Foreign Keys**: created_by references users(id)
- **Access Control**: is_public flag for sharing templates
- **Usage Tracking**: usage_count for analytics

### Conversations
Groups related prompts into conversation threads.
- **Primary Key**: UUID
- **Foreign Keys**: user_id references users(id)
- **Metadata**: Tracks total messages and status
- **Organization**: Provides context for prompt sequences

### Prompts
Individual prompt-response pairs with full interaction data.
- **Primary Key**: UUID
- **Foreign Keys**:
  - conversation_id references conversations(id)
  - template_id references templates(id) (optional)
- **Versioning**: Version field for prompt evolution tracking
- **Performance**: Token count and response time metrics
- **AI Integration**: Stores model used and complete interaction

### Audit_logs
Comprehensive audit trail for all system activities.
- **Primary Key**: UUID
- **Foreign Keys**: user_id references users(id)
- **Flexibility**: JSON columns for old_values, new_values, metadata
- **Security**: IP address and user agent tracking
- **Coverage**: All CRUD operations on sensitive entities

## Key Design Decisions

### UUID Primary Keys
- Better for distributed systems
- Security through obscurity
- No information leakage about record counts
- Better for API design

### Soft Delete Pattern
- Data retention for audit and recovery
- Maintains referential integrity
- Implemented on all user-generated content
- Performance consideration with indexes

### Timestamp Strategy
- created_at: Record creation time
- updated_at: Last modification time
- deleted_at: Soft delete timestamp (NULL = active)

### JSON Columns
- audit_logs.old_values: Previous state
- audit_logs.new_values: New state
- audit_logs.metadata: Additional context
- conversations.context: Session context data

## Relationships

1. **Users → Conversations** (1:N)
   - One user can have many conversations
   - CASCADE DELETE on user deletion

2. **Users → Templates** (1:N)
   - One user can create many templates
   - SET NULL on user deletion (preserve public templates)

3. **Conversations → Prompts** (1:N)
   - One conversation contains many prompts
   - CASCADE DELETE on conversation deletion

4. **Templates → Prompts** (1:N, Optional)
   - One template can be used in many prompts
   - SET NULL on template deletion

5. **Users → Audit_logs** (1:N)
   - One user generates many audit entries
   - RESTRICT DELETE (preserve audit trail)

## Constraints and Rules

### Data Integrity
- All foreign keys enforce referential integrity
- NOT NULL constraints on critical fields
- CHECK constraints for enum-like fields (status, role)
- Length limits on text fields

### Cascading Rules
- User deletion: CASCADE conversations, SET NULL templates
- Conversation deletion: CASCADE prompts
- Template deletion: SET NULL in prompts
- Audit logs: RESTRICT all deletions

### Indexing Strategy
- Primary keys: Clustered indexes (automatic)
- Foreign keys: Non-clustered indexes for JOIN performance
- Search columns: Composite indexes for common queries
- Temporal queries: Indexes on timestamp columns