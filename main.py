"""
TDEase Backend Main Application Entry Point with Integrated System Management
"""
import asyncio
import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from app.core.app import create_app
from app.core.config import get_settings
from app.core.integration import initialize_system, cleanup_system
from app.core.production import initialize_production, shutdown_production

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with system integration"""
    logger.info("Starting TDEase Backend with system integration...")
    
    try:
        # Initialize system based on environment
        if settings.environment == "production":
            await initialize_production()
        else:
            await initialize_system()
        
        logger.info("TDEase Backend startup completed")
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down TDEase Backend...")
        
        try:
            if settings.environment == "production":
                await shutdown_production()
            else:
                await cleanup_system()
            
            logger.info("TDEase Backend shutdown completed")
        except Exception as e:
            logger.error(f"Shutdown error: {e}")


def create_integrated_app() -> FastAPI:
    """Create FastAPI application with integrated system management"""
    # Create base app
    app = create_app()
    
    # Override lifespan with integrated system management
    app.router.lifespan_context = lifespan
    
    # Add system status endpoints
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        try:
            from app.core.integration import system_integration
            if system_integration.is_initialized():
                status = await system_integration.get_system_status()
                return {
                    "status": "healthy",
                    "system": status,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            else:
                return {
                    "status": "initializing",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }

    @app.get("/system/status")
    async def system_status():
        """Detailed system status endpoint"""
        try:
            from app.core.integration import system_integration
            from app.core.production import get_production_manager
            
            if settings.environment == "production":
                prod_manager = get_production_manager()
                if prod_manager:
                    return await prod_manager.get_status()
            
            if system_integration.is_initialized():
                return await system_integration.get_system_status()
            else:
                return {"status": "not_initialized"}
                
        except Exception as e:
            logger.error(f"System status error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    return app


def main():
    """Main entry point for the TDEase backend application"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create integrated app
    app = create_integrated_app()
    
    # Run the application
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "development" else False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
