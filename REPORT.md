# Assignment 5 report

Name: Kundan Singh
Agent tool and version (Claude Code or Antigravity CLI): Claude Code. The work was done in
a Claude agent session built on Claude Code 2.1.330, with the model Claude Opus 5.5
(claude-opus-5-5), on 2026-11-21. The permission-refusal evidence still has to be
captured in local Claude Code (see `evidence/permission-denied.md`).

Answer each question in two to five sentences, below the question, unless it asks for a
table. Point to commits, files, tests or rule IDs where you can.

## 1. Clarify (Part 3)

How many questions did the agent list? Which one, if guessed wrong, would have changed
the backend's behavior the most, and what did you decide?

The agent listed 20 questions (`prompts/03-clarify.txt`). Nine were already answered by
the spec, and eleven became decisions D1 to D11 (commit 4a35f42). The one with the most
effect is Q1/D1: whether `room_id` may arrive as `true`, `1.0` or `"1"`. FastAPI and
pydantic in lax mode quietly convert all three to an integer, so a guessed answer would
have accepted requests that R3 says are the wrong type. D1 makes the model strict, so
all three give `422 invalid_request`. The `daily_limit` code that the page already
handled was not decided: it went under "Proposed, not built".

## 2. Tests before the lock (Part 4)

Name one weak test you found before the lock and how you fixed it. Did any locked test
turn out to be wrong later? If so, which test, which rule, and why.

`test_r9_failed_posts_leave_all_existing_bookings_unchanged` accepted any of
404/409/422 for four bad requests, so a backend sending the wrong code would still
pass. Before the lock I changed it to check each exact error code (`invalid_name`,
`invalid_time`, `room_not_found`, `overlap`). I also found four tests
(`test_r2_ordered_by_room_id_then_start`, `test_r2_room_id_filter_returns_only_that_room`,
`test_r7_filling_gap_between_two_bookings_allowed`,
`test_r8_delete_removes_only_that_booking`) that made 3 to 5 bookings for "Ana" on one
day. Nothing in R2, R7 or R8 needs the same name, and the page's `daily_limit` message
hinted that a per-person limit could come later, so I gave each booking its own name.
Because of that, no locked test turned out wrong. All 200 still pass after R11
(970c9b1) and after the ADR change (456c61a).

## 3. The plan (Part 5)

What did you reject from the plan, or add to "Not in this change", and why?

The planning agent's draft made the R7 check and the insert one `BEGIN IMMEDIATE`
transaction inside Task 1. I rejected that for the build. It is a real design choice
with a cost (writes are serialized), and the handout leaves it to ADR 0001. So the plan
used a plain `has_overlap` plus `insert_booking`, and "Not in this change" says the
concurrency control is deferred (commit 4266827). I also made sure "Not in this change"
names:
- `daily_limit`, which is only proposed, even though the page has a message for it;
- no capacity check (P2), no past-date check (P1), no login (P3);
- no new endpoints or error codes, and no ORM or new package.

## 4. Review findings (Part 7)

One row for every finding in `evidence/review.md` and `evidence/contract-check.md`.

| # | Agent | Finding, in a few words | Fixed (commit SHA) or rejected (reason) |
|---|---|---|---|
| 1 | reviewer | `list_bookings` builds SQL with an f-string and `+=` (AGENTS.md: no SQL string building) | Fixed, 430c442: two fixed SQL strings |
| 2 | reviewer | deeply nested JSON raises `RecursionError`, giving a 500 without the R9 body | Fixed, e5da8e8: reproduced (100000 `[`) before the fix; now `422 invalid_request` |
| 3 | reviewer | overlap check and insert are separate transactions, so two requests can race | Rejected for Part 7, because no spec rule covers concurrency; recorded and fixed under ADR 0001 (456c61a) |
| 4 | reviewer | async POST calls blocking sqlite on the event loop | Rejected: moving it to the threadpool would make finding 3's race reachable within one process; one local sqlite call is fast, and "L2" is the wrong rule ID (L2 is about imports) |
| 5 | contract-checker | rows 1–15 and 17–19: every request, status, error body, error code and 204 handling match | No action: all "Match" |
| 6 | contract-checker | row 16: `daily_limit` in the page but not in the spec | Rejected for Part 7: not in the spec. Built later only after the spec added R11 (2d278f5, then 970c9b1) |
| 7 | contract-checker | rows 5–7 note: response field names "not verified" because they are built in service.py | Rejected: already covered by locked tests `test_r1_lists_exactly_the_four_rooms_in_id_order` and `test_r3_valid_booking_returns_201_with_six_fields`, which check the exact fields |

