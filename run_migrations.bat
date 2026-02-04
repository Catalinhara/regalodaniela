@echo off
echo Running Database Migrations...
set DATABASE_URL=postgresql+asyncpg://user:password@localhost:5433/companion
.\backend\venv\Scripts\alembic -c backend/alembic.ini upgrade head
pause
