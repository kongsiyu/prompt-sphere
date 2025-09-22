@echo off
REM ================================================================
REM Development Environment Setup Script (Windows)
REM ================================================================
REM This script sets up the complete development environment for
REM the AI System Prompt Generator project on Windows

setlocal EnableDelayedExpansion

REM Colors for output (limited in Windows)
set "RED=[31m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "NC=[0m"

REM Get project root directory
set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"

echo [INFO] Setting up development environment for AI System Prompt Generator...
echo [INFO] Project root: %PROJECT_ROOT%

REM ================================================================
REM SYSTEM REQUIREMENTS CHECK
REM ================================================================
echo [INFO] Checking system requirements...

REM Check Node.js
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo [SUCCESS] Node.js version: %NODE_VERSION%

REM Check npm
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm is not installed. Please install npm.
    exit /b 1
)

for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
echo [SUCCESS] npm version: %NPM_VERSION%

REM Check Python
where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python is not installed. Please install Python 3.11+ from https://python.org/
        exit /b 1
    ) else (
        set "PYTHON_CMD=py"
    )
) else (
    set "PYTHON_CMD=python"
)

for /f "tokens=*" %%i in ('%PYTHON_CMD% --version') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python version: %PYTHON_VERSION%

REM Check pip
where pip >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not installed. Please install pip.
    exit /b 1
)
echo [SUCCESS] pip is available

REM Check Docker (optional)
where docker >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=3 delims= " %%i in ('docker --version') do (
        for /f "tokens=1 delims=," %%j in ("%%i") do set DOCKER_VERSION=%%j
    )
    echo [SUCCESS] Docker version: !DOCKER_VERSION!
) else (
    echo [WARNING] Docker is not installed. Docker features will not be available.
)

REM Check Docker Compose (optional)
where docker-compose >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=3 delims= " %%i in ('docker-compose --version') do (
        for /f "tokens=1 delims=," %%j in ("%%i") do set COMPOSE_VERSION=%%j
    )
    echo [SUCCESS] Docker Compose version: !COMPOSE_VERSION!
) else (
    echo [WARNING] Docker Compose is not available.
)

REM ================================================================
REM FRONTEND SETUP
REM ================================================================
echo [INFO] Setting up frontend dependencies...

if exist "frontend\package.json" (
    cd frontend
    echo [INFO] Installing frontend dependencies...
    npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install frontend dependencies
        exit /b 1
    )
    echo [SUCCESS] Frontend dependencies installed
    cd "%PROJECT_ROOT%"
) else (
    echo [WARNING] Frontend package.json not found, skipping frontend setup
)

REM ================================================================
REM BACKEND SETUP
REM ================================================================
echo [INFO] Setting up backend dependencies...

if exist "backend\requirements.txt" (
    cd backend

    REM Check if virtual environment exists
    if not exist ".venv" (
        echo [INFO] Creating Python virtual environment...
        %PYTHON_CMD% -m venv .venv
        if errorlevel 1 (
            echo [ERROR] Failed to create virtual environment
            exit /b 1
        )
    )

    REM Activate virtual environment
    call .venv\Scripts\activate.bat

    echo [INFO] Installing backend dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install backend dependencies
        exit /b 1
    )

    REM Install development dependencies if available
    if exist "pyproject.toml" (
        findstr /c:"[project.optional-dependencies]" pyproject.toml >nul 2>&1
        if not errorlevel 1 (
            echo [INFO] Installing development dependencies...
            pip install -e ".[dev]"
        )
    )

    echo [SUCCESS] Backend dependencies installed
    cd "%PROJECT_ROOT%"
) else (
    echo [WARNING] Backend requirements.txt not found, skipping backend setup
)

REM ================================================================
REM ROOT LEVEL DEPENDENCIES
REM ================================================================
echo [INFO] Installing root-level dependencies...

if exist "package.json" (
    npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install root-level dependencies
        exit /b 1
    )
    echo [SUCCESS] Root-level dependencies installed
)

REM ================================================================
REM PRE-COMMIT HOOKS SETUP
REM ================================================================
echo [INFO] Setting up pre-commit hooks...

REM Install pre-commit if not available
where pre-commit >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing pre-commit...
    pip install pre-commit
)

REM Install pre-commit hooks
if exist ".pre-commit-config.yaml" (
    echo [INFO] Installing pre-commit hooks...
    pre-commit install
    if not errorlevel 1 (
        echo [SUCCESS] Pre-commit hooks installed
    )
) else (
    echo [WARNING] Pre-commit configuration not found
)

REM ================================================================
REM ENVIRONMENT FILES SETUP
REM ================================================================
echo [INFO] Setting up environment files...

REM Root level .env file
if exist ".env.example" (
    if not exist ".env.local" (
        echo [INFO] Creating .env.local from template...
        copy ".env.example" ".env.local" >nul
        echo [SUCCESS] Created .env.local
    ) else (
        echo [INFO] .env.local already exists
    )
)

REM Frontend .env file
if exist "frontend\.env.example" (
    if not exist "frontend\.env.local" (
        echo [INFO] Creating frontend\.env.local from template...
        copy "frontend\.env.example" "frontend\.env.local" >nul
        echo [SUCCESS] Created frontend\.env.local
    )
)

REM Backend .env file
if exist "backend\.env.example" (
    if not exist "backend\.env" (
        echo [INFO] Creating backend\.env from template...
        copy "backend\.env.example" "backend\.env" >nul
        echo [SUCCESS] Created backend\.env
    )
)

REM ================================================================
REM DOCKER SETUP
REM ================================================================
where docker >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Setting up Docker environment...

    if exist "docker-compose.yml" (
        echo [INFO] Building Docker images...
        docker-compose build
        if not errorlevel 1 (
            echo [SUCCESS] Docker images built
        )
    )
) else (
    echo [WARNING] Skipping Docker setup (Docker not available)
)

REM ================================================================
REM SUCCESS MESSAGE
REM ================================================================
echo.
echo [SUCCESS] Development environment setup complete!
echo.
echo Next steps:
echo   1. Review and update environment files with your specific values:
echo      - .env.local
echo      - frontend\.env.local
echo      - backend\.env
echo.
echo   2. Start development servers:
echo      - Full stack: npm run dev
echo      - Frontend only: npm run dev:frontend
echo      - Backend only: npm run dev:backend
echo      - Docker: npm run start
echo.
echo   3. Run quality checks:
echo      - Linting: npm run lint
echo      - Testing: npm run test
echo      - Type checking: npm run type-check
echo.
echo   4. Use Makefile commands (with make or nmake):
echo      - make dev        # Start development
echo      - make test       # Run tests
echo      - make lint       # Run linting
echo      - make help       # See all commands
echo.
echo [INFO] Happy coding! 🚀

pause