## 5. The spec change (Part 8)

Did the contract checker, or any earlier step, notice that the page already handles an
error code the spec did not define? Why does a change go spec, then test, then code, in
three commits?

Yes, three times:
- the clarify step listed it as Q17 and put it under "Proposed, not built";
- the planning step kept it in "Not in this change";
- the contract-checker flagged `daily_limit` as "not in the spec" (row 16).

Nothing sent it until the spec had R11. The order spec (2d278f5), test (8a6169c), code
(970c9b1) means the rule is agreed and written down before anyone builds it. The test is
then written from the spec, not from the code, and is seen to fail for the right reason
first: three tests failed with `201 == 409`. The code is then judged against that
test. Separate commits let a reviewer, and the grader, check that order in the history.

## 6. Where the lock stops (Part 4)

Name one way an agent could still change a locked test despite your deny rule, and what
in this assignment would catch it.

The deny rule `Edit(/tests/acceptance/**)` only stops Claude Code's file-edit tools. An
agent allowed to run shell commands could still change a test with
`sed -i`, `python -c "open(...).write(...)"` or `git checkout <old> -- tests/acceptance`
through Bash. It could also make a test pointless without touching it, for example by
editing `tests/conftest.py`. The grader catches this by comparing every file that was in
`tests/acceptance/` at the tag `a5-tests-locked` with the submitted commit, and
`tools/check.py` prints "locked test files unchanged since the lock". It also uses its
own copies of `conftest.py`, `tools/` and `pytest.ini`.

## 7. Legacy parser (Part 10)

Which odd behaviors did you pin? Did the agent's first refactor change any behavior, and
how did you find out? Before fixing one of these bugs for real, what would you check?

`tests/legacy/test_old_format.py` (e33a472) pins 12 wrong results:
- "12:30 PM" → "24:30" and "12:00 AM" → "12:00";
- a lowercase "pm" is ignored;
- minutes are not padded ("9:5 AM" → "09:5");
- "9:00AM" is kept as "09:00AM", and "13:00 PM" → "25:00";
- one- and three-digit years are kept;
- day and month are never checked;

It also pins the exact exceptions: KeyError, IndexError, ValueError and AttributeError.
Before relying on them, I ran the 36 tests against 17 one-change copies of the original,
and all 17 were caught. The refactor (01409bc) passed every test the first time. While
writing it, I avoided an "obvious" cleanup, `hour, minutes = clock`. That would have
turned the `IndexError` for "9" into a `ValueError`, and
`test_legacy_to_24h_no_colon_raises_index_error` would have caught it. I also ran a
differential fuzz of the original against the refactor: 144,800 inputs, 0 differences.
Before fixing a bug for real, for example 12 PM, I would check:
- how the old system actually exported noon and midnight (real export rows);
- whether any rows already imported depend on the old output;
- how the new backend's R3/R5 would treat the corrected times.

Then I would change the pinned test on purpose, in the same commit as the fix.

## 8. The agent team

What did giving each agent one job and its own tools buy you? Name one thing that went
wrong with an agent and how you caught it.

Each agent had one job and only the tools for it:
- The test-writer worked only from the spec, so its 200 tests were written with no code
  to copy from. That makes them an independent check on the build, not a copy of it.
- The reviewer and the contract-checker had only Read, Grep and Glob, so they could
  only report. When the reviewer was wrong (finding 4's suggestion would have widened
  the race), the mistake stayed a report that I rejected, not a change I had to find
  and undo.
- Running the two reviewers side by side gave two independent views: code against
  rules, and page against API.

Things that went wrong:
- The test-writer broke its own limit: it ran one `ls` outside the single command it
  was allowed. It said so itself in its report, and I checked `git status` to confirm
  nothing outside `tests/acceptance/` changed.
- It also wrote four tests that would have broken once R11 arrived. I caught them by
  reading every test against the page before the lock (Q2).
- This cloud session could not load `.claude/agents/` as named agent types, so each
  subagent ran from its agent file's text, and its tool limits were followed by
  instruction, not enforced by the tool. That is recorded in the ledger.

## Screenshot

`evidence/page.png` shows the page with at least one booking made through your backend.

It shows three bookings for today (Ana, Priya, Study group), made through the backend
(Priya was booked from the page itself). After a booking from the page was cancelled,
an overlapping attempt for Ben in Quiet Room A shows the page's overlap message.
