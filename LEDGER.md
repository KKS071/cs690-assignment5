# Provenance Ledger

Write one entry per reviewable change, when the work is done, using exactly the schema
in HANDOUT.md. Put the prompts you typed into AI tools in `prompts/` and name the file in
the entry's `prompts` field. When a subagent did the work, name it in the `tool` field.

## Worked example (not graded; leave it here and add your entries under "My entries")

This shows the level of detail expected. The change is not part of this assignment, and
the commit SHA, date and numbers are made up.

```
## Entry 0
artifact:  commit 3f9c2ab, GET /api/health in app/routes.py (example only)
tool:      Claude Code 2.1.x, main agent, Claude Opus model, 2031-03-01
prompts:   asked for a health endpoint that returns {"ok": true}; prompts/00-health.txt
review:    read the diff. The agent also added a "version" field and a new package to
           read it from git; I rejected both because the request did not ask for them,
           and kept only the endpoint.
checks:    python -m pytest: 41 passed. python tools/check_layers.py: passed.
evidence:  request from the operations team, ticket OPS-12
risk:      no test checks the endpoint under load; not needed for this change.
```

## My entries


## Entry 1
artifact:  commit 4a35f42 (Spec clarified), docs/spec.md section 7, D1 to D11 and "Proposed, not built"
tool:      Claude (claude.ai agent session built on Claude Code 2.1.330), main agent, model Claude Opus 5.5 (claude-opus-5-5), 2026-11-21
prompts:   the Part 3 clarify prompt, and the 20 questions it produced; prompts/03-clarify.txt
review:    went through Q1 to Q20 against the spec. Nine were already answered (R3 object rule, R4 trimming, R3/R5 split for "09:15", "24:00", R8 freeing, section 2 fixed rooms, P1, page null/60-char cases), so no decision was written for them. Wrote D1 to D11 for the rest. First draft of D5 rejected "+1" as a room_id; changed it to accept "+1" because the spec only says "an integer" and a decision must not reject what the spec accepts. The daily_limit code in app.js went to "Proposed, not built", not to a decision.
checks:    re-read sections 1 to 6 after the edit: unchanged (git diff shows only section 7). python tools/check.py: decisions counted.
evidence:  spec section 7, D1 to D11; Q17 -> Proposed, not built
risk:      D5 and D11 are judgement calls on wording the spec leaves open; a hidden test that reads "integer" differently (for example rejecting "01") would disagree.

