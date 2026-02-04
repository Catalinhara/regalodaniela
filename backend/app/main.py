import logging
import sys
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.infrastructure.database import engine, Base
from app.api.routes import router as companion_router
from app.api.auth_routes import router as auth_router
from app.api.endpoints.analysis import router as analysis_router

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB connection
    print("Starting up Clinical Companion Backend...")
    
    # Run migrations automatically
    try:
        import subprocess
        print("Running database migrations...")
        # We run this in a shell to ensure 'alembic' is found in the path
        # 'upgrade head' ensures the DB is at the latest version
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Migrations applied successfully.")
    except Exception as e:
        print(f"Migration error: {e}")
        # In production, you might want to exit if migrations fail
        
    yield
    # Shutdown: Close connections
    print("Shutting down...")

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Clinical Companion API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

from app.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization", "Content-Type", "Accept"],
    expose_headers=["*"]
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    # same-origin-allow-popups is required for Google OAuth popup
    # same-origin-allow-popups is safer than unsafe-none
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    # Added Cross-Origin-Resource-Policy for GIS
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "companion-backend",
        "version": "0.1.0"
    }

app.include_router(auth_router)
app.include_router(companion_router)
app.include_router(analysis_router)

