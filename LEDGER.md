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
