from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import os

from app.config import settings
from app.database import init_db
from app.api.v1 import (
    lessons,
    departments,
    statistics,
    health,
    files,
    lessons_with_files,
    solution_search,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Lessons Learned API...")
    try:
        await init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    print("🛑 Shutting down Lessons Learned API...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="A comprehensive API for managing quality issues and lessons learned in manufacturing processes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": str(exc) if settings.debug else "Internal server error",
            "timestamp": "2024-01-01T00:00:00Z",  # This would be dynamic in production
        },
    )


# Include API routers
app.include_router(lessons.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(statistics.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(lessons_with_files.router, prefix="/api/v1")
app.include_router(solution_search.router, prefix="/api/v1")

# Mount static files for uploads
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
if os.path.exists(uploads_dir):
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


# Root endpoint
@app.get("/", summary="API Root", description="Welcome endpoint with API information")
async def root():
    """Root endpoint with API information"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": "/api/v1/health",
        "endpoints": {
            "lessons": "/api/v1/lessons",
            "departments": "/api/v1/departments",
            "statistics": "/api/v1/statistics",
            "health": "/api/v1/health",
            "files": "/api/v1/files",
            "lessons-with-files": "/api/v1/lessons",
            "solution-search": "/api/v1/solution-search",
        },
    }


# API info endpoint
@app.get(
    "/api/info", summary="API Information", description="Get detailed API information"
)
async def api_info():
    """Get detailed API information"""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "description": "A comprehensive API for managing quality issues and lessons learned",
        "features": [
            "CRUD operations for lessons learned",
            "Department-level analytics",
            "Advanced filtering and search",
            "Statistics and trend analysis",
            "File upload support",
            "AI-powered analysis integration",
            "Solution search across multiple sources",
        ],
        "endpoints": {
            "lessons": {
                "create": "POST /api/v1/lessons",
                "create_with_files": "POST /api/v1/lessons/create-with-files",
                "get_all": "GET /api/v1/lessons",
                "get_by_id": "GET /api/v1/lessons/{id}",
                "update": "PUT /api/v1/lessons/{id}",
                "delete": "DELETE /api/v1/lessons/{id}",
                "summary": "GET /api/v1/lessons/{id}/summary",
                "regenerate_ai": "POST /api/v1/lessons/{id}/regenerate-ai",
                "add_attachments": "POST /api/v1/lessons/{id}/add-attachments",
                "remove_attachment": "DELETE /api/v1/lessons/{id}/attachments/{filename}",
            },
            "departments": {
                "list": "GET /api/v1/departments",
                "lessons": "GET /api/v1/departments/{department}/lessons",
                "summary": "GET /api/v1/departments/{department}/summary",
                "statistics": "GET /api/v1/departments/{department}/statistics",
            },
            "statistics": {
                "overview": "GET /api/v1/statistics/overview",
                "trends": "GET /api/v1/statistics/trends",
                "severity": "GET /api/v1/statistics/severity",
                "departments": "GET /api/v1/statistics/departments",
            },
            "health": {
                "check": "GET /api/v1/health",
                "database": "GET /api/v1/health/database",
                "config": "GET /api/v1/health/config",
            },
            "files": {
                "upload_single": "POST /api/v1/files/upload",
                "upload_multiple": "POST /api/v1/files/upload-multiple",
                "delete": "DELETE /api/v1/files/{filename}",
                "info": "GET /api/v1/files/{filename}/info",
                "config": "GET /api/v1/files/config",
            },
            "solution-search": {
                "submit": "POST /api/v1/solution-search/submit",
                "get_results": "GET /api/v1/solution-search/{search_id}",
                "get_status": "GET /api/v1/solution-search/{search_id}/status",
                "refine": "POST /api/v1/solution-search/{search_id}/refine",
                "save_solution": "POST /api/v1/solution-search/{search_id}/save",
                "history": "GET /api/v1/solution-search/history",
                "saved_solutions": "GET /api/v1/solution-search/saved",
            },
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
