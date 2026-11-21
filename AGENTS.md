# AGENTS.md

## Project

RoomBook, a study-room booking app. The page in `frontend/` is finished and belongs to
another team. The backend in `app/` is built to match `docs/spec.md`.

## General rules

- Read `docs/spec.md` before every change. The spec is the source of truth: when code
  and spec disagree, the spec wins. When the spec is unclear, stop and ask. Do not guess.
- Never edit anything in `frontend/`.
- Never change a test in `tests/acceptance/` to make code pass.
- Do only the task you were given. Do not add endpoints, fields, error codes, rules,
  packages or features that the spec does not ask for.
- Python 3.11 or later. Use only the packages in `requirements.txt`.
- Run the tests with `python -m pytest`.

## Backend rules

- Four layers, each with one job. `app/routes.py` speaks HTTP and nothing else: it
  parses requests, calls the service, and turns results or errors into responses.
  `app/service.py` is where every rule in spec section 5 is enforced. `app/repository.py`
  is the only file that imports `sqlite3` or contains SQL. `app/models.py` holds the
  request shapes. Routes never call the repository directly.
- `app/main.py` defines `create_app(db_path: str = "roombook.db")` exactly as spec
  section 3 says: create tables, seed the four rooms once, serve `frontend/`.
- Every error response, including FastAPI's own validation errors and invalid JSON, has
  exactly the body `{"error": "<code>", "message": "<text>"}` from R9, with a code from
  spec section 6.
- Storage is `sqlite3` from the standard library. No ORM, no new packages.
- Open a fresh connection per repository call (or per request) and close it; never share
  one connection between threads.
- A request that fails must not write anything. Check every rule in the R9 order before
  the first write.
- Use parameterised SQL (`?` placeholders) only; never build SQL with string formatting.
- After every task run `python tools/check_layers.py` and `python -m pytest`, and report
  both results.
