@echo off
echo Setting up Test Environment Variables...
set DATABASE_URL=postgresql+asyncpg://user:password@localhost:5433/companion
set QDRANT_HOST=localhost
set QDRANT_PORT=6333
set REDIS_URL=redis://localhost:6379

echo Running Database Migrations...
.\backend\venv\Scripts\alembic -c backend/alembic.ini upgrade head

echo Running Integration Tests...
.\backend\venv\Scripts\python backend/tests/integration_tests.py
pause
