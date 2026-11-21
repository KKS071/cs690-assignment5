# ADR 0001: Check and insert a booking inside one SQLite write transaction

Status: Accepted
Date: 2026-11-21

## Context

`POST /api/bookings` checked R7 (no overlap) and then inserted, with separate
connections and separate transactions: `has_overlap`, then `insert_booking`. R11 (the
daily limit) works the same way: it counts and then inserts. FastAPI runs requests on
several threads, and one SQLite file can be served by more than one worker process. When
two requests for the same room and time arrive together, both can read "no overlap"
before either one inserts, so both are saved. R7 is broken, and R11 can be broken the
same way. None of the acceptance tests shows this, because the test client sends one
request at a time.

We checked that this really happens. In `evidence/race_check.py`, 8 threads book the
same slot at once, 30 times. Before this change, 28 of the 30 trials saved more than one
overlapping booking. If nobody decides, the page will sometimes show two people in the
same room at the same time, and nothing will say so.

## Options considered

1. **Run the checks and the insert in one `BEGIN IMMEDIATE` transaction on one
   connection.** `BEGIN IMMEDIATE` takes SQLite's write lock at the start. A second
   writer waits (up to the connection's busy timeout of 10 s) until the first one
   commits, and then sees its booking.
   - Advantage: correct across threads *and* processes that share the file, with no new
     package, and the rule code stays in the service.
   - Cost: writes are serialized for the whole database file, not per room, and a
     request can wait for the lock. Under heavy load a request could hit the timeout
     and fail with `database is locked`.
2. **A process-wide `threading.Lock` in the service around check and insert.**
   - Advantage: the simplest change, and the repository does not change.
   - Cost: it protects only one process. Two uvicorn workers, or two `create_app`
     instances on the same file, still race.
3. **A SQLite trigger (`BEFORE INSERT ... RAISE(ABORT)`) that rejects an overlapping
   row.**
   - Advantage: the database itself enforces R7, even for writes that do not go
     through the app.
   - Cost: R7 and R11 logic would be written twice, in SQL and in the service. The
     service would also have to translate a SQLite error into `overlap` or
     `daily_limit` in the right R9 order. A trigger is also SQL-in-schema that is easy
     to miss in review.
4. **One `INSERT ... SELECT ... WHERE NOT EXISTS (overlap)` statement.**
   - Advantage: a single statement is atomic, so no explicit transaction is needed.
   - Cost: it can only answer "inserted or not", so it cannot say *which* rule failed.
     That breaks the distinction between `overlap` and `daily_limit`, and R11's count
     makes the statement hard to read.
5. **Do nothing.**
   - Advantage: no work.
   - Cost: R7 and R11 are silently broken under concurrent use.

## Decision

Option 1. `Repository.write_transaction()` opens one connection, issues
`BEGIN IMMEDIATE`, and yields a `BookingWrite` with `has_overlap`, `names_on_date` and
`insert_booking` on that connection. It commits on success and rolls back on any
exception. `BookingService.create_booking` runs R7, R11 and the insert inside it.

R3 to R6 need no database state that can change under them, so they stay outside the
lock. The main reason for this choice: it is the only option that is correct across
processes and still lets the service report the right error code in the R9 order. The
cost, serialized writes, does not matter for one library's study rooms. Commit 456c61a
made the change as its own task: 209 tests passed, the layer check passed, and the race
script saved more than one overlapping booking in 0 of 30 trials.

## Consequences

- Easier: R7 and R11 now hold under concurrent requests and with more than one worker.
  Any future rule that has to "check, then write" can use the same `write_transaction`.
- Harder: every booking insert holds the database-wide write lock briefly, so write
  throughput is limited to one booking at a time. A long-running request inside the
  transaction would block all other bookings.
- To watch:
  - keep slow work (network calls, anything that can block) out of
    `write_transaction`;
  - any new code path that writes bookings must go through it;
  - if load ever grows, watch for `database is locked` errors, because they mean the
    10 s busy timeout was reached;
  - `DELETE` does not need the lock, because removing a booking cannot break R7 or
    R11.
