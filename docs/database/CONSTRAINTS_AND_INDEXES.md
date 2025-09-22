# Database Constraints and Indexes

## Foreign Key Constraints and Cascading Rules

### Overview
This document details all foreign key relationships, cascading rules, and indexing strategies implemented in the AI System Prompt Generator database schema.

### Foreign Key Relationships

#### 1. Users → Conversations
```sql
FOREIGN KEY (user_id) REFERENCES users(id)
ON DELETE CASCADE ON UPDATE CASCADE
```

**Rationale**: When a user is deleted, all their conversations should be removed as they are personal data. Conversations cannot exist without a user owner.

**Impact**: Cascading delete ensures data consistency and privacy compliance.

#### 2. Users → Templates (Creator)
```sql
FOREIGN KEY (created_by) REFERENCES users(id)
ON DELETE SET NULL ON UPDATE CASCADE
```

**Rationale**: Public templates should remain available even if the creator account is deleted. Setting to NULL preserves valuable community content.

**Impact**: Templates become orphaned but remain functional for public use.

#### 3. Templates → Templates (Parent/Child Versioning)
```sql
FOREIGN KEY (parent_template_id) REFERENCES templates(id)
ON DELETE SET NULL ON UPDATE CASCADE
```

**Rationale**: Template versioning should not break if parent is deleted. Child templates can stand alone.

**Impact**: Version history is partially preserved, children become root templates.

#### 4. Conversations → Prompts
```sql
FOREIGN KEY (conversation_id) REFERENCES conversations(id)
ON DELETE CASCADE ON UPDATE CASCADE
```

**Rationale**: Prompts are meaningless without their conversation context. They should be removed with the conversation.

**Impact**: Ensures no orphaned prompts exist in the system.

#### 5. Templates → Prompts (Optional Usage)
```sql
FOREIGN KEY (template_id) REFERENCES templates(id)
ON DELETE SET NULL ON UPDATE CASCADE
```

**Rationale**: Prompts should remain even if the template they were based on is deleted. The prompt content is preserved.

**Impact**: Historical prompts retain their content but lose template association.

#### 6. Prompts → Prompts (Parent/Child Chains)
```sql
FOREIGN KEY (parent_prompt_id) REFERENCES prompts(id)
ON DELETE SET NULL ON UPDATE CASCADE
```

**Rationale**: Prompt chains should not break entirely if a parent is deleted. Children can continue as independent prompts.

**Impact**: Conversation flow is preserved, though some context may be lost.

#### 7. Users → Audit Logs
```sql
FOREIGN KEY (user_id) REFERENCES users(id)
ON DELETE RESTRICT ON UPDATE CASCADE
```

**Rationale**: Audit trails must be preserved for compliance and security. Users cannot be deleted if audit logs exist.

**Impact**: Requires cleanup of audit logs before user deletion, or soft-delete implementation.

#### 8. Templates → Template Ratings
```sql
FOREIGN KEY (template_id) REFERENCES templates(id)
ON DELETE CASCADE ON UPDATE CASCADE
```

**Rationale**: Ratings are meaningless without the template they rate.

**Impact**: All ratings are removed when template is deleted.

#### 9. Users → Template Ratings
```sql
FOREIGN KEY (user_id) REFERENCES users(id)
ON DELETE CASCADE ON UPDATE CASCADE
```

**Rationale**: User ratings should be removed with the user for privacy.

**Impact**: Template rating averages need recalculation after user deletion.

#### 10. Conversations → Conversation Participants
```sql
FOREIGN KEY (conversation_id) REFERENCES conversations(id)
ON DELETE CASCADE ON UPDATE CASCADE
```

**Rationale**: Participants list is meaningless without the conversation.

**Impact**: All sharing and collaboration data is removed with conversation.

#### 11. Users → Conversation Participants
```sql
FOREIGN KEY (user_id) REFERENCES users(id)
ON DELETE CASCADE ON UPDATE CASCADE
```

**Rationale**: Participation records should be removed with user deletion.

**Impact**: Shared conversations lose participants but remain accessible to remaining users.

## Index Strategy

### Primary Indexes (Automatic)
All tables have clustered indexes on their UUID primary keys for fast lookups.

### Foreign Key Indexes
```sql
-- User relationships
INDEX idx_conversations_user_id (user_id)
INDEX idx_templates_created_by (created_by)
INDEX idx_prompts_conversation_id (conversation_id)
INDEX idx_audit_logs_user_id (user_id)

-- Template relationships
INDEX idx_prompts_template_id (template_id)
INDEX idx_template_ratings_template (template_id)
INDEX idx_templates_parent (parent_template_id)

-- Prompt relationships
INDEX idx_prompts_parent (parent_prompt_id)
```

### Query Performance Indexes

#### User Management
```sql
INDEX idx_users_email (email)              -- Login queries
INDEX idx_users_active (is_active)         -- Active user filtering
INDEX idx_users_email_verified (email_verified) -- Verification status
INDEX idx_users_last_login (last_login_at) -- Activity tracking
```

