"""Storage for RoomBook. The only module that imports sqlite3 or contains SQL.

Every method opens its own connection and closes it before returning, so the
repository is safe to use from FastAPI's worker threads. It stores and fetches; it does
not validate. The service decides what is allowed.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import Any

ROOMS = [
    (1, "Quiet Room A", 2),
    (2, "Quiet Room B", 2),
    (3, "Group Room C", 6),
    (4, "Group Room D", 8),
]

_BOOKING_COLUMNS = 'id, room_id, date, start, "end", booked_by'


def _booking(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "room_id": row["room_id"],
        "date": row["date"],
        "start": row["start"],
        "end": row["end"],
        "booked_by": row["booked_by"],
    }


class Repository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create the tables if missing, and add the four rooms if there are none."""
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS rooms ("
                " id INTEGER PRIMARY KEY,"
                " name TEXT NOT NULL,"
                " capacity INTEGER NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS bookings ("
                " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " room_id INTEGER NOT NULL REFERENCES rooms(id),"
                " date TEXT NOT NULL,"
                " start TEXT NOT NULL,"
                ' "end" TEXT NOT NULL,'
                " booked_by TEXT NOT NULL)"
            )
            (count,) = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()
            if count == 0:
                conn.executemany("INSERT INTO rooms (id, name, capacity) VALUES (?, ?, ?)", ROOMS)

    def list_rooms(self) -> list[dict[str, Any]]:
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT id, name, capacity FROM rooms ORDER BY id").fetchall()
        return [{"id": r["id"], "name": r["name"], "capacity": r["capacity"]} for r in rows]

    def list_bookings(self, date: str, room_id: int | None = None) -> list[dict[str, Any]]:
        sql = f"SELECT {_BOOKING_COLUMNS} FROM bookings WHERE date = ?"
        params: list[Any] = [date]
        if room_id is not None:
            sql += " AND room_id = ?"
            params.append(room_id)
        sql += " ORDER BY room_id, start, id"
        with closing(self._connect()) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_booking(r) for r in rows]

    def has_overlap(self, room_id: int, date: str, start: str, end: str) -> bool:
        """True when a booking in that room on that date overlaps [start, end).
        HH:MM strings are fixed width, so comparing them as text compares the times."""
        with closing(self._connect()) as conn:
            row = conn.execute(
                'SELECT 1 FROM bookings WHERE room_id = ? AND date = ? AND start < ? AND ? < "end" LIMIT 1',
                (room_id, date, end, start),
            ).fetchone()
        return row is not None

    def insert_booking(self, room_id: int, date: str, start: str, end: str, booked_by: str) -> dict[str, Any]:
        with closing(self._connect()) as conn, conn:
            cur = conn.execute(
                'INSERT INTO bookings (room_id, date, start, "end", booked_by) VALUES (?, ?, ?, ?, ?)',
                (room_id, date, start, end, booked_by),
            )
            booking_id = cur.lastrowid
        return {"id": booking_id, "room_id": room_id, "date": date, "start": start, "end": end, "booked_by": booked_by}

    def delete_booking(self, booking_id: int) -> bool:
        with closing(self._connect()) as conn, conn:
            cur = conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
            return cur.rowcount == 1
