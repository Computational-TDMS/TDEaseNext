"""
FastAPI Application Entry Point
Main application configuration and startup
"""

import sys
from pathlib import Path

# Add src directory to Python path (workflow, nodes)
_project_root = Path(__file__).parent.parent
_src_path = _project_root / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os

from importlib import import_module
workflow = import_module("app.api.workflow")
try:
    tools = import_module("app.api.tools")
except Exception:
    tools = None
try:
    files = import_module("app.api.files")
except Exception:
    files = None
try:
    batch_config = import_module("app.api.batch_config")
except Exception:
    batch_config = None
try:
    tool_schemas = import_module("app.api.tool_schemas")
except Exception:
    tool_schemas = None
try:
    workspace = import_module("app.api.workspace")
except Exception:
    workspace = None
try:
    compute_proxy = import_module("app.api.compute_proxy")
except Exception:
    compute_proxy = None
from app.core.websocket import manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log", mode="a") if Path("logs").exists() else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler"""
    # Startup
    logger.info("TDEase API Server starting up...")
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    logger.info("TDEase API Server startup complete")
    
    yield
    
    # Shutdown
    logger.info("TDEase API Server shutting down...")
    
    # Cleanup WebSocket connections
    await manager.cleanup_all_connections()
    
    logger.info("TDEase API Server shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="TDEase API",
    description="质谱数据分析工作流平台 - Mass Spectrometry Data Analysis Workflow Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.local", "testserver"]
)

# Include API routers
app.include_router(workflow.router, prefix="/api/workflows", tags=["workflows"])
try:
    executions = import_module("app.api.execution")
    app.include_router(executions.router, prefix="/api/executions", tags=["executions"])
except Exception:
    pass
if tools is not None:
    app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
if files is not None:
    app.include_router(files.router, prefix="/api/files", tags=["files"])
if batch_config is not None:
    app.include_router(batch_config.router)  # Already has /api/batch-configs prefix
if tool_schemas is not None:
    app.include_router(tool_schemas.router, prefix="/api/tools", tags=["tools"])
if workspace is not None:
    app.include_router(workspace.router, prefix="/api", tags=["workspace"])
if compute_proxy is not None:
    app.include_router(compute_proxy.router, prefix="/api/compute-proxy", tags=["compute-proxy"])

# WebSocket route
@app.websocket("/ws/{workflow_id}")
async def websocket_endpoint(websocket, workflow_id: str):
    """WebSocket endpoint for real-time workflow monitoring"""
    await manager.websocket_endpoint(websocket, workflow_id)

@app.websocket("/ws/executions/{execution_id}")
async def execution_websocket_endpoint(websocket, execution_id: str):
    """WebSocket endpoint for real-time execution logs and status"""
    await manager.execution_websocket_endpoint(websocket, execution_id)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TDEase API Server",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
            name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
        )) if logger.handlers else None,
        "version": "1.0.0"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "request_id": id(request)
        }
    )

# Startup and shutdown events are now handled by lifespan context manager above

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
