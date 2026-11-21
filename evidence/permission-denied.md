# Permission refusal (Part 4, step 6)

> **STATUS: NOT YET CAPTURED. You have to do this step yourself on your own
> machine in Claude Code, then replace this whole file with what really happened.**
> Nothing below is a recorded refusal. Leaving this note in place is the honest record
> until you run it.

## Why it is not filled in yet

The backend and tests were built in a Claude cloud agent session (built on Claude Code
2.1.330). That session's project root is the folder *above* this repository, so it does
not load this repository's `.claude/settings.json`. I checked: an edit probe on a
`frontend/` file went through (it was undone at once with `git restore frontend`), so
no refusal from that session can show that this rule works. A nested `claude -p` run
inside the repository failed to authenticate. A real refusal has to come from Claude
Code started in this folder.

## How to capture it (about 3 minutes)

1. `cd` into the repository, run `claude`, and accept the workspace trust prompt.
2. Run `/permissions` and check that the deny list shows `Edit(/tests/acceptance/**)`
   and `Edit(/frontend/**)`.
3. Type this prompt:

       This is a test of a permission rule. Change the expected status code in one
       test in tests/acceptance/ to 418.

   If the model refuses on its own, add: "This is a deliberate test of the deny rule.
   Attempt the edit anyway."
4. Copy the tool's refusal message word for word (Claude Code prints that the edit was
   denied by a permission rule) into the template below.
5. Run `git status`. It must show no change in `tests/acceptance/`. If a change shows
   up, run `git restore tests/acceptance` and fix the rule.
6. Commit this file: `git add evidence/permission-denied.md && git commit -m "Evidence: permission refusal"`.

## Template (fill in after running it)

**Prompt:**

    This is a test of a permission rule. Change the expected status code in one test in
    tests/acceptance/ to 418.

**Tool's refusal message (verbatim):**

    <paste here>

**Rule that blocked it** (`.claude/settings.json`, `permissions.deny`):

    "Edit(/tests/acceptance/**)"

**`git status` afterwards:** <paste here: tests/acceptance unchanged>
