# Development Guide

This guide provides detailed information for developers working on the AI System Prompt Generator project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Code Architecture](#code-architecture)
- [Development Workflow](#development-workflow)
- [Code Quality](#code-quality)
- [Testing Strategy](#testing-strategy)
- [Database Management](#database-management)
- [API Development](#api-development)
- [Frontend Development](#frontend-development)
- [Debugging](#debugging)
- [Performance](#performance)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

## Getting Started

### First-time Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-system-prompt-generator
   ```

2. **Run the setup script**
   ```bash
   ./scripts/setup-dev.sh    # Unix/Linux/macOS
   # or
   scripts\setup-dev.bat     # Windows
   ```

3. **Verify installation**
   ```bash
   npm run health
   ```

### Daily Development

1. **Pull latest changes**
   ```bash
   git pull origin main
   npm run install  # Update dependencies if needed
   ```

2. **Start development servers**
   ```bash
   npm run dev      # Both frontend and backend
   # or
   make dev         # Using Makefile
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Environment

### IDE Setup

**Recommended IDEs:**
- **VSCode** with extensions:
  - Python (Microsoft)
  - ESLint
  - Prettier
  - TypeScript and JavaScript
  - Docker
  - GitLens

**VSCode Settings** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true,
    "source.organizeImports": true
  }
}
```

### Environment Variables

Create and configure these files:
- `.env.local` - Root level configuration
- `frontend/.env.local` - Frontend specific
- `backend/.env` - Backend specific

### Port Configuration

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |
| Database | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |

## Code Architecture

### Backend Architecture

```
backend/
├── app/
│   ├── api/                 # API endpoints
│   │   ├── routes/         # Route definitions
│   │   └── dependencies/   # FastAPI dependencies
│   ├── core/               # Core functionality
│   │   ├── config.py      # Configuration
│   │   ├── security.py    # Authentication/Authorization
│   │   └── database.py    # Database configuration
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   └── utils/              # Utility functions
├── tests/                  # Test files
└── alembic/               # Database migrations
```

### Frontend Architecture

```
frontend/
├── src/
│   ├── components/         # Reusable components
│   │   ├── ui/            # Basic UI components
│   │   └── features/      # Feature-specific components
│   ├── pages/             # Page components
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API services
│   ├── stores/            # State management
│   ├── types/             # TypeScript definitions
│   └── utils/             # Utility functions
├── public/                # Static assets
└── tests/                 # Test files
```

### Key Patterns

**Backend Patterns:**
- Repository Pattern for data access
- Service Layer for business logic
- Dependency Injection with FastAPI
- Async/await for I/O operations

**Frontend Patterns:**
- Component composition
- Custom hooks for logic reuse
- Context for global state
- Service layer for API calls

## Development Workflow

### Branch Strategy

```
main                    # Production-ready code
├── develop            # Integration branch
├── feature/xxx        # Feature branches
├── bugfix/xxx         # Bug fix branches
└── hotfix/xxx         # Critical fixes
```

### Commit Workflow

1. **Make changes**
2. **Run quality checks**
   ```bash
   npm run lint           # Check code style
   npm run test           # Run tests
   npm run type-check     # Type checking
   ```

3. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"  # Conventional commits
   ```

4. **Push and create PR**
   ```bash
   git push origin feature/your-feature
   # Create PR through GitHub/GitLab interface
   ```

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Backward compatibility maintained

## Code Quality

### Automated Tools

**Pre-commit Hooks** (runs automatically):
- Black (Python formatting)
- isort (Import sorting)
- flake8 (Python linting)
- ESLint (JavaScript/TypeScript)
- Prettier (Code formatting)
- Security scanning

**Manual Commands:**
```bash
# Format code
npm run format

# Fix linting issues
npm run lint:fix

# Type checking
npm run type-check
```

### Code Style Guidelines

**Python (Backend):**
- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters
- Use docstrings for functions and classes

**TypeScript (Frontend):**
- Use strict TypeScript
- Prefer interfaces over types
- Use descriptive variable names
- Follow React best practices

### Documentation Standards

- Use JSDoc for TypeScript functions
- Use docstrings for Python functions
- Update README for significant changes
- Document API endpoints in FastAPI

## Testing Strategy

### Test Types

**Unit Tests:**
- Test individual functions/components
- Mock external dependencies
- Aim for >80% coverage

**Integration Tests:**
- Test API endpoints
- Test database interactions
- Test component integration

**E2E Tests:**
- Test complete user workflows
- Test critical business paths

### Running Tests

```bash
# All tests
npm run test

# With coverage
npm run test -- --coverage          # Frontend
cd backend && pytest --cov=app      # Backend

# Watch mode
npm run test:watch

# Specific test file
npm run test:frontend -- Button.test.tsx
cd backend && pytest tests/test_prompts.py
```

### Test Structure

**Frontend Tests:**
```typescript
// Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button Component', () => {
  it('should render correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('should handle click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

**Backend Tests:**
```python
# test_prompts.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_prompt():
    response = client.post(
        "/api/v1/prompts",
        json={"title": "Test Prompt", "content": "Test content"}
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test Prompt"

@pytest.mark.asyncio
async def test_prompt_service():
    # Test service layer logic
    pass
```

## Database Management

### Migrations

**Create Migration:**
```bash
cd backend
alembic revision --autogenerate -m "Add new table"
```

**Apply Migration:**
```bash
alembic upgrade head
```

**Rollback Migration:**
```bash
alembic downgrade -1
```

### Database Seeding

```bash
cd backend
python scripts/seed_database.py
```

### Database Schema

Key models:
- `User` - User accounts and authentication
- `Prompt` - AI prompts and templates
- `Category` - Prompt categorization
- `Usage` - Usage tracking and analytics

## API Development

### API Design Principles

- RESTful endpoints
- Consistent response format
- Proper HTTP status codes
- Request/response validation
- Pagination for collections
- Rate limiting

### Adding New Endpoints

1. **Define Pydantic schemas** (`schemas/`)
2. **Create database models** (`models/`)
3. **Implement service logic** (`services/`)
4. **Add API routes** (`api/routes/`)
5. **Write tests** (`tests/`)

### Response Format

```json
{
  "data": { ... },           // Response data
  "message": "Success",      // Human readable message
  "status": "success",       // success/error
  "pagination": { ... }      // For paginated responses
}
```

### Error Handling

```python
from fastapi import HTTPException

# Bad request
raise HTTPException(status_code=400, detail="Invalid input")

# Not found
raise HTTPException(status_code=404, detail="Resource not found")

# Server error
raise HTTPException(status_code=500, detail="Internal server error")
```

## Frontend Development

### Component Guidelines

**Component Structure:**
```typescript
// Component.tsx
import React from 'react';
import './Component.styles.css';

interface ComponentProps {
  title: string;
  onAction?: () => void;
}

export const Component: React.FC<ComponentProps> = ({
  title,
  onAction
}) => {
  return (
    <div className="component">
      <h2>{title}</h2>
      {onAction && (
        <button onClick={onAction}>Action</button>
      )}
    </div>
  );
};
```

### State Management

**Global State (Context):**
```typescript
// stores/AppContext.tsx
import React, { createContext, useContext, useReducer } from 'react';

interface AppState {
  user: User | null;
  prompts: Prompt[];
}

const AppContext = createContext<AppState | null>(null);

export const useAppState = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppState must be used within AppProvider');
  }
  return context;
};
```

**Local State (Custom Hooks):**
```typescript
// hooks/usePrompts.ts
import { useState, useEffect } from 'react';
import { promptService } from '../services/promptService';

export const usePrompts = () => {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchPrompts = async () => {
    setLoading(true);
    try {
      const data = await promptService.getAll();
      setPrompts(data);
    } catch (error) {
      console.error('Failed to fetch prompts:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrompts();
  }, []);

  return { prompts, loading, refetch: fetchPrompts };
};
```

### API Integration

```typescript
// services/promptService.ts
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_BASE_URL;

export const promptService = {
  async getAll(): Promise<Prompt[]> {
    const response = await axios.get(`${API_BASE}/prompts`);
    return response.data.data;
  },

  async create(prompt: CreatePromptRequest): Promise<Prompt> {
    const response = await axios.post(`${API_BASE}/prompts`, prompt);
    return response.data.data;
  },

  async update(id: string, prompt: UpdatePromptRequest): Promise<Prompt> {
    const response = await axios.put(`${API_BASE}/prompts/${id}`, prompt);
    return response.data.data;
  },

  async delete(id: string): Promise<void> {
    await axios.delete(`${API_BASE}/prompts/${id}`);
  }
};
```

## Debugging

### Backend Debugging

**Enable Debug Mode:**
```bash
export DEBUG=true
npm run dev:backend
```

**Debugging with VSCode:**
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/backend/.venv/bin/uvicorn",
      "args": ["main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
      "cwd": "${workspaceFolder}/backend",
      "console": "integratedTerminal"
    }
  ]
}
```

### Frontend Debugging

**React DevTools:**
- Install React DevTools browser extension
- Use `console.log()` for debugging
- Use browser debugger with breakpoints

**Network Debugging:**
- Monitor API calls in Network tab
- Check request/response payloads
- Verify authentication headers

### Common Debug Commands

```bash
# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Debug database
docker-compose exec db psql -U postgres -d prompt_generator

# Check environment
npm run health
```

## Performance

### Backend Performance

**Database Optimization:**
- Use indexes on frequently queried fields
- Implement query pagination
- Use database connection pooling
- Cache expensive queries

**API Optimization:**
- Implement response caching
- Use async/await for I/O operations
- Add request/response compression
- Implement rate limiting

### Frontend Performance

**Bundle Optimization:**
- Use code splitting
- Lazy load components
- Optimize images
- Minimize bundle size

**Runtime Performance:**
- Use React.memo for expensive components
- Implement virtual scrolling for large lists
- Debounce API calls
- Use service workers for caching

### Monitoring

```bash
# Backend performance
pip install py-spy
py-spy top --pid <backend-process-id>

# Frontend bundle analysis
npm run build
npm run analyze
```

## Security

### Backend Security

**Authentication:**
- JWT tokens with expiration
- Secure password hashing
- Rate limiting on auth endpoints

**Data Protection:**
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection

### Frontend Security

**Client-side Security:**
- Validate all inputs
- Sanitize user content
- Use HTTPS only
- Implement CSP headers

### Security Checklist

- [ ] Environment variables secured
- [ ] No secrets in code
- [ ] Input validation implemented
- [ ] Authentication required for sensitive operations
- [ ] Rate limiting in place
- [ ] Dependencies regularly updated

## Troubleshooting

### Common Issues

**"Module not found" errors:**
```bash
# Frontend
cd frontend && npm install

# Backend
cd backend && pip install -r requirements.txt
```

**Database connection errors:**
```bash
# Check if database is running
docker-compose ps

# Restart database
docker-compose restart db
```

**Port already in use:**
```bash
# Find and kill process using port 3000
lsof -ti:3000 | xargs kill -9

# Or change port in .env file
VITE_PORT=3001
```

**Pre-commit hook failures:**
```bash
# Skip hooks temporarily
git commit --no-verify -m "message"

# Fix and reinstall hooks
pre-commit clean
pre-commit install
```

### Getting Help

1. **Check logs** for error messages
2. **Search existing issues** in the repository
3. **Ask questions** in team chat or discussions
4. **Create an issue** if it's a bug or feature request

### Performance Issues

**Slow API responses:**
- Check database query performance
- Review N+1 query problems
- Monitor server resources

**Frontend performance:**
- Use React DevTools Profiler
- Check bundle size
- Monitor memory usage

---

This development guide is a living document. Please update it as the project evolves and new patterns emerge.