"""Deployment file templates for spawn deploy init."""

# Dockerfile Templates

DOCKERFILE_FASTAPI = """FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

DOCKERFILE_FLASK = """FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Expose Flask default port
EXPOSE 5000

# Run the application
CMD ["uv", "run", "flask", "run", "--host", "0.0.0.0", "--port", "5000"]
"""

DOCKERFILE_GENERIC = """FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Run the application
CMD ["uv", "run", "python", "main.py"]
"""

# Docker Compose Template

DOCKER_COMPOSE_CONTENT = """services:
  app:
    build: .
    ports:
      - "${APP_PORT:-8000}:8000"
    environment:
      - ENV=${ENV:-development}
    env_file:
      - .env
    volumes:
      - .:/app
    restart: unless-stopped

  # Uncomment to add PostgreSQL database
  # db:
  #   image: postgres:16-alpine
  #   environment:
  #     POSTGRES_DB: ${POSTGRES_DB:-myapp}
  #     POSTGRES_USER: ${POSTGRES_USER:-postgres}
  #     POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
  #   ports:
  #     - "${POSTGRES_PORT:-5432}:5432"
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #   restart: unless-stopped

  # Uncomment to add Redis cache
  # redis:
  #   image: redis:7-alpine
  #   ports:
  #     - "${REDIS_PORT:-6379}:6379"
  #   restart: unless-stopped

# volumes:
#   postgres_data:
"""

# Environment Variables Template

ENV_EXAMPLE_CONTENT = """# Application
ENV=development
APP_PORT=8000
DEBUG=True

# Database (uncomment if using PostgreSQL)
# POSTGRES_DB=myapp
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=postgres
# POSTGRES_PORT=5432
# DATABASE_URL=postgresql://postgres:postgres@db:5432/myapp

# Redis (uncomment if using Redis)
# REDIS_HOST=redis
# REDIS_PORT=6379
# REDIS_URL=redis://redis:6379/0

# Security
# SECRET_KEY=your-secret-key-here
# JWT_SECRET=your-jwt-secret-here

# External APIs
# API_KEY=your-api-key-here
"""

# GitHub Actions CI Workflow Template

GITHUB_ACTIONS_CI = """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'

    - name: Install uv
      uses: astral-sh/setup-uv@v5

    - name: Install dependencies
      run: |
        uv sync --frozen

    - name: Run linter
      run: |
        uv run ruff check .

    - name: Run tests
      run: |
        uv run pytest tests/ -v

    - name: Check code coverage
      run: |
        uv run pytest tests/ --cov=. --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        fail_ci_if_error: false

  build:
    runs-on: ubuntu-latest
    needs: test

    steps:
    - uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Build Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: false
        tags: app:latest
        cache-from: type=gha
        cache-to: type=gha,mode=max
"""
