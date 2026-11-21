"""HTTP layer: parse requests, call the service, turn results and errors into responses.

No rules and no SQL here. Inputs are read raw so that the service, not FastAPI's own
validation, decides every error (R9).
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.service import BookingError, BookingService

router = APIRouter(prefix="/api")

STATUS = {
    "invalid_request": 422,
    "invalid_name": 422,
    "invalid_time": 422,
    "room_not_found": 404,
    "booking_not_found": 404,
    "overlap": 409,
}


def error_response(code: str, message: str) -> JSONResponse:
    """The one error body from R9."""
    return JSONResponse(status_code=STATUS[code], content={"error": code, "message": message})


def _service(request: Request) -> BookingService:
    return request.app.state.service


@router.get("/rooms")
def list_rooms(request: Request) -> JSONResponse:
    return JSONResponse(status_code=200, content=_service(request).list_rooms())


@router.get("/bookings")
def list_bookings(request: Request) -> JSONResponse:
    params = request.query_params
    try:
        bookings = _service(request).list_bookings(params.get("date"), params.get("room_id"))
    except BookingError as err:
        return error_response(err.code, err.message)
    return JSONResponse(status_code=200, content=bookings)


@router.post("/bookings")
async def create_booking(request: Request) -> JSONResponse:
    raw = await request.body()
    try:
        data = json.loads(raw)
    except (ValueError, RecursionError):
        # RecursionError: a body nested too deeply to parse still gets the R9 body.
        return error_response("invalid_request", "The body is not valid JSON.")
    try:
        booking = _service(request).create_booking(data)
    except BookingError as err:
        return error_response(err.code, err.message)
    return JSONResponse(status_code=201, content=booking)


@router.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: str, request: Request) -> Response:
    try:
        _service(request).cancel_booking(booking_id)
    except BookingError as err:
        return error_response(err.code, err.message)
    return Response(status_code=204)
