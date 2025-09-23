# AI Prompt Generator Backend

FastAPI backend for AI System Prompt Generator - 阿里百炼DashScope集成的智能提示词生成器。

## Features

- 🚀 FastAPI web framework with async support
- 🔗 阿里百炼DashScope API integration for Qwen models
- 📊 MySQL database with SQLAlchemy ORM
- 🔒 JWT authentication with 钉钉OAuth support
- 📝 Automatic OpenAPI/Swagger documentation
- 🧪 Comprehensive test suite with pytest

## Installation

```bash
# Install dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Configuration

Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
```

Key configuration variables:
- `DASHSCOPE_API_KEY` - 阿里百炼 API key
- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - JWT secret key

## Development

```bash
# Run development server
uvicorn app.main:app --reload

# Run tests
pytest

# Code formatting
black .

# Type checking
mypy .
```

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.