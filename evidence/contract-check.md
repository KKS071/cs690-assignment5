# Contract-checker report (Part 7)

The `contract-checker` subagent's report, exactly as returned (definition:
`.claude/agents/contract-checker.md`, read-only tools Read, Grep and Glob). It ran on
2026-11-21 on commit edaf980, at the same time as the reviewer.

---

| # | Item | What the page does | What the spec says | What the backend does | Match or mismatch |
|---|---|---|---|---|---|
| 1 | `GET /api/rooms` | `api("GET", "/api/rooms")`, no query, no body (app.js:161) | Section 4: `200`, a list of rooms (R1) | `@router.get("/rooms")` under prefix `/api`, returns `200` with `service.list_rooms()` (routes.py:37-39) | Match |
| 2 | `GET /api/bookings?date=` | Sends `date` = date input value, URL-encoded (string `YYYY-MM-DD`). Never sends `room_id` (app.js:148) | Section 4 / R2: `date` is required, `room_id` is optional; `200`, a list of bookings | Reads `date` and `room_id` from `query_params`, passes them to the service, `200` on success, R9 error body on `BookingError` (routes.py:42-49) | Match |
| 3 | `POST /api/bookings` request | Header `Content-Type: application/json`. Body `{room_id: Number(select) -> JSON number (integer), date: string, start: string "HH:MM", end: string "HH:MM", booked_by: string, not trimmed}`. The selects offer start 08:00-21:30 and end 08:30-22:00 in 30-minute steps (app.js:158-159, 183-191) | Section 4 / R3: five fields; `room_id` is an integer, the other four are strings; D3 says the body is read as JSON whatever the header says | Reads the raw body with `json.loads`; invalid JSON gives `422 invalid_request`; otherwise `service.create_booking(data)`. `BookingRequest` is strict: `room_id: int`, four `str` fields, date and time format validators, extra fields ignored (routes.py:52-63, models.py:42-65) | Match |
| 4 | `DELETE /api/bookings/{id}` | Path `"/api/bookings/" + booking.id` (the number from the list response), no body (app.js:203) | Section 4 / R8: `204`, empty body | `@router.delete("/bookings/{booking_id}")` takes the id as `str`, calls `service.cancel_booking`, returns `Response(status_code=204)` (routes.py:66-72) | Match |
| 5 | Rooms response fields | Loops over the response as an array and reads `room.id`, `room.name`, `room.capacity` (app.js:106-114, 171-175) | Section 4: a room has exactly `id`, `name`, `capacity`; section 2 gives the values | Passes `service.list_rooms()` through unchanged. The field names are built in app/service.py, which this check does not read | Match with the spec; backend side not verified |
| 6 | Bookings list response fields | Loops over the response as an array and reads `room_id`, `id`, `start`, `end`, `booked_by`. Does not read `date` (app.js:119-135) | Section 4: a booking has exactly `id`, `room_id`, `date`, `start`, `end`, `booked_by` | Passes the service result through unchanged (routes.py:49); fields are built in service.py (not read) | Match with the spec; backend side not verified |
| 7 | Created booking response | Treats any 2xx (`response.ok`) as success and does not check for `201`. Reads `start`, `end`, `booked_by` (app.js:191-192) | `201`, the new booking (six fields); R4 says the returned name is trimmed | Returns `201` with the service result (routes.py:63) | Match (status matches; fields come from service.py, not read) |
| 8 | Error body | Reads `data.error` and `data.message` only when each is a string. A body that is not JSON becomes `null` and shows a generic "The server answered N" message (app.js:45-54, 68) | R9: every error body is exactly `{"error": "<code>", "message": "<text>"}`; D11 says paths outside section 4 keep the framework's default body | `error_response` returns `{"error": code, "message": message}` with the status taken from `STATUS`. A `RequestValidationError` handler also returns an R9 body (routes.py:28-30, main.py:29-33) | Match |
| 9 | Status codes for each code | The page does not map a status to a code. It uses only `error` to look up `MESSAGES` | Section 6: `invalid_request`/`invalid_name`/`invalid_time` give 422, `room_not_found`/`booking_not_found` give 404, `overlap` gives 409 | `STATUS` dict holds the same six pairs (routes.py:18-25) | Match |
| 10 | `invalid_request` | Has a message, and is the only code whose server `message` is added to the page's text (app.js:16, 62-63) | 422; R2, R3, R8 | In `STATUS` as 422; also used for invalid JSON and by the validation safety net | Match |
| 11 | `invalid_name` | Message: "Enter your name, 40 characters at most." | 422; R4 (1-40 characters after trimming) | In `STATUS` as 422 | Match |
| 12 | `invalid_time` | Message: on the hour or half hour, 08:00-22:00, at most 3 hours | 422; R5 (same conditions, and start before end) | In `STATUS` as 422 | Match |
| 13 | `room_not_found` | Message: "That room does not exist. Reload the page." | 404; R2, R6 | In `STATUS` as 404 | Match |
| 14 | `booking_not_found` | Message: "That booking was already cancelled." | 404; R8 | In `STATUS` as 404 | Match |
| 15 | `overlap` | Message: room already booked for part of that time | 409; R7 | In `STATUS` as 409 | Match |
| 16 | `daily_limit` | Has a message: "You already have 2 bookings on that day..." (app.js:22) | Not in sections 4-6. Section 7 lists it under "Proposed, not built" | Not in `STATUS`, so the backend never sends it | Not in the spec (the page has a message for it, but nothing sends it, so no conflict) |
| 17 | Status check `404` on `/api/rooms` | If `GET /api/rooms` gets a 404, shows "The backend is not built yet." (app.js:163-164) | R1 defines no error for this route | The route is mounted, so it does not return 404 | Match (this fallback is never reached) |
| 18 | Status check `response.ok` / unknown code | Any status that is not 2xx throws `ApiError`. A code that is not in `MESSAGES` shows "The server answered <status>: <message>" | R9 / D11 | Section 4 endpoints always send a known code | Match |
| 19 | `204` handling | Checks `response.status === 204` before parsing and returns `null` without reading the body. `cancelBooking` ignores the result (app.js:42-44, 203) | R8: `204`, empty body; section 4: the 204 body is not JSON | `Response(status_code=204)` with no content | Match |

Mismatches:
- I found no mismatches. Every request, response status, error-body shape and error code the page uses agrees with the spec and with routes.py, models.py and main.py.
- Not in the spec: `daily_limit` (MESSAGES key). The spec defines no such rule or code (section 7 lists it as "Proposed, not built"), and the backend never sends it.
- Not verified: the response field names for rooms and bookings (rows 5-7). routes.py passes the service's results through unchanged, and those names are built in app/service.py, which is outside the files this check reads.
