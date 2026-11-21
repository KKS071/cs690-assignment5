"""Converts rows from the old booking system's export (legacy/old_bookings.csv)
into the format of the new backend.

Written years ago for the old system. Nobody remembers every case it handles, and it
has no tests. The plan is to import the old bookings next term, so this code has to
be made safe to change first.

Refactored for readability only: every result and every exception is the same as
before, including the known-wrong ones pinned in tests/legacy/test_old_format.py
(for example "12:30 PM" -> "24:30", and a lowercase "pm" being ignored).

Run it on the sample export:
    python -m legacy.old_format legacy/old_bookings.csv
"""

from __future__ import annotations

ROOMS: dict[str, int] = {"Room A": 1, "Room B": 2, "Room C": 3, "Room D": 4}

WORD_SEPARATOR = " "      # between "9:00" and "AM"/"PM"; split on exactly one space
TIME_SEPARATOR = ":"
DATE_SEPARATOR = "/"      # old dates are month/day/year
PM_SUFFIX = "PM"          # matched case-sensitively, as the old system did
PM_HOUR_OFFSET = 12       # added to the hour for every PM time, 12 PM included
TWO_DIGIT_WIDTH = 2       # zero-padding for hours, months and days
SHORT_YEAR_LENGTH = 2     # only two-digit years get a century
CENTURY_PREFIX = "20"


def to_24h(text: str) -> str:
    """Convert an old time such as "1:00 PM" or "8:30" to "HH:MM".

    The hour is zero-padded and gets +12 when the second word is exactly "PM"; the
    minutes are copied as written. Known odd results are kept on purpose: "12:30 PM"
    gives "24:30", "12:00 AM" gives "12:00", "3:00 pm" gives "03:00", "9:5 AM" gives
    "09:5". Raises ValueError for a hour that is not a number, IndexError when there
    is no ":" and AttributeError when text is not a string.
    """
    words = text.strip().split(WORD_SEPARATOR)
    clock = words[0].split(TIME_SEPARATOR)
    hour = int(clock[0])          # evaluated before the minutes, as before
    minutes = clock[1]
    if len(words) > 1 and words[1] == PM_SUFFIX:
        hour = hour + PM_HOUR_OFFSET
    return str(hour).zfill(TWO_DIGIT_WIDTH) + TIME_SEPARATOR + minutes


def _to_iso_date(day: str) -> str:
    """Turn an old "month/day/year" date into "YYYY-MM-DD".

    Two-digit years get the "20" prefix; other years are kept as written. Month and
    day are zero-padded but not checked, so "14/3/2031" gives "2031-14-03". Raises
    IndexError when there are fewer than three parts.
    """
    parts = day.split(DATE_SEPARATOR)
    month = parts[0]
    day_of_month = parts[1]
    year = parts[2]
    if len(year) == SHORT_YEAR_LENGTH:
        year = CENTURY_PREFIX + year
    return year + "-" + month.zfill(TWO_DIGIT_WIDTH) + "-" + day_of_month.zfill(TWO_DIGIT_WIDTH)


def _capitalize_first(name: str) -> str:
    """Upper-case the first character only ("bo chen" -> "Bo chen"). Raises IndexError
    for an empty name."""
    return name[0].upper() + name[1:]


def parse_old_row(row: dict[str, str]) -> dict[str, int | str]:
    """Convert one CSV row (columns room, day, from, to, who) to a new-style booking.

    Fields are read in the old order (room, day, who, from, to), so a row with several
    problems raises the same exception as before: KeyError for an unknown room or a
    missing column, IndexError for a bad date or an empty name, and whatever to_24h
    raises for a bad time.
    """
    room_id = ROOMS[row["room"].strip()]
    date = _to_iso_date(row["day"].strip())
    booked_by = _capitalize_first(row["who"].strip())
    return {
        "room_id": room_id,
        "date": date,
        "start": to_24h(row["from"]),
        "end": to_24h(row["to"]),
        "booked_by": booked_by,
    }


if __name__ == "__main__":
    import csv
    import sys

    with open(sys.argv[1], newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            print(parse_old_row(row))
