"""
ObraHunter - Aplicação Principal
API REST + Auth + Notificações + Scheduler automático
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import router as main_router
from app.api.auth_routes import router as auth_router
from app.api.notif_routes import router as notif_router
from app.tasks.scheduler import ObraHunterScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

scheduler = ObraHunterScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle — inicia banco e scheduler"""
    logger.info("🏗️ Iniciando ObraHunter...")
    await init_db()
    logger.info("✅ Banco de dados inicializado")

    if settings.SCHEDULER_ENABLED:
        scheduler_task = asyncio.create_task(scheduler.iniciar())
        logger.info("🤖 Scheduler de buscas automáticas iniciado (24/7)")

    yield
    await scheduler.parar()
    logger.info("👋 ObraHunter encerrado")


app = FastAPI(
    title="ObraHunter API",
    description=(
        "Sistema automatizado de prospecção de obras. "
        "Multi-usuário com autenticação JWT, notificações in-app, "
        "busca contínua 24/7 e score de oportunidade."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(auth_router, prefix="/api/v1")
app.include_router(notif_router, prefix="/api/v1")
app.include_router(main_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "scheduler_enabled": settings.SCHEDULER_ENABLED,
        "features": ["multi-user", "jwt-auth", "in-app-notifications", "auto-search-24/7"],
    }


@app.get("/")
async def root():
    return {
        "app": "ObraHunter",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
