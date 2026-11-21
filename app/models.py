"""Request shapes and format checks (spec R2, R3; decisions D1, D2, D5, D10).

Pydantic only: no HTTP and no SQL here.
"""

from __future__ import annotations

import datetime
import re

from pydantic import BaseModel, ConfigDict, field_validator

# ASCII digits only, matched against the whole string (D2).
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
TIME_PATTERN = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]")
INT_PATTERN = re.compile(r"[+-]?[0-9]+")


def is_valid_date(text: object) -> bool:
    """True when text is exactly YYYY-MM-DD and a real calendar day (R2, D10)."""
    if not isinstance(text, str) or DATE_PATTERN.fullmatch(text) is None:
        return False
    try:
        datetime.date(int(text[0:4]), int(text[5:7]), int(text[8:10]))
    except ValueError:
        return False
    return True


def is_valid_time(text: object) -> bool:
    """True when text is exactly HH:MM from 00:00 to 23:59 (R3)."""
    return isinstance(text, str) and TIME_PATTERN.fullmatch(text) is not None


def parse_int(text: object) -> int | None:
    """The integer in a query or path string, or None if it is not one (D5)."""
    if not isinstance(text, str) or INT_PATTERN.fullmatch(text) is None:
        return None
    return int(text)


class BookingRequest(BaseModel):
    """The body of POST /api/bookings (R3). Strict types (D1); unknown fields ignored."""

    model_config = ConfigDict(strict=True, extra="ignore")

    room_id: int
    date: str
    start: str
    end: str
    booked_by: str

    @field_validator("date")
    @classmethod
    def _date_format(cls, value: str) -> str:
        if not is_valid_date(value):
            raise ValueError("date must be a real day written as YYYY-MM-DD")
        return value

    @field_validator("start", "end")
    @classmethod
    def _time_format(cls, value: str) -> str:
        if not is_valid_time(value):
            raise ValueError("times must be written as HH:MM, from 00:00 to 23:59")
        return value
