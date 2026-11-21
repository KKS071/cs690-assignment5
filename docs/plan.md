# Plan: RoomBook backend, R1 to R10

Drafted by the planning agent in plan mode (read-only), then reviewed and edited before
saving. Prompt: `prompts/05-plan.txt`. Three bounded tasks; each ends with
`python tools/check_layers.py` and `python -m pytest`, and both results are reported.

## Task 1

**Creates:** `app/repository.py`. It is the only file that imports `sqlite3` or holds SQL.

- `class Repository(db_path)`. Every method opens its own connection with
  `contextlib.closing(sqlite3.connect(db_path))` and uses `with conn:` to commit or roll
  back. A connection is never stored or shared. SQL uses `?` placeholders only.
- `init_db()` creates the two tables if they are missing:
  - `rooms(id INTEGER PRIMARY KEY, name, capacity)`;
  - `bookings(id INTEGER PRIMARY KEY AUTOINCREMENT, room_id, date, start, "end", booked_by)`.

  AUTOINCREMENT implements D9. The four rooms from section 2 are inserted only when the
  rooms table is empty, so a restart never adds them twice (R10).
- `list_rooms()` returns `{id, name, capacity}` dicts ordered by id (R1).
- `list_bookings(date, room_id=None)` returns six-field dicts ordered by `room_id`,
  then `start`, then `id` (R2, D8).
- `has_overlap(room_id, date, start, end)` is true when a booking in that room on that
  date has `start < new_end` and `new_start < end` (R7). Comparing the fixed-width
  `HH:MM` strings gives the right order.
- `insert_booking(...)` returns the new booking with its id.
- `delete_booking(id)` returns True when a row was removed.
- No validation lives here.

**Done:** `import app.repository` works, and the layer check shows no L1, L2 or L5
problem in this file (L4 still fails because the other modules do not exist yet). A
manual smoke check on a temporary file shows:
- running `init_db` twice still gives 4 rooms;
- insert and list work;
- an overlapping booking is detected and a touching one is not;
- delete returns True, then False.

No acceptance test can pass yet: all of them error with `No module named 'app.main'`
until Task 3.

## Task 2

**Creates:** `app/models.py` and `app/service.py`. Neither file imports fastapi,
starlette or sqlite3, and neither contains SQL.

**`app/models.py`** uses pydantic only.
- `BookingRequest` is strict and ignores extra fields. It has `room_id: int` and
  `date`, `start`, `end`, `booked_by: str`. Strict mode rejects `true`, `1.0`, `"1"`
  and `null` for `room_id` (D1).
- Validators use `re.fullmatch` with ASCII `[0-9]` classes (D2):
  - the date must match `YYYY-MM-DD` and be accepted by `datetime.date` (D10);
  - a time must match `HH:MM` from `00:00` to `23:59`.
- Helpers:
  - `is_valid_date(text)`;
  - `parse_int(text)`, which accepts `[+-]?[0-9]+` (D5) and returns None for anything
    else.

**`app/service.py`**
- `BookingError(code, message)` carries an error code from section 6.
- `BookingService(repo)` has these methods:
  - `list_rooms()` (R1).
  - `list_bookings(date, room_id)`: checks the date format, then the room_id format,
    then that the room exists (R2, D6).
  - `create_booking(data)` checks the rules in the R9 order, all before the first
    write:
    1. R3 shape;
    2. R4 name, trimmed, 1 to 40 code points (D4);
    3. R5 times: `:00` or `:30`, 08:00 to 22:00, start before end, at most 180 minutes;
    4. R6 room in the four ids;
    5. R7 `has_overlap`.

    Only then does it call `insert_booking`.
  - `cancel_booking(raw_id)`: a bad id gives `invalid_request`; an unknown id, or one
    outside SQLite's 64-bit range, gives `booking_not_found` (R8).

**Done:** both modules import, and the layer check shows no L1, L2 or L5 problem in
them. A manual smoke check through `BookingService(Repository(tmp))` gives the right
error code for one payload per rule and for the R9 order cases, and the bookings are
unchanged after each failure. Acceptance tests still error until Task 3.

## Task 3

**Creates:** `app/routes.py` and `app/main.py`.

**`app/routes.py`**
- An `APIRouter` that imports `app.service`, never `app.repository` (L3). It gets the
  service from `request.app.state.service`.
- It reads raw inputs, so FastAPI's own validation never decides an error:
  - query parameters with `request.query_params`; unknown ones are ignored (D7);
  - the POST body with `await request.body()` and `json.loads`, whatever the
    Content-Type (D3);
  - the path id as `str`.
- Responses:
  - a new booking returns `201`;
  - a cancel returns `204` with an empty body.
- It maps error codes to statuses: `invalid_*` to 422, `*_not_found` to 404,
  `overlap` to 409. Every error body is exactly `{"error", "message"}` (R9).

**`app/main.py`**
- `create_app(db_path: str = "roombook.db")`:
  1. builds the repository and calls `init_db()`;
  2. stores the service on `app.state`;
  3. includes the router;
  4. adds a `RequestValidationError` handler that returns `422 invalid_request`, as a
     safety net;
  5. serves `GET /`, `/app.js` and `/styles.css` from `frontend/` with `FileResponse`
     (R10).
- Paths outside section 4 keep the framework defaults (D11).

**Done:**
- `python tools/check_layers.py` passes L1 to L5.
- `python -m pytest` passes every test in `tests/acceptance/` (R1 to R10), with no
  test edited.
- `uvicorn app.main:create_app --factory --port 8000` serves the page, and booking and
  cancelling work in the browser.

## Not in this change

- **Locked and frozen files:** no edits to `frontend/`, `tests/acceptance/`,
  `tests/conftest.py`, `tools/`, `pytest.ini` or `requirements.txt`.
- **Rules the spec does not have:**
  - no `daily_limit` rule or code: it is only "Proposed, not built", even though the
    page has a message for it;
  - no capacity or head-count check (P2);
  - no past-date check (P1);
  - no login, and no ownership check when cancelling (P3).
- **Shape of the API:** no new endpoints (no PUT, PATCH or GET of a single booking), no
  new fields or error codes, and no custom error bodies for paths outside section 4
  (D11).
- **Dependencies:** no ORM, no migration tool, no new package, and no shared or pooled
  connection.
- **Concurrency control for R7.** Rejected from the draft plan: it had Task 1 make the
  overlap check and the insert one `BEGIN IMMEDIATE` transaction. That is a real design
  choice with costs, and Part 9 records it in ADR 0001, so it is not built ahead of that
  decision.
- **Extra work:** no extra unit tests or refactors beyond the five modules.