## Entry 2
artifact:  commit a73602a (Acceptance tests locked, tag a5-tests-locked): tests/acceptance/test_r1 to test_r10, and the deny rule Edit(/tests/acceptance/**) in .claude/settings.json
tool:      Claude (claude.ai agent session built on Claude Code 2.1.330), model Claude Opus 5.5 (claude-opus-5-5), 2026-11-21. The tests were written by the test-writer subagent: this session cannot load .claude/agents/ as named types ("Agent type 'test-writer' not found"), so it ran as a general-purpose subagent briefed with the body of .claude/agents/test-writer.md verbatim and told to use only that file's tools
prompts:   the Part 4 prompt, plus the extra notes passed to the subagent; prompts/04-tests.txt
review:    read all ten files line by line against the spec before running anything. Every error test checks the status, the error code, the exact {error, message} keys and that bookings are unchanged; none checks message text; ids come from POST responses. Boundaries are covered: 180/210 minutes, 08:00 and 22:00, 07:30 and 22:30, touching bookings, 40/41 characters after trimming, 2031-02-30, 2032-02-29. Changed four tests by hand (test_r2_ordered_by_room_id_then_start, test_r2_room_id_filter_returns_only_that_room, test_r7_filling_gap_between_two_bookings_allowed, test_r8_delete_removes_only_that_booking): each made 3 to 5 bookings for "Ana" on one date. Nothing in R2/R7/R8 needs the same person, and the page's daily_limit message shows that a per-person limit could come later and break a locked test, so I gave each booking a different name. Also tightened test_r9_failed_posts_leave_all_existing_bookings_unchanged, which accepted any of 404/409/422: it now checks each exact error code. Kept the subagent's choice to leave out the D5/D3/D11 judgement calls. The subagent said it ran one ls outside the allowed command; that changed nothing.
checks:    python tools/check.py tests: 200 collected, a test for each of R1 to R10, 0 passed and 200 errored, all with "No module named 'app.main'".
evidence:  R1 to R10; tag a5-tests-locked
risk:      the tests have not run against any backend yet, so a wrong expected value would only show up in Part 6 and could not be fixed then. The lock has not yet been shown to block an edit: evidence/permission-denied.md still has to be captured in local Claude Code.

## Entry 3
artifact:  commit 26be5f1 (Task 1), app/repository.py
tool:      Claude (claude.ai agent session built on Claude Code 2.1.330), main agent, model Claude Opus 5.5 (claude-opus-5-5), 2026-11-21
prompts:   Task 1 of docs/plan.md; prompts/06-task1.txt
review:    read the diff. Every method opens and closes its own connection, all SQL uses ? placeholders, "end" is quoted because END is an SQL keyword, rooms are seeded only when the table is empty, list order is room_id, start, id (D8), and AUTOINCREMENT keeps ids from being reused (D9). The overlap query is start < new_end AND new_start < end, which is R7's "each starts before the other ends". It has no validation, as the plan says. Nothing outside app/repository.py changed.
checks:    smoke run on a temp file: init_db twice leaves 4 rooms; an overlapping booking is found, while a touching one and one in another room are not; delete returns True, then False; the id after a delete is 2, not reused. python tools/check_layers.py: only L4 "missing module" lines for the four files not written yet (expected). python -m pytest tests/acceptance: 6 failed, 194 errors, all from the missing app.main (expected until Task 3).
evidence:  R1, R2, R7, R8, R10, D8, D9; plan Task 1
risk:      the separate has_overlap + insert_booking leaves a race between two requests at the same moment (deferred to ADR 0001); a huge room_id integer would overflow sqlite, so the service must guard it.

## Entry 4
artifact:  commit 394e26d (Task 2), app/models.py and app/service.py
tool:      Claude (claude.ai agent session built on Claude Code 2.1.330), main agent, model Claude Opus 5.5 (claude-opus-5-5), 2026-11-21
prompts:   Task 2 of docs/plan.md; prompts/06-task2.txt
review:    read the diff against R2 to R9. The checks in create_booking run in the R9 order: R3, then R4, R5, R6, R7, and the only write comes after all of them. The pydantic model is strict, so true, 1.0 and "1" are wrong types (D1). The regexes use [0-9] and fullmatch, so a trailing newline or non-ASCII digits are rejected (D2). The date also goes through datetime.date (D10). R5 has five conditions, one for each bullet in the spec plus both ends; the length is "> 180" so exactly 180 minutes is allowed. R6 checks against the room ids in Python, so a 10**30 room_id never reaches sqlite. In R2 both format checks come before the room lookup (D6). The message text is free-form, which the spec allows. Neither file has any HTTP or SQL.
checks:    smoke run through BookingService on a temp file, one payload per rule plus R9 pairs: true/"1"/1.0 -> invalid_request; ""+07:00 -> invalid_name; 07:00+room 9 -> invalid_time; room 9 -> room_not_found; overlap -> overlap; 180 min OK, 210 min -> invalid_time; huge ids -> 404 codes, no crash. python tools/check_layers.py: only L4 for main.py and routes.py (expected). python -m pytest tests/acceptance: 6 failed, 194 errors, still no app.main (expected).
evidence:  R2 to R9, D1, D2, D4, D5, D6, D10; plan Task 2
risk:      the HTTP layer is not written yet, so invalid JSON and the framework's own 422s are untested until Task 3.

## Entry 5
artifact:  commit 9e9f799 (Task 3), app/routes.py and app/main.py; then evidence/page.png
tool:      Claude (claude.ai agent session built on Claude Code 2.1.330), main agent, model Claude Opus 5.5 (claude-opus-5-5), 2026-11-21; screenshot by a Playwright script driving headless Chrome against the real uvicorn server
prompts:   Task 3 of docs/plan.md; prompts/06-task3.txt
review:    read the diff. Routes read the query, the body and the path id as raw strings, so FastAPI's own validation never produces a non-R9 body. Invalid JSON, including an empty body, gives 422 invalid_request. routes.py imports the service, not the repository (L3). The one error_response helper is reused by main.py's RequestValidationError safety net. The status map matches section 6. create_app builds a fresh repository per db_path and serves the three frontend files. A path outside section 4 (/api/nope) keeps FastAPI's default {"detail": ...} body, as D11 says.
checks:    python tools/check_layers.py: passed, L1 to L5. python -m pytest tests/acceptance: 200 passed, with no test edited. With uvicorn on port 8000 and curl: an empty body gives 422 invalid_request; a text/plain body is still parsed (D3); an overlap gives 409; delete gives 204. In the browser (headless Chrome, page untouched): booked Priya in room B, booked and then cancelled "Temp booking" ("Booking cancelled."), and an overlapping booking for Ben showed the page's overlap message, which is in the screenshot.
evidence:  R1 to R10, D3, D11; plan Task 3; evidence/page.png
risk:      two requests at the same moment can both pass has_overlap (ADR 0001). The screenshot is headless Chrome on Linux, not a desktop browser.

## Entry 6
artifact:  commit fd808f8 (evidence/review.md, evidence/contract-check.md); fixes 430c442 (review finding 1) and e5da8e8 (review finding 2)
tool:      Claude (claude.ai agent session built on Claude Code 2.1.330), model Claude Opus 5.5 (claude-opus-5-5), 2026-11-21. The reviewer subagent and the contract-checker subagent ran at the same time as read-only subagents briefed with their agent files; the fixes were made by the main agent
prompts:   the Part 7 prompt, the subagent task lines, and the "fix finding n" prompts; prompts/07-reviews.txt
review:    read both reports and checked each finding against the code and the spec. Review 1: accepted. AGENTS.md bans building SQL with string formatting, and list_bookings used an f-string plus +=; now two fixed SQL strings. Review 2: accepted after reproducing it. A body of 100000 nested "[" gave a 500 with no R9 body; now 422 invalid_request. Review 3 (race between has_overlap and insert): rejected for now, because no rule in the spec covers concurrency; it is the subject of ADR 0001 in Part 9. Review 4 (async POST blocks the event loop): rejected. Moving the sqlite calls to the threadpool would make finding 3's race reachable within one process, and one local sqlite call per POST is acceptable. The reviewer also tagged it L2, which is wrong: L2 is about imports. Contract check: 19 rows, no mismatches. daily_limit is "not in the spec": rejected for now, already under Proposed, not built. Its "rows 5-7 not verified" note is covered by test_r1_lists_exactly_the_four_rooms_in_id_order and test_r3_valid_booking_returns_201_with_six_fields, which check the exact fields.
checks:    after each fix: python tools/check_layers.py passed; python -m pytest: 200 passed. The nested-JSON request was rerun after fix 2: 422 {"error":"invalid_request",...}.
evidence:  R9, R7, AGENTS.md Backend rules (parameterised SQL); evidence/review.md findings 1-4; evidence/contract-check.md rows 1-19
risk:      no locked test covers deeply nested JSON (the check was by hand); the R7 race stays open until ADR 0001.

## Entry 7
artifact:  commits 2d278f5 (Spec: R11 daily limit), 8a6169c (Test: R11), 970c9b1 (R11: daily limit): docs/spec.md, tests/acceptance/test_r11_daily_limit.py, app/repository.py, app/service.py, app/routes.py
tool:      Claude (claude.ai agent session built on Claude Code 2.1.330), main agent, model Claude Opus 5.5 (claude-opus-5-5), 2026-11-21. The R11 test file was drafted in the chat and placed by hand (the agent may not write in tests/acceptance/)
prompts:   the spec text was copied from the handout; the test draft request and the Part 8 code prompt are in prompts/08-r11.txt
review:    spec: checked that the diff only adds R11, the section 6 row, R11 at the end of the R9 order, "R1 to R11" and the Version 2 log line, plus a note that the daily_limit proposal is now built. Test: checked each expected value against R11. A third booking gives 409 daily_limit with nothing saved. Bookings in all rooms count. "Ana Lima", "  ana lima " and "ANA LIMA\t" are one person. Other people and other dates are not limited. A cancel frees a place. R7, R6 and R5 come before R11 (the R9 order). Before the code it failed 3, passed 6; the three failures were "assert 201 == 409", the right reason. The six that passed check behaviour that must still hold, not the new limit. Code: names_on_date is the only new SQL and lives in the repository; the rule itself (strip + lower, count >= 2) lives in the service; the check runs after R7, so overlap still wins; routes only gained the 409 mapping. Nothing else changed.
checks:    python tools/check_layers.py: passed. python -m pytest: 209 passed (200 locked + 9 R11). In headless Chrome on the real server: "Sam", "sam " and "SAM" on one day; the third got the page's own message "You already have 2 bookings on that day. Cancel one to book another."
evidence:  R11, R9 order; tests test_r11_*
risk:      "ignoring case" is done with str.lower(), so some Unicode case pairs (for example "ß" and "SS") are not treated as the same person. The R11 count, like R7, is a separate read before the insert and shares the race described in ADR 0001.

## Entry 8
artifact:  commits 456c61a (ADR 0001 change: write transaction) and de14eb7 (ADR 0001), app/repository.py, app/service.py, docs/adr/0001-serialize-booking-writes.md, evidence/race_check.py
tool:      Claude (claude.ai agent session built on Claude Code 2.1.330), main agent, model Claude Opus 5.5 (claude-opus-5-5), 2026-11-21
prompts:   the Part 9 question, the summary of the answer, and the follow-up task prompt; prompts/09-adr.txt
review:    did not take the race on faith: wrote evidence/race_check.py (8 threads, 30 trials) and saw 28/30 trials save overlapping bookings before the change. Weighed five options (BEGIN IMMEDIATE, threading.Lock, trigger, INSERT...WHERE NOT EXISTS, nothing). Rejected threading.Lock because it does not cover two processes, and the trigger and the single statement because they cannot report overlap and daily_limit separately in the R9 order. Read the diff. write_transaction commits only after the with block ends and rolls back on BookingError. The SQL stayed in repository.py (BookingWrite) and the rules stayed in service.py; the old separate-connection has_overlap and names_on_date were removed so nothing can bypass the lock. R3 to R6 stay outside the lock, because they read nothing that can change.
checks:    python tools/check_layers.py: passed. python -m pytest: 209 passed. python evidence/race_check.py .: 0/30 trials with an overlap, down from 28/30.
evidence:  R7, R11, R9 order; ADR 0001
risk:      the race script is timing-based, so 0/30 is strong evidence but not proof. Behaviour when the 10 s busy timeout runs out (a database is locked error, which would give a 500) is not handled or tested.
