#!/usr/bin/env python3
"""
Test Server - FastAPI server with optional services for testing
Gracefully handles missing Neo4j and Redis connections
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import structlog
import time
from typing import Dict, Any

from api.routers import audit, standards, agent_optimized, workflow
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
    Modified to gracefully handle missing services for testing
    """
    # Startup
    logger.info("Starting Code Standards Auditor API (TEST MODE)", version="1.0.0")

    # Initialize services with graceful degradation
    app.state.services_available = {
        "neo4j": False,
        "redis": False,
        "workflow": False,
        "standards_sync": False
    }

    # Try to initialize Neo4j connection
    try:
        app.state.neo4j = Neo4jService(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD
        )
        await app.state.neo4j.connect()
        app.state.services_available["neo4j"] = True
        logger.info("✅ Neo4j connection established")
    except Exception as e:
        logger.warning("⚠️  Neo4j connection failed - continuing without Neo4j", error=str(e))
        app.state.neo4j = None

    # Try to initialize cache service
    try:
        app.state.cache = CacheService(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD
        )
        await app.state.cache.connect()
        app.state.services_available["redis"] = True
        logger.info("✅ Redis cache connection established")
    except Exception as e:
        logger.warning("⚠️  Redis connection failed - continuing without cache", error=str(e))
        app.state.cache = None

    # Try to initialize integrated workflow service
    try:
        app.state.workflow_service = IntegratedWorkflowService()
        app.state.services_available["workflow"] = True
        logger.info("✅ Integrated workflow service initialized")
    except Exception as e:
        logger.warning("⚠️  Workflow service initialization failed", error=str(e))
        app.state.workflow_service = None

    # Try to initialize standards synchronization service
    try:
        if app.state.neo4j:
            standards_dir = Path(settings.STANDARDS_BASE_PATH)
            if standards_dir.exists():
                sync_service = StandardsSyncService(
                    neo4j_service=app.state.neo4j,
                    standards_dir=standards_dir
                )

                # Run initial sync
                await sync_service.sync_all()

                # Start scheduled sync (every hour)
                scheduled_sync = ScheduledSyncService(
                    sync_service=sync_service,
                    interval_seconds=3600  # 1 hour
                )
                await scheduled_sync.start()

                app.state.sync_service = sync_service
                app.state.scheduled_sync = scheduled_sync
                app.state.services_available["standards_sync"] = True
                logger.info("✅ Standards sync service initialized (1 hour interval)")
            else:
                logger.warning(f"⚠️  Standards directory not found: {standards_dir}")
                app.state.sync_service = None
                app.state.scheduled_sync = None
        else:
            logger.info("ℹ️  Standards sync disabled (Neo4j not available)")
            app.state.sync_service = None
            app.state.scheduled_sync = None
    except Exception as e:
        logger.warning("⚠️  Standards sync initialization failed", error=str(e))
        app.state.sync_service = None
        app.state.scheduled_sync = None

    # Log overall status
    available_services = [k for k, v in app.state.services_available.items() if v]
    logger.info(
        "Server startup complete",
        available_services=available_services,
        degraded_mode=len(available_services) < 3
    )

    yield

    # Shutdown
    logger.info("Shutting down Code Standards Auditor API")

    try:
        # Stop scheduled sync
        if hasattr(app.state, 'scheduled_sync') and app.state.scheduled_sync:
            await app.state.scheduled_sync.stop()
            logger.info("Standards sync service stopped")

        # Close connections if they exist
        if app.state.neo4j:
            await app.state.neo4j.disconnect()
            logger.info("Neo4j connection closed")
        if app.state.cache:
            await app.state.cache.disconnect()
            logger.info("Redis connection closed")
        logger.info("All connections closed successfully")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title="Code Standards Auditor API (TEST)",
    description="AI-powered code auditing and standards management API - Test Mode",
    version="1.0.0-test",
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
# Note: Commenting out AuthMiddleware for easier testing
# app.add_middleware(AuthMiddleware)

