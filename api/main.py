"""
Code Standards Auditor API
Main FastAPI application entry point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import structlog
import time
from typing import Dict, Any

# from api.routers import audit  # Temporarily disabled - has FastAPI parameter injection issue
from api.routers import standards, agent_optimized, workflow
from services.integrated_workflow_service import IntegratedWorkflowService
from api.middleware.auth import AuthMiddleware
from api.middleware.logging import LoggingMiddleware
from api.middleware.rate_limit import RateLimitMiddleware
from config.settings import Settings
from services.neo4j_service import Neo4jService
from services.cache_service import CacheService
from services.standards_sync_service import StandardsSyncService, ScheduledSyncService
from pathlib import Path

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle - startup and shutdown
    """
    # Startup
    logger.info("Starting Code Standards Auditor API", version="1.0.0")
    
    # Initialize services
    try:
        # Initialize Neo4j connection
        app.state.neo4j = Neo4jService(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD,
            database=settings.NEO4J_DATABASE
        )
        await app.state.neo4j.connect()
        logger.info("Neo4j connection established")
        
        # Initialize cache service (optional - graceful degradation if Redis unavailable)
        try:
            app.state.cache = CacheService(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD
            )
            await app.state.cache.connect()
            logger.info("Redis cache connection established")
        except Exception as e:
            logger.warning(f"Redis unavailable, continuing without cache: {e}")
            app.state.cache = None
        
        # Initialize integrated workflow service
        app.state.workflow_service = IntegratedWorkflowService()
        logger.info("Integrated workflow service initialized")

        # Initialize and start automatic standards synchronization
        standards_dir = Path("/Volumes/FS001/pythonscripts/standards")
        sync_service = StandardsSyncService(
            neo4j_service=app.state.neo4j,
            standards_dir=standards_dir
        )
        app.state.scheduled_sync = ScheduledSyncService(
            sync_service=sync_service,
            interval_seconds=3600  # Sync every hour
        )
        await app.state.scheduled_sync.start()
        logger.info("Automatic standards synchronization started (interval: 1 hour)")

    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Code Standards Auditor API")

    try:
        # Stop automatic sync service
        if hasattr(app.state, 'scheduled_sync'):
            await app.state.scheduled_sync.stop()
            logger.info("Automatic standards synchronization stopped")

        # Close connections
        await app.state.neo4j.disconnect()
        if app.state.cache:
            await app.state.cache.disconnect()
        logger.info("All connections closed successfully")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title="Code Standards Auditor API",
    description="AI-powered code auditing and standards management API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, 
                  requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)
app.add_middleware(AuthMiddleware)

# Include routers
# app.include_router(  # Temporarily disabled - audit router has parameter injection issue
#     audit.router,
#     prefix="/api/v1/audit",
#     tags=["audit"]
# )
app.include_router(standards.router)  # Router already has prefix defined
app.include_router(agent_optimized.router)  # Router already has prefix defined
app.include_router(workflow.router)  # Router already has prefix defined

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint - API information
    """
    return {
        "name": "Code Standards Auditor API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/v1/health")
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Health check endpoint
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "services": {}
    }
    
    # Check Neo4j connection
    try:
        if hasattr(request.app.state, 'neo4j'):
            await request.app.state.neo4j.health_check()
            health_status["services"]["neo4j"] = "connected"
    except Exception as e:
        health_status["services"]["neo4j"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis connection
    try:
        if hasattr(request.app.state, 'cache'):
            await request.app.state.cache.health_check()
            health_status["services"]["redis"] = "connected"
    except Exception as e:
        health_status["services"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """
    Custom 404 handler
    """
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource {request.url.path} was not found",
            "path": request.url.path
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """
    Custom 500 handler
    """
    logger.error("Internal server error", 
                path=request.url.path, 
                error=str(exc))
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": request.state.request_id if hasattr(request.state, 'request_id') else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
