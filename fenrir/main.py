"""Fenrir — FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fenrir.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    logger = logging.getLogger("fenrir")
    logger.info(
        f"Starting Fenrir v0.1.0 on {settings.fenrir_host}:{settings.fenrir_port}"
    )
    logger.info(f"  OpenEMR:  {settings.openemr_url}")
    logger.info(f"  FHIR:     {settings.openemr_fhir_url}")
    logger.info(f"  Heimdall: {settings.heimdall_url}")
    logger.info(f"  Headless: {settings.browser_headless}")
    logger.info(f"  Messages: {'enabled' if settings.message_enabled else 'disabled'}")

    # Start message poller if enabled
    poller = None
    if settings.message_enabled:
        from fenrir.openemr.message_poller import get_poller
        poller = get_poller()
        await poller.start()
        logger.info(f"  Poller:   polling every {settings.message_poll_interval}s as '{settings.fenrir_username}'")

    yield

    # Stop message poller
    if poller:
        await poller.stop()
    logger.info("Fenrir shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Fenrir — Computer-Use Agent",
        version="0.1.0",
        description="AI-powered browser automation and FHIR integration for the Asgard AI Platform.",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # JWT Auth (Yggdrasil + Zitadel)
    from fenrir.middleware.auth import JWTAuthMiddleware
    app.add_middleware(JWTAuthMiddleware)

    # Routers
    from fenrir.api.health import router as health_router
    from fenrir.api.mcp import router as mcp_router

    app.include_router(health_router)
    app.include_router(mcp_router)

    # Message poller status endpoint
    from fastapi import APIRouter
    from fenrir.openemr.message_poller import get_poller

    msg_router = APIRouter(tags=["messages"])

    @msg_router.get("/api/messages/status")
    async def message_poller_status():
        """Get the status of the OpenEMR message poller."""
        return get_poller().status.model_dump()

    app.include_router(msg_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "fenrir.main:app",
        host=settings.fenrir_host,
        port=settings.fenrir_port,
        reload=True,
    )
