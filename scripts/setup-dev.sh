#!/bin/bash

# ================================================================
# Development Environment Setup Script
# ================================================================
# This script sets up the complete development environment for
# the AI System Prompt Generator project

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

log_info "Setting up development environment for AI System Prompt Generator..."
log_info "Project root: $PROJECT_ROOT"

# ================================================================
# SYSTEM REQUIREMENTS CHECK
# ================================================================
log_info "Checking system requirements..."

# Check Node.js
if ! command_exists node; then
    log_error "Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d 'v' -f 2)
log_success "Node.js version: $NODE_VERSION"

# Check npm
if ! command_exists npm; then
    log_error "npm is not installed. Please install npm."
    exit 1
fi

NPM_VERSION=$(npm --version)
log_success "npm version: $NPM_VERSION"

# Check Python
if ! command_exists python; then
    if ! command_exists python3; then
        log_error "Python is not installed. Please install Python 3.11+ from https://python.org/"
        exit 1
    else
        PYTHON_CMD="python3"
    fi
else
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version | cut -d ' ' -f 2)
log_success "Python version: $PYTHON_VERSION"

# Check pip
if ! command_exists pip; then
    if ! command_exists pip3; then
        log_error "pip is not installed. Please install pip."
        exit 1
    else
        PIP_CMD="pip3"
    fi
else
    PIP_CMD="pip"
fi

log_success "pip is available"

# Check Docker (optional)
if command_exists docker; then
    DOCKER_VERSION=$(docker --version | cut -d ' ' -f 3 | cut -d ',' -f 1)
    log_success "Docker version: $DOCKER_VERSION"
else
    log_warning "Docker is not installed. Docker features will not be available."
fi

# Check Docker Compose (optional)
if command_exists docker-compose; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d ' ' -f 3 | cut -d ',' -f 1)
    log_success "Docker Compose version: $COMPOSE_VERSION"
elif command_exists docker && docker compose version >/dev/null 2>&1; then
    COMPOSE_VERSION=$(docker compose version --short)
    log_success "Docker Compose (plugin) version: $COMPOSE_VERSION"
else
    log_warning "Docker Compose is not available."
fi

# ================================================================
# FRONTEND SETUP
# ================================================================
log_info "Setting up frontend dependencies..."

if [ -f "frontend/package.json" ]; then
    cd frontend
    log_info "Installing frontend dependencies..."
    npm install
    log_success "Frontend dependencies installed"
    cd "$PROJECT_ROOT"
else
    log_warning "Frontend package.json not found, skipping frontend setup"
fi

# ================================================================
# BACKEND SETUP
# ================================================================
log_info "Setting up backend dependencies..."

if [ -f "backend/requirements.txt" ]; then
    cd backend

    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        log_info "Creating Python virtual environment..."
        $PYTHON_CMD -m venv .venv
    fi

    # Activate virtual environment
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        # Windows (Git Bash)
        source .venv/Scripts/activate
    else
        # Unix/Linux/macOS
        source .venv/bin/activate
    fi

    log_info "Installing backend dependencies..."
    $PIP_CMD install --upgrade pip
    $PIP_CMD install -r requirements.txt

    # Install development dependencies if available
    if [ -f "pyproject.toml" ] && grep -q "\[project.optional-dependencies\]" pyproject.toml; then
        log_info "Installing development dependencies..."
        $PIP_CMD install -e ".[dev]"
    fi

    log_success "Backend dependencies installed"
    cd "$PROJECT_ROOT"
else
    log_warning "Backend requirements.txt not found, skipping backend setup"
fi

# ================================================================
# ROOT LEVEL DEPENDENCIES
# ================================================================
log_info "Installing root-level dependencies..."

if [ -f "package.json" ]; then
    npm install
    log_success "Root-level dependencies installed"
fi

# ================================================================
# PRE-COMMIT HOOKS SETUP
# ================================================================
log_info "Setting up pre-commit hooks..."

# Install pre-commit if not available
if ! command_exists pre-commit; then
    log_info "Installing pre-commit..."
    $PIP_CMD install pre-commit
fi

# Install pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    log_info "Installing pre-commit hooks..."
    pre-commit install
    log_success "Pre-commit hooks installed"
else
    log_warning "Pre-commit configuration not found"
fi

# ================================================================
# ENVIRONMENT FILES SETUP
# ================================================================
log_info "Setting up environment files..."

# Root level .env file
if [ -f ".env.example" ] && [ ! -f ".env.local" ]; then
    log_info "Creating .env.local from template..."
    cp .env.example .env.local
    log_success "Created .env.local"
else
    log_info ".env.local already exists or no template available"
fi

# Frontend .env file
if [ -f "frontend/.env.example" ] && [ ! -f "frontend/.env.local" ]; then
    log_info "Creating frontend/.env.local from template..."
    cp frontend/.env.example frontend/.env.local
    log_success "Created frontend/.env.local"
fi

# Backend .env file
if [ -f "backend/.env.example" ] && [ ! -f "backend/.env" ]; then
    log_info "Creating backend/.env from template..."
    cp backend/.env.example backend/.env
    log_success "Created backend/.env"
fi

# ================================================================
# DOCKER SETUP
# ================================================================
if command_exists docker; then
    log_info "Setting up Docker environment..."

    if [ -f "docker-compose.yml" ]; then
        log_info "Building Docker images..."
        docker-compose build
        log_success "Docker images built"
    fi
else
    log_warning "Skipping Docker setup (Docker not available)"
fi

# ================================================================
# VERIFICATION
# ================================================================
log_info "Running setup verification..."

# Test frontend
if [ -f "frontend/package.json" ]; then
    cd frontend
    if npm run type-check >/dev/null 2>&1; then
        log_success "Frontend type checking works"
    else
        log_warning "Frontend type checking failed"
    fi
    cd "$PROJECT_ROOT"
fi

# Test backend
if [ -f "backend/requirements.txt" ]; then
    cd backend
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        source .venv/Scripts/activate
    else
        source .venv/bin/activate
    fi

    if $PYTHON_CMD -c "import app" >/dev/null 2>&1; then
        log_success "Backend imports work"
    else
        log_warning "Backend imports failed"
    fi
    cd "$PROJECT_ROOT"
fi

# ================================================================
# SUCCESS MESSAGE
# ================================================================
echo
log_success "Development environment setup complete!"
echo
echo "Next steps:"
echo "  1. Review and update environment files with your specific values:"
echo "     - .env.local"
echo "     - frontend/.env.local"
echo "     - backend/.env"
echo
echo "  2. Start development servers:"
echo "     - Full stack: npm run dev"
echo "     - Frontend only: npm run dev:frontend"
echo "     - Backend only: npm run dev:backend"
echo "     - Docker: npm run start"
echo
echo "  3. Run quality checks:"
echo "     - Linting: npm run lint"
echo "     - Testing: npm run test"
echo "     - Type checking: npm run type-check"
echo
echo "  4. Use Makefile commands:"
echo "     - make dev        # Start development"
echo "     - make test       # Run tests"
echo "     - make lint       # Run linting"
echo "     - make help       # See all commands"
echo

log_info "Happy coding! 🚀"