# Include routers
app.include_router(
    audit.router,
    prefix="/api/v1/audit",
    tags=["audit"]
)
app.include_router(
    standards.router,
    prefix="/api/v1/standards",
    tags=["standards"]
)
app.include_router(
    agent_optimized.router,
    tags=["agent-optimized"]
)
app.include_router(
    workflow.router,
    tags=["integrated-workflow"]
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint - API information
    """
    return {
        "name": "Code Standards Auditor API (TEST MODE)",
        "version": "1.0.0-test",
        "status": "operational",
        "documentation": "/docs",
        "health": "/api/v1/health",
        "note": "Running in test mode with graceful service degradation"
    }


@app.get("/api/v1/health")
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Health check endpoint
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0-test",
        "services": {},
        "mode": "test"
    }

    # Check Neo4j connection
    if hasattr(request.app.state, 'neo4j') and request.app.state.neo4j:
        try:
            await request.app.state.neo4j.health_check()
            health_status["services"]["neo4j"] = "connected"
        except Exception as e:
            health_status["services"]["neo4j"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    else:
        health_status["services"]["neo4j"] = "not configured"

    # Check Redis connection
    if hasattr(request.app.state, 'cache') and request.app.state.cache:
        try:
            await request.app.state.cache.health_check()
            health_status["services"]["redis"] = "connected"
        except Exception as e:
            health_status["services"]["redis"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    else:
        health_status["services"]["redis"] = "not configured"

    # Check workflow service
    if hasattr(request.app.state, 'workflow_service') and request.app.state.workflow_service:
        health_status["services"]["workflow"] = "initialized"
    else:
        health_status["services"]["workflow"] = "not configured"

    # Add services availability summary
    if hasattr(request.app.state, 'services_available'):
        health_status["services_available"] = request.app.state.services_available

    return health_status


@app.get("/api/v1/test-info")
async def test_info(request: Request) -> Dict[str, Any]:
    """
    Test mode information endpoint
    """
    return {
        "mode": "test",
        "authentication": "disabled",
        "services_available": getattr(request.app.state, 'services_available', {}),
        "routers_loaded": [
            "/api/v1/audit",
            "/api/v1/standards",
            "/agent-optimized",
            "/workflow"
        ],
        "middleware": [
            "CORS",
            "Logging",
            "RateLimit"
        ],
        "note": "This server is running in test mode with optional service connections"
    }


@app.get("/api/v1/sync/status")
async def sync_status(request: Request) -> Dict[str, Any]:
    """
    Get standards synchronization status
    """
    if not hasattr(request.app.state, 'sync_service') or not request.app.state.sync_service:
        return {
            "enabled": False,
            "message": "Standards synchronization is not enabled"
        }

    status = await request.app.state.sync_service.get_sync_status()
    status["enabled"] = True

    if hasattr(request.app.state, 'scheduled_sync') and request.app.state.scheduled_sync:
        status["scheduled"] = True
        status["interval_seconds"] = request.app.state.scheduled_sync.interval_seconds
        status["running"] = request.app.state.scheduled_sync.running
    else:
        status["scheduled"] = False

    return status


@app.post("/api/v1/sync/trigger")
async def trigger_sync(request: Request, force: bool = False) -> Dict[str, Any]:
    """
    Manually trigger standards synchronization
    """
    if not hasattr(request.app.state, 'sync_service') or not request.app.state.sync_service:
        return {
            "success": False,
            "error": "Standards synchronization is not enabled"
        }

    try:
        stats = await request.app.state.sync_service.sync_all(force=force)
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error("Manual sync failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


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

    print("\n" + "="*60)
    print("  CODE STANDARDS AUDITOR - TEST SERVER")
    print("="*60)
    print("\n✨ Starting server with graceful service degradation...")
    print("📝 Swagger docs will be available at: http://localhost:8000/docs")
    print("🏥 Health check at: http://localhost:8000/api/v1/health")
    print("ℹ️  Test info at: http://localhost:8000/api/v1/test-info")
    print("\n⚠️  NOTE: Running in TEST mode")
    print("   - Authentication middleware disabled")
    print("   - Services are optional (Neo4j, Redis)")
    print("   - Graceful degradation enabled")
    print("\n" + "="*60 + "\n")

    uvicorn.run(
        "test_server:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower()
    )
