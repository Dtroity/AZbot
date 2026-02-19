import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import init_db, engine
from .routes import orders_router, suppliers_router, filters_router, stats_router, activity_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and other resources"""
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection OK (host=%s, db=%s)", settings.postgres_host, settings.postgres_db)
        await init_db()
    except Exception as e:
        logger.error("Database connection failed: %s (check POSTGRES_HOST, POSTGRES_PASSWORD)", e)
    yield


# Create FastAPI app (redirect_slashes=False чтобы дашборд за /api/* не получал 307 на путь без /api/)
app = FastAPI(
    title="Supply Management API",
    description="Enterprise supply management system API",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(orders_router)
app.include_router(suppliers_router)
app.include_router(filters_router)
app.include_router(stats_router)
app.include_router(activity_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Supply Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/ready")
async def ready_check():
    """Проверка готовности: подключение к БД (для панели и отладки)."""
    try:
        from .database import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "error", "detail": str(e)},
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    err_str = str(exc).lower()
    if "connection" in err_str or "password" in err_str or "database" in err_str or "asyncpg" in err_str or "sqlalchemy" in err_str:
        logger.exception("Database error")
        return JSONResponse(
            status_code=503,
            content={
                "error": "database_unavailable",
                "detail": "Нет доступа к БД. Проверьте POSTGRES_HOST, POSTGRES_PASSWORD и логи api." if not settings.debug else str(exc)
            }
        )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "Something went wrong"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )
