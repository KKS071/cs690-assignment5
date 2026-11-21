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
