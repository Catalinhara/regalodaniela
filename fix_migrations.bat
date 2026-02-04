@echo off
echo Fixing Database Migration State...
set DATABASE_URL=postgresql+asyncpg://user:password@localhost:5433/companion

echo Stamping revision '4838883a80a9' (google_id and language already exist)...
.\backend\venv\Scripts\alembic -c backend/alembic.ini stamp 4838883a80a9

echo Applying remaining migrations (creating facts table)...
.\backend\venv\Scripts\alembic -c backend/alembic.ini upgrade head

echo Done! Now try running run_tests.bat again.
pause
