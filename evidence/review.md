# Reviewer report (Part 7)

The `reviewer` subagent's report, exactly as returned (definition:
`.claude/agents/reviewer.md`, read-only tools Read, Grep and Glob). It ran on 2026-11-21
on commit edaf980, at the same time as the contract-checker.

---

1. app/repository.py:72 | L1 | blocking | `list_bookings` builds its SQL with an f-string (`f"SELECT {_BOOKING_COLUMNS} FROM bookings ..."`) and then adds to it with `+=` (lines 75 and 77). AGENTS.md "Backend rules" says "never build SQL with string formatting". The values are still passed through `?` placeholders and only constant text is joined in, so no user input gets into the SQL, but the rule as written is broken. Fix: use two fixed SQL strings, one with the room filter and one without. (AGENTS.md has no ID for this rule; L1 is the closest.)
2. app/routes.py:56 | R9 | minor | `json.loads(raw)` catches only `ValueError`. A deeply nested body such as `[[[[...]]]]` raises `RecursionError`, which gives a 500 without the `{"error","message"}` body instead of `422 invalid_request`. This is a risk, not a normal case.
3. app/service.py:93 | R7 | minor | The overlap check (`has_overlap`) and the insert (`insert_booking`, line 96) use separate connections and separate transactions, with no lock between them. It is safe today only because `create_booking` in routes.py is `async` and nothing awaits between the two calls. If this changes (a sync route, or several worker processes), two overlapping bookings could both be saved. Not in the spec.
4. app/routes.py:53 | L2 | minor | `create_booking` is `async def` but calls the synchronous service and sqlite3 code directly, so every POST blocks the event loop while the database is in use. The other routes are sync and run in the threadpool. Style and performance risk, not in the spec.

Files reviewed: app/__init__.py, app/main.py, app/routes.py, app/service.py, app/repository.py, app/models.py
