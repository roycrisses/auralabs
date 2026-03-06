"""FastAPI application factory and server runner."""

from __future__ import annotations

import uvicorn
import python_multipart  # Explicitly import for PyInstaller bundling
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import body modules to trigger tool registration
import aura.body.clipboard  # noqa: F401
import aura.body.desktop  # noqa: F401
import aura.body.filesystem  # noqa: F401
import aura.body.process  # noqa: F401
import aura.body.web  # noqa: F401
import aura.body.apps  # noqa: F401
import aura.body.sysinfo  # noqa: F401
import aura.body.notify  # noqa: F401
import aura.body.schedule  # noqa: F401
import aura.body.workflow  # noqa: F401
import aura.body.vision  # noqa: F401
import aura.body.voice  # noqa: F401
import aura.body.knowledge  # noqa: F401
import aura.body.delegate  # noqa: F401
import aura.body.memory_tools  # noqa: F401
import aura.body.trigger_tools  # noqa: F401
import aura.mcp  # noqa: F401 — MCP support
from aura.server.routes import router
from aura.server.settings_routes import settings_router
from aura.server.upload import upload_router
from aura.server.webhook_routes import webhook_router


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    app = FastAPI(title="Aura", version="0.1.0", description="Multi-agent desktop orchestrator")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(upload_router, prefix="/api")
    app.include_router(webhook_router, prefix="/api")
    return app


app = create_app()


def run_server(host: str = "127.0.0.1", port: int = 8420):
    """Start the uvicorn server."""
    uvicorn.run(
        app,  # Pass the app instance directly
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    run_server()
