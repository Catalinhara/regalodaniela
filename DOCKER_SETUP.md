# 🚀 Docker Rebuild & Startup Guide

## Quick Start

```powershell
# 1. Stop existing containers
docker-compose down

# 2. Rebuild containers with new dependencies
docker-compose build --no-cache

# 3. Start everything
docker-compose up
```

## Detailed Steps

### 1. Set Environment Variables

Create a `.env` file in the project root:

```powershell
# Copy the example file
Copy-Item .env.example .env

# Edit .env and set your values
notepad .env
```

**Required variables:**
- `OPENROUTER_API_KEY` - Your OpenRouter API key (for LLM features)
- `JWT_SECRET_KEY` - Random 32+ character string for access tokens
- `JWT_REFRESH_SECRET_KEY` - Different random string for refresh tokens

**Generate secure secrets:**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Stop Existing Containers

```powershell
docker-compose down
```

This stops and removes containers but **keeps your database data**.

### 3. Rebuild Containers

```powershell
# Rebuild without cache (ensures fresh install of new dependencies)
docker-compose build --no-cache
```

This will:
- Install new Python packages (passlib, python-jose, email-validator, slowapi)
- Install axios in frontend
- Build fresh Docker images

### 4. Start Services

```powershell
# Start in foreground (see logs)
docker-compose up

# OR start in background (detached)
docker-compose up -d
```

### 5. Verify Services

Check that all services are running:
```powershell
docker-compose ps
```

Expected output:
```
NAME                    STATUS              PORTS
claramante-backend-1    Up                  0.0.0.0:8000->8000/tcp
claramante-frontend-1   Up                  0.0.0.0:5173->5173/tcp
claramante-db-1         Up                  0.0.0.0:5432->5432/tcp
```

### 6. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

You should see the **Login/Register screen** instead of the main app.

## Database Migration

The new authentication system added `users` and `refresh_tokens` tables. These will be created automatically on first startup.

**⚠️ Important:** The old `TEMP_USER_ID` is removed. You'll need to:
1. Register a new account
2. Existing check-ins/patients/etc. will be orphaned

**To clear old data:**
```powershell
# Stop containers
docker-compose down

# Remove database volume
docker volume rm claramante_postgres_data

# Restart (creates fresh database)
docker-compose up
```

## Troubleshooting

### Port Already in Use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

### Container Build Fails
```powershell
# Clean everything and rebuild
docker-compose down -v
docker system prune -a
docker-compose build --no-cache
docker-compose up
```

### Database Connection Issues
```powershell
# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Frontend Not Loading
```powershell
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend only
docker-compose build --no-cache frontend
docker-compose up frontend
```

## Development Workflow

### View Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart a Service
```powershell
docker-compose restart backend
docker-compose restart frontend
```

### Execute Commands in Container
```powershell
# Backend shell
docker-compose exec backend bash

# Run migrations (if needed)
docker-compose exec backend alembic upgrade head

# Frontend shell
docker-compose exec frontend sh
```

### Database Access
```powershell
# Connect to PostgreSQL
docker-compose exec db psql -U user -d companion

# View users
SELECT id, email, full_name, created_at FROM users;

# View refresh tokens
SELECT user_id, token_family, is_revoked, created_at FROM refresh_tokens;
```

## Production Deployment

For production, update `docker-compose.yml`:

1. **Remove volume mounts** (lines 9, 21-22) - Use built code, not live reload
2. **Set secure secrets** in `.env`
3. **Change Dockerfile CMD** - Remove `--reload` flag
4. **Use production build** for frontend - `npm run build` + serve static files
5. **Enable HTTPS** - Set `secure=True` for cookies in `auth_routes.py`
6. **Update CORS origins** - Set production domain in `config.py`

## Summary

```powershell
# Complete rebuild process
docker-compose down
docker-compose build --no-cache
docker-compose up

# Then visit: http://localhost:5173
```

You're ready to test the authentication system! 🎉
