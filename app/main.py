"""Builds the RoomBook application (spec section 3, R10).

    uvicorn app.main:create_app --factory --port 8000
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

from app.repository import Repository
from app.routes import error_response, router
from app.service import BookingService

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def create_app(db_path: str = "roombook.db") -> FastAPI:
    repo = Repository(db_path)
    repo.init_db()

    app = FastAPI(title="RoomBook")
    app.state.service = BookingService(repo)
    app.include_router(router)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Safety net: routes read raw input, so this should not fire, but if it does the
        # body still follows R9.
        return error_response("invalid_request", "The request was not valid.")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(FRONTEND / "index.html", media_type="text/html")

    @app.get("/app.js", include_in_schema=False)
    def app_js() -> FileResponse:
        return FileResponse(FRONTEND / "app.js", media_type="text/javascript")

    @app.get("/styles.css", include_in_schema=False)
    def styles_css() -> FileResponse:
        return FileResponse(FRONTEND / "styles.css", media_type="text/css")

    return app
