# Backend Testing Guide

## 🧪 Overview

This document describes the pytest-based testing infrastructure for the AI Prompt Generator backend.

## 📁 Test Structure

```
tests/
├── conftest.py                    # Pytest configuration and fixtures
├── test_models.py                 # Database model unit tests (22 tests)
├── test_config.py                 # Configuration unit tests (18 tests)
├── test_api.py                    # FastAPI application tests (20 tests)
├── test_api_models.py             # Pydantic model tests (20 tests)
├── test_api_endpoints.py          # API endpoint integration tests (23 tests)
├── test_repositories.py           # Repository layer integration tests (@database)
├── test_database_integration.py   # Database connection and session tests (@database)
└── fixtures/                      # Test fixtures (if needed)
```

## 🔧 Test Configuration

### Pytest Configuration

The project uses `pyproject.toml` for pytest configuration:

```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
asyncio_mode = "auto"
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### Test Markers

- `@pytest.mark.unit` - Unit tests (isolated, no external dependencies)
- `@pytest.mark.api` - API-related tests
- `@pytest.mark.database` - Database tests (skipped by default)
- `@pytest.mark.slow` - Slow-running tests

## 🚀 Running Tests

### Using the Custom Test Runner

```bash
# Run unit tests only (no database)
python run_pytest.py unit

# Run all unit tests (default)
python run_pytest.py all

# Run database integration tests only
python run_pytest.py database
# or
python run_pytest.py db

# Run complete test suite (unit + database)
python run_pytest.py full

# Run with detailed output
python run_pytest.py coverage
```

### Using pytest directly

```bash
# Run unit tests only
python -m pytest tests/test_models.py tests/test_config.py tests/test_api.py tests/test_api_models.py tests/test_api_endpoints.py -v

# Run database tests only
python -m pytest tests/test_repositories.py tests/test_database_integration.py -v -m database --run-database-tests

# Run all tests
python -m pytest tests/ -v

# Run only unit tests
python -m pytest -m unit -v

# Run with coverage
python -m pytest --cov=app --cov=database.models --cov-report=term-missing
```

## 📊 Test Coverage

### 🔹 Unit Tests (Always Run)

#### Database Models (`test_models.py`)
- ✅ User model creation and validation
- ✅ Template model with JSON fields
- ✅ Conversation model with context/settings
- ✅ Prompt model with sequence management
- ✅ AuditLog model with metadata
- ✅ Model inheritance and table structure

#### Configuration (`test_config.py`)
- ✅ Settings instantiation and field access
- ✅ Database configuration validation
- ✅ API settings and CORS configuration
- ✅ Security settings validation
- ✅ Field type checking and defaults

#### API Layer
**Application Structure** (`test_api.py`)
- ✅ FastAPI application structure
- ✅ Basic endpoint existence
- ✅ Request/response handling
- ✅ Error handling behavior
- ✅ Content type management

**Pydantic Models** (`test_api_models.py`)
- ✅ PromptRequest validation and serialization
- ✅ PromptResponse structure and defaults
- ✅ HealthResponse model validation
- ✅ Field type validation and error handling
- ✅ Model integration workflows

**API Endpoints** (`test_api_endpoints.py`)
- ✅ Health check endpoint functionality
- ✅ Prompt generation with all field combinations
- ✅ Request validation and error responses
- ✅ Unicode and special character handling
- ✅ API documentation endpoints

### 🔹 Database Integration Tests (Optional)

#### Repository Layer (`test_repositories.py`)
- ✅ UserRepository CRUD operations
- ✅ TemplateRepository with category and tag search
- ✅ ConversationRepository with context handling
- ✅ PromptRepository with sequence management
- ✅ AuditLogRepository with action tracking
- ✅ Cross-repository transactions
- ✅ Error handling and constraint validation

#### Database Integration (`test_database_integration.py`)
- ✅ Basic connection and session management
- ✅ Transaction commit and rollback behavior
- ✅ Concurrent session handling
- ✅ Long-running session stability
- ✅ Error handling and recovery
- ✅ Schema operations and constraints
- ✅ Index creation and usage

## 🏗️ Test Fixtures

The `conftest.py` provides comprehensive fixtures:

```python
# Mock database sessions
mock_database_session()
mock_engine()

# Sample data fixtures
sample_user_data()
sample_template_data()
sample_conversation_data()
sample_prompt_data()

# Model instance fixtures
sample_user()
sample_template()
sample_conversation()
sample_prompt()

# API client
client()  # FastAPI TestClient
```

## 🎯 Test Strategy

### Unit Tests Philosophy
- **Isolated**: Tests don't depend on external services
- **Fast**: All tests complete in under 1 second
- **Reliable**: Tests pass consistently without flakiness
- **Focused**: Each test validates a specific behavior

### Database Test Strategy
- Models are tested without database connections
- Use mock sessions for repository testing
- Validate field types and constraints
- Test JSON field serialization

### API Test Strategy
- Test application structure and configuration
- Validate endpoint existence and basic behavior
- Test error handling and edge cases
- Avoid database dependencies in unit tests

## 📈 Test Results

Current test status:
- **103 passing tests** ✅
- **0 failing tests** ✅
- **35 warnings** (Pydantic/SQLAlchemy deprecations)
- **~0.32s** execution time

## 🛠️ Development Workflow

### Adding New Tests

1. Create test files following the naming convention `test_*.py`
2. Use appropriate markers (`@pytest.mark.unit`, `@pytest.mark.api`)
3. Utilize existing fixtures from `conftest.py`
4. Run tests locally before committing

### Test Categories

#### Unit Tests ✅ (103 tests)
- Database models (without DB connection)
- Configuration classes
- API structure and endpoints
- Pydantic model validation
- Request/response handling

#### Database Integration Tests ✅ (Available)
- Repository CRUD operations
- Database connection management
- Transaction handling
- Concurrent access patterns
- Schema operations
- Error recovery scenarios

#### Performance Tests ⏸️ (Future)
- Load testing
- Memory usage profiling
- Connection pool optimization
- Query performance analysis

## 🚨 Known Limitations

1. **Database Tests Optional**: Database integration tests require explicit activation with `--run-database-tests` flag
2. **External APIs**: No tests for OpenAI/Anthropic integrations yet
3. **Authentication**: JWT/auth testing not implemented
4. **E2E Testing**: No browser-based testing implemented

## 🔮 Future Improvements

1. **Performance Testing**: Add load and performance tests
2. **E2E Testing**: Browser-based testing with Playwright
3. **Contract Testing**: API contract validation
4. **External API Testing**: Mock OpenAI/Anthropic integrations
5. **Security Testing**: Authentication and authorization tests

## 🏃‍♂️ Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run unit tests:
```bash
python run_pytest.py all
```

3. Run database tests (optional):
```bash
python run_pytest.py database
```

4. Run complete suite:
```bash
python run_pytest.py full
```

5. Verify unit test output:
```
🧪 Running All Available Tests with pytest
==================================================
tests\test_models.py ......................              [ 21%]
tests\test_config.py ..................                  [ 38%]
tests\test_api.py ....................                   [ 58%]
tests\test_api_models.py ....................            [ 77%]
tests\test_api_endpoints.py .......................        [100%]

======================= 103 passed, 35 warnings in 0.37s ========================
🎉 All tests passed!
```

## 📝 Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain test coverage above 80%
4. Update this documentation

---

**Status**: ✅ Production Ready
**Last Updated**: 2024-01-01
**Unit Test Count**: 103 (always run)
**Database Test Count**: Available (run on demand)
**Coverage**: Complete unit testing + optional database integration testing