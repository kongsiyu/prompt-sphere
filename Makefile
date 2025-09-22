# Makefile for AI System Prompt Generator
# Development commands for both frontend and backend

.PHONY: help dev build test lint format clean install setup start stop restart health

# Default target
help: ## Show this help message
	@echo "AI System Prompt Generator - Development Commands"
	@echo "================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development
dev: ## Start development servers for both frontend and backend
	npm run dev

dev-frontend: ## Start only frontend development server
	npm run dev:frontend

dev-backend: ## Start only backend development server
	npm run dev:backend

# Building
build: ## Build both frontend and backend
	npm run build

build-frontend: ## Build only frontend
	npm run build:frontend

build-backend: ## Build only backend
	npm run build:backend

# Testing
test: ## Run tests for both frontend and backend
	npm run test

test-frontend: ## Run only frontend tests
	npm run test:frontend

test-backend: ## Run only backend tests
	npm run test:backend

test-watch: ## Run tests in watch mode
	npm run test:watch

# Linting and formatting
lint: ## Lint code for both frontend and backend
	npm run lint

lint-frontend: ## Lint only frontend code
	npm run lint:frontend

lint-backend: ## Lint only backend code
	npm run lint:backend

lint-fix: ## Fix linting issues for both frontend and backend
	npm run lint:fix

format: ## Format code for both frontend and backend
	npm run format

format-frontend: ## Format only frontend code
	npm run format:frontend

format-backend: ## Format only backend code
	npm run format:backend

type-check: ## Run type checking for both frontend and backend
	npm run type-check

# Installation
install: ## Install dependencies for both frontend and backend
	npm run install

install-dev: ## Install development dependencies
	npm run install:dev

install-frontend: ## Install only frontend dependencies
	npm run install:frontend

install-backend: ## Install only backend dependencies
	npm run install:backend

# Cleaning
clean: ## Clean build artifacts and dependencies
	npm run clean

clean-frontend: ## Clean only frontend artifacts
	npm run clean:frontend

clean-backend: ## Clean only backend artifacts
	npm run clean:backend

# Docker operations
docker-build: ## Build Docker images
	npm run docker:build

docker-up: ## Start services with Docker Compose
	npm run docker:up

docker-down: ## Stop Docker services
	npm run docker:down

docker-logs: ## Show Docker logs
	npm run docker:logs

docker-restart: ## Restart Docker services
	npm run docker:restart

docker-clean: ## Clean Docker images and volumes
	npm run docker:clean

# Application lifecycle
setup: ## Complete setup (install deps + build docker)
	npm run setup

start: ## Start application with Docker
	npm run start

stop: ## Stop application
	npm run stop

restart: ## Restart application
	npm run restart

health: ## Check application health
	npm run health

# Database operations
backup: ## Backup database
	npm run backup

restore: ## Restore database from backup
	npm run restore

# Quality checks
check: lint type-check test ## Run all quality checks

# Development workflow
quick-start: install-dev docker-build start ## Quick start for new developers

# Production build
prod-build: clean build ## Clean production build

# Check dependencies
check-deps: ## Check for outdated dependencies
	cd frontend && npm outdated || true
	cd backend && pip list --outdated || true

# Security audit
security: ## Run security audit
	cd frontend && npm audit || true
	cd backend && pip-audit || true

# Update dependencies
update-deps: ## Update dependencies
	cd frontend && npm update
	cd backend && pip install --upgrade -r requirements.txt