#### Content Discovery
```sql
INDEX idx_templates_public (is_public)     -- Public template browsing
INDEX idx_templates_category (category)    -- Category filtering
INDEX idx_templates_usage (usage_count)    -- Popular templates
INDEX idx_templates_rating (rating_avg, rating_count) -- Best rated templates
```

#### Conversation Management
```sql
INDEX idx_conversations_status (status)    -- Filter by conversation status
INDEX idx_conversations_activity (last_activity_at) -- Recent activity
INDEX idx_conversations_shared (shared)    -- Shared conversations
INDEX idx_conversations_share_token (share_token) -- Token lookup
```

#### Prompt Processing
```sql
INDEX idx_prompts_status (status)          -- Processing queue
INDEX idx_prompts_sequence (conversation_id, sequence_number) -- Message order
INDEX idx_prompts_model (model_used)       -- Model usage analytics
INDEX idx_prompts_tokens (token_count_total) -- Usage analytics
INDEX idx_prompts_cost (cost)              -- Cost tracking
```

#### Audit and Security
```sql
INDEX idx_audit_logs_entity (entity_type, entity_id) -- Entity lookup
INDEX idx_audit_logs_action (action)       -- Action filtering
INDEX idx_audit_logs_ip (ip_address)       -- Security analysis
INDEX idx_audit_logs_severity (severity)   -- Alert filtering
INDEX idx_audit_logs_session (session_id)  -- Session tracking
```

#### Temporal Queries
```sql
INDEX idx_users_created (created_at)       -- Registration analytics
INDEX idx_templates_created (created_at)   -- Content creation trends
INDEX idx_conversations_created (created_at) -- Usage patterns
INDEX idx_prompts_created (created_at)     -- Activity analytics
INDEX idx_audit_logs_created (created_at)  -- Time-based audit queries
```

### Full-Text Search Indexes
```sql
FULLTEXT INDEX ft_templates_search (name, description, content)
FULLTEXT INDEX ft_conversations_search (title, description)
FULLTEXT INDEX ft_prompts_search (content, user_input, ai_response)
```

**Usage**: Enable natural language search across content.

**Performance**: MySQL InnoDB full-text search with relevance ranking.

### Composite Indexes

#### Conversation Message Ordering
```sql
INDEX idx_prompts_sequence (conversation_id, sequence_number)
```
**Purpose**: Fast retrieval of conversation messages in order.

#### Template Popularity
```sql
INDEX idx_templates_rating (rating_avg, rating_count)
```
**Purpose**: Efficient sorting by rating quality and reliability.

#### User Activity Tracking
```sql
INDEX idx_audit_logs_user_action (user_id, action)
```
**Purpose**: Quick user activity analysis and security monitoring.

#### Temporal Entity Lookups
```sql
INDEX idx_audit_logs_severity_created (severity, created_at)
```
**Purpose**: Security incident analysis by severity and time.

## Constraint Validation

### Check Constraints
```sql
-- Rating validation
CHECK (rating BETWEEN 1 AND 5)

-- Temperature validation (AI model parameter)
CHECK (temperature BETWEEN 0.0 AND 2.0)

-- Token count validation
CHECK (token_count_input >= 0)
CHECK (token_count_output >= 0)
CHECK (token_count_total >= 0)
```

### Unique Constraints
```sql
-- User email uniqueness
UNIQUE KEY uk_users_email (email)

-- One rating per user per template
UNIQUE KEY uk_template_ratings (template_id, user_id)

-- One participation per user per conversation
UNIQUE KEY uk_conversation_participants (conversation_id, user_id)

-- Unique share tokens
UNIQUE KEY uk_conversations_share_token (share_token)
```

## Performance Considerations

### Index Maintenance
- Indexes are automatically maintained by MySQL
- Statistics are updated regularly for query optimization
- Full-text indexes rebuild automatically on content changes

### Query Patterns
1. **User Dashboard**: Recent conversations and templates
2. **Template Discovery**: Public templates by category and rating
3. **Conversation History**: Messages in chronological order
4. **Audit Queries**: User activity and security events
5. **Analytics**: Usage statistics and performance metrics

### Optimization Strategies
1. **Partitioning**: Consider partitioning audit_logs by date for large datasets
2. **Archiving**: Move old conversations to archive tables
3. **Caching**: Cache frequently accessed templates and user data
4. **Read Replicas**: Use read replicas for analytics queries

## Security Implications

### Audit Trail Integrity
- RESTRICT cascading on audit logs prevents data loss
- All sensitive operations are logged
- IP addresses and user agents tracked for security analysis

### Data Privacy
- Soft delete implementation preserves data relationships
- User deletion requires explicit audit log cleanup
- Personal data can be anonymized while preserving functionality

### Access Control
- Foreign key constraints enforce data ownership
- Sharing tokens provide controlled access to conversations
- Participant permissions control collaboration access