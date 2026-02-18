# ⚠️ Docker I/O Error - Diagnosis & Solutions

## Problem Actual

Docker está mostrando errores de I/O (input/output error):
```
Error: open /var/lib/docker/containers/.../.tmp-config.v2.json: input/output error
```

**Causa:** Corrupción del almacenamiento interno de Docker Desktop (no es culpa de nuestro código)

---

## ✅ Solución 1: Reiniciar Docker Desktop (MÁS RÁPIDO)

1. **Abre Docker Desktop**
2. **Click en el ícono de settings** (⚙️)
3. **Troubleshoot** → **Reset Kubernetes** o **Clean / Purge data**
4. **Restart Docker Desktop**

Luego:
```powershell
cd c:\Users\catal\OneDrive\Desktop\ClaraMente
docker-compose up -d
```

---

## ✅ Solución 2: Usar Backend Local (MÁS SIMPLE)

Ya tienes todo configurado localmente. Solo necesitas:

### Paso 1: Asegurar servicios auxiliares
```powershell
# Redis (necesario para cache)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# PostgreSQL (necesario para DB)
docker run -d --name postgres -p 5432:5432 \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=companion \
  postgres:15-alpine

# Qdrant (necesario para vectores)
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

### Paso 2: Iniciar backend local
```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0
```

### Paso 3: Iniciar frontend
```powershell
cd frontend
npm run dev -- --host
```

---

## Estado Actual

✅ **Código correcto** - Backend image rebuilt con Google AI
✅ **Configuración correcta** - `.env` tiene `GOOGLE_AI_API_KEY`
❌ **Docker corrupto** - Necesita reset de Docker Desktop

---

## Recomendación

**Opción A (Docker):** Restart Docker Desktop → `docker-compose up -d`
**Opción B (Local):** Servicios individuales + backend local + frontend local

¿Cuál prefieres?
