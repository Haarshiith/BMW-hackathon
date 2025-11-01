from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, engine
from app.schemas import HealthCheckResponse
from app.config import settings
from app.services.openai_service import openai_service
from datetime import datetime
import time

router = APIRouter(prefix="/health", tags=["health"])

# Store start time for uptime calculation
start_time = time.time()


@router.get(
    "/",
    response_model=HealthCheckResponse,
    summary="Health check",
    description="Check the health status of the API and its dependencies",
)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Perform a comprehensive health check"""
    try:
        # Check database connection
        db_status = "healthy"
        try:
            from sqlalchemy import text

            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        # Calculate uptime
        uptime_seconds = time.time() - start_time
        uptime_str = f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m {int(uptime_seconds % 60)}s"

        # Determine overall status
        overall_status = "healthy"
        if db_status != "healthy":
            overall_status = "unhealthy"

        return HealthCheckResponse(
            status=overall_status,
            version="1.0.0",
            database_status=db_status,
            uptime=uptime_str,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}",
        )


@router.get(
    "/database",
    summary="Database health check",
    description="Check the database connection specifically",
)
async def database_health_check():
    """Check database connection specifically"""
    try:
        from sqlalchemy import text

        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()

        return {
            "status": "healthy",
            "message": "Database connection successful",
            "test_query_result": row[0] if row else None,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}",
        )


@router.get(
    "/config",
    summary="Configuration check",
    description="Check application configuration (without exposing sensitive data)",
)
async def config_health_check():
    """Check application configuration"""
    try:
        return {
            "status": "healthy",
            "config": {
                "app_name": settings.app_name,
                "debug": settings.debug,
                "upload_dir": settings.upload_dir,
                "max_file_size": settings.max_file_size,
                "database_configured": bool(settings.database_url),
                "openai_configured": bool(
                    settings.openai_api_key
                    and settings.openai_api_key != "test_key_placeholder"
                ),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration check failed: {str(e)}",
        )
