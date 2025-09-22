# AI System Prompt Generator

A full-stack application for creating, managing, and optimizing AI system prompts. Built with React (TypeScript) frontend and FastAPI (Python) backend.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node Version](https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen)](https://nodejs.org/)
[![Python Version](https://img.shields.io/badge/python-%3E%3D3.11-blue)](https://www.python.org/)

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [Testing](#testing)
- [Deployment](#deployment)
- [License](#license)

## Features

- 🎯 **Intuitive Interface**: Modern React-based UI for creating and managing prompts
- 🔧 **Template System**: Reusable prompt templates with variable substitution
- 🔍 **Search & Filter**: Advanced search and filtering capabilities
- 📊 **Analytics**: Track prompt performance and usage statistics
- 🔒 **Secure**: JWT-based authentication and authorization
- 🚀 **Fast**: Optimized for performance with efficient caching
- 📱 **Responsive**: Mobile-friendly design
- 🔌 **Extensible**: Plugin system for custom functionality

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React/TS)    │◄──►│   (FastAPI/Py)  │◄──►│   (Mysql)       │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 3306    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Redis Cache   │
                    │   Port: 6379    │
                    └─────────────────┘
```

### Tech Stack

**Frontend:**
- React 19+ with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- React Query for data fetching
- Zustand for state management

**Backend:**
- FastAPI with Python 3.11+
- SQLAlchemy for ORM
- Alembic for database migrations
- Pydantic for data validation
- JWT for authentication

**Development Tools:**
- Docker & Docker Compose
- Pre-commit hooks
- ESLint, Prettier, Black, isort
- Jest, pytest for testing

## Quick Start

### Prerequisites

- Node.js 18+ and npm 9+
- Python 3.11+ and pip
- Docker and Docker Compose (optional)
- Git

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ai-system-prompt-generator

# Run the setup script
./scripts/setup-dev.sh    # Unix/Linux/macOS
# or
scripts\setup-dev.bat     # Windows
```

### 2. Start Development

```bash
# Start both frontend and backend
npm run dev

# Or start individually
npm run dev:frontend  # http://localhost:3000
npm run dev:backend   # http://localhost:8000

# Or use Docker
npm run start         # Docker Compose
```

### 3. Verify Setup

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Development Setup

### Manual Setup

If you prefer to set up manually or the script doesn't work:

1. **Install Frontend Dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

2. **Install Backend Dependencies**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Unix/Linux/macOS
   # or .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   pip install -e ".[dev]"
   cd ..
   ```

3. **Install Root Dependencies**
   ```bash
   npm install
   ```

4. **Setup Environment Files**
   ```bash
   cp .env.example .env.local
   cp frontend/.env.example frontend/.env.local
   cp backend/.env.example backend/.env
   ```

5. **Setup Pre-commit Hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Available Commands

#### Root Level (works with both frontend and backend)

```bash
# Development
npm run dev              # Start both servers
npm run dev:frontend     # Start only frontend
npm run dev:backend      # Start only backend

# Building
npm run build            # Build both
npm run build:frontend   # Build only frontend
npm run build:backend    # Build only backend

# Testing
npm run test            # Test both
npm run test:frontend   # Test only frontend
npm run test:backend    # Test only backend
npm run test:watch      # Test in watch mode

# Code Quality
npm run lint            # Lint both
npm run lint:fix        # Fix linting issues
npm run format          # Format code
npm run type-check      # Type checking

# Docker
npm run docker:build    # Build images
npm run docker:up       # Start services
npm run docker:down     # Stop services
npm run start           # Start with Docker Compose
npm run stop            # Stop services
```

#### Makefile Commands

```bash
make help          # Show all available commands
make dev           # Start development
make test          # Run tests
make lint          # Run linting
make format        # Format code
make docker-build  # Build Docker images
make quick-start   # Full setup for new developers
```

## Project Structure

```
ai-system-prompt-generator/
├── frontend/                 # React TypeScript frontend
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API services
│   │   ├── stores/         # State management
│   │   ├── types/          # TypeScript types
│   │   └── utils/          # Utility functions
│   ├── public/             # Static assets
│   ├── tests/              # Frontend tests
│   └── package.json        # Frontend dependencies
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   ├── core/           # Core functionality
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── pyproject.toml      # Python project config
├── scripts/                # Development scripts
├── docs/                   # Documentation
├── docker-compose.yml      # Docker configuration
├── .pre-commit-config.yaml # Pre-commit hooks
├── Makefile               # Make commands
├── package.json           # Root package.json
└── README.md              # This file
```

## API Documentation

### Endpoints

The API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Key Endpoints

- `GET /api/v1/prompts` - List all prompts
- `POST /api/v1/prompts` - Create new prompt
- `GET /api/v1/prompts/{id}` - Get specific prompt
- `PUT /api/v1/prompts/{id}` - Update prompt
- `DELETE /api/v1/prompts/{id}` - Delete prompt
- `GET /api/v1/templates` - List prompt templates
- `GET /health` - Health check

## Contributing

### Code Style

We use automated code formatting and linting:

- **Frontend**: ESLint + Prettier
- **Backend**: Black + isort + flake8
- **Pre-commit hooks**: Automatically format code on commit

### Development Workflow

1. Create a feature branch
2. Make changes
3. Run tests: `npm run test`
4. Run linting: `npm run lint`
5. Commit changes (pre-commit hooks will run)
6. Push and create a pull request

### Commit Convention

We follow conventional commits:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Build/tooling changes

## Testing

### Running Tests

```bash
# All tests
npm run test

# Frontend tests only
npm run test:frontend

# Backend tests only
npm run test:backend

# Watch mode
npm run test:watch

# With coverage
npm run test -- --coverage  # Frontend
cd backend && pytest --cov=app  # Backend
```

### Test Structure

- **Frontend**: Jest + Testing Library
- **Backend**: pytest + TestClient
- **E2E**: Playwright (planned)

## Deployment

### Docker Production

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

See the `.env.example` files for all configuration options:
- `.env.example` - Root level configuration
- `frontend/.env.example` - Frontend specific
- `backend/.env.example` - Backend specific

### Health Checks

The application provides health check endpoints:
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system status

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: support@ai-prompt-generator.com
- 💬 Discussions: Use GitHub Discussions
- 🐛 Issues: Use GitHub Issues
- 📖 Docs: See `/docs` directory

---

Made with ❤️ by the AI Prompt Generator Team