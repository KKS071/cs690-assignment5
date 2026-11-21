"""Business rules for RoomBook: every rule in spec section 5 is enforced here.

No HTTP and no SQL. Errors are raised as BookingError with a code from spec section 6;
app/routes.py turns them into responses.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.models import BookingRequest, is_valid_date, parse_int
from app.repository import Repository

NAME_MAX = 40
OPENING = 8 * 60          # 08:00
CLOSING = 22 * 60         # 22:00
MAX_MINUTES = 180         # R5: at most 3 hours
ALLOWED_MINUTES = {0, 30}
SQLITE_MAX_INT = 2**63 - 1
DAILY_LIMIT = 2           # R11: at most two bookings per person per date


class BookingError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _person_key(name: str) -> str:
    """R11: two names are the same person after trimming and ignoring case."""
    return name.strip().lower()


def _minutes(hhmm: str) -> int:
    return int(hhmm[:2]) * 60 + int(hhmm[3:])


class BookingService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    # R1
    def list_rooms(self) -> list[dict[str, Any]]:
        return self.repo.list_rooms()

    def _room_ids(self) -> set[int]:
        return {room["id"] for room in self.repo.list_rooms()}

    # R2
    def list_bookings(self, date: str | None, room_id: str | None) -> list[dict[str, Any]]:
        if date is None or not is_valid_date(date):
            raise BookingError("invalid_request", "date is required, as a real day written YYYY-MM-DD")
        room: int | None = None
        if room_id is not None:
            room = parse_int(room_id)
            if room is None:
                raise BookingError("invalid_request", "room_id must be an integer")
            if room not in self._room_ids():
                raise BookingError("room_not_found", "There is no room with that id.")
        return self.repo.list_bookings(date, room)

    # R3 to R7 and R11, checked in the R9 order; nothing is written until every check passes.
    def create_booking(self, data: object) -> dict[str, Any]:
        # R3
        if not isinstance(data, dict):
            raise BookingError("invalid_request", "The body must be a JSON object.")
        try:
            req = BookingRequest.model_validate(data)
        except ValidationError as err:
            first = err.errors()[0]
            where = ".".join(str(p) for p in first.get("loc", ())) or "body"
            raise BookingError("invalid_request", f"{where}: {first.get('msg', 'invalid')}") from None

        # R4
        name = req.booked_by.strip()
        if not 1 <= len(name) <= NAME_MAX:
            raise BookingError("invalid_name", "The name must be 1 to 40 characters.")

        # R5
        start, end = _minutes(req.start), _minutes(req.end)
        if (
            start % 60 not in ALLOWED_MINUTES
            or end % 60 not in ALLOWED_MINUTES
            or start < OPENING
            or end > CLOSING
            or start >= end
            or end - start > MAX_MINUTES
        ):
            raise BookingError("invalid_time", "Bookings use :00 or :30, between 08:00 and 22:00, for at most 3 hours.")

        # R6
        if req.room_id not in self._room_ids():
            raise BookingError("room_not_found", "There is no room with that id.")

        # R7, R11 and the insert run inside one write transaction (ADR 0001).
        with self.repo.write_transaction() as tx:
            # R7
            if tx.has_overlap(req.room_id, req.date, req.start, req.end):
                raise BookingError("overlap", "That room is already booked for part of that time.")

            # R11: same person = equal after trimming and ignoring case, across all rooms.
            person = _person_key(name)
            held = sum(1 for other in tx.names_on_date(req.date) if _person_key(other) == person)
            if held >= DAILY_LIMIT:
                raise BookingError("daily_limit", "That person already has 2 bookings on that date.")

            return tx.insert_booking(req.room_id, req.date, req.start, req.end, name)

    # R8
    def cancel_booking(self, raw_id: str) -> None:
        booking_id = parse_int(raw_id)
        if booking_id is None:
            raise BookingError("invalid_request", "The booking id must be an integer.")
        if abs(booking_id) > SQLITE_MAX_INT or not self.repo.delete_booking(booking_id):
            raise BookingError("booking_not_found", "There is no booking with that id.")
