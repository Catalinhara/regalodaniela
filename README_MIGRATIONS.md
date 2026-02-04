# 🗄️ Database Migrations Manual (Alembic)

ClaraMente uses **Alembic** to safely manage database schema changes. This ensures that every developer and production environment stays in sync without manual SQL commands.

## 🚀 How it Works
When the Backend container starts, it automatically runs:
```bash
alembic upgrade head
```
This checks the `alembic/versions` folder and applies any missing migrations to the database before the API becomes active.

---

## 🛠️ Common Tasks

### 1. Creating a New Migration
When you modify a model in `backend/app/infrastructure/tables.py`, you must generate a new migration script:

```bash
# Run this from the root directory
docker exec claramente-backend-1 alembic revision --autogenerate -m "describe_your_change"
```

A new file will appear in `backend/alembic/versions/`. **Always review this file** to ensure it captured your changes correctly.

### 2. Applying Migrations Locally
Normally, this happens automatically on startup. If you want to trigger it manually:

```bash
docker exec claramente-backend-1 alembic upgrade head
```

### 3. Reverting a Migration
If a migration causes issues, you can step back:

```bash
docker exec claramente-backend-1 alembic downgrade -1
```

---

## 🏗️ Production/Fresh Builds
If you are deploying for the first time or running `docker compose up` on a fresh machine:
1.  **Do nothing**. The backend container is programmed to detect a fresh database and apply all migrations (from the initial schema to the current version) automatically.
2.  The tables `users`, `patients`, `checkins`, etc., will be created instantly.

## ⚠️ Important Rules
1.  **Never delete migration files** if they have already been applied to any production or collaborator database.
2.  **Import new models**: If you create a brand new `.py` file for models, ensure it is imported in `backend/alembic/env.py` so Alembic can "see" it.
3.  **DATABASE_URL**: Alembic uses the same environment variable as the FastAPI app, ensuring it always points to the correct Postgres instance.

---
🌿 *Maintain a clean schema, maintain a healthy application.*
