"""R10. The application (spec section 3)."""

from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
DATE = "2031-03-14"
ROOMS = [
    {"id": 1, "name": "Quiet Room A", "capacity": 2},
    {"id": 2, "name": "Quiet Room B", "capacity": 2},
    {"id": 3, "name": "Group Room C", "capacity": 6},
    {"id": 4, "name": "Group Room D", "capacity": 8},
]


def body(**kw):
    b = {"room_id": 1, "date": DATE, "start": "09:00", "end": "10:00", "booked_by": "Ana"}
    b.update(kw)
    return b


def bookings(client, date=DATE):
    r = client.get("/api/bookings", params={"date": date})
    assert r.status_code == 200
    return r.json()


def test_r10_serves_index_html_at_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "RoomBook" in r.text
    assert r.content == (FRONTEND / "index.html").read_bytes()


def test_r10_serves_app_js(client):
    r = client.get("/app.js")
    assert r.status_code == 200
    assert r.content == (FRONTEND / "app.js").read_bytes()


def test_r10_serves_styles_css(client):
    r = client.get("/styles.css")
    assert r.status_code == 200
    assert r.content == (FRONTEND / "styles.css").read_bytes()


def test_r10_fresh_database_has_four_rooms_and_no_bookings(new_client):
    c = new_client("fresh.db")
    assert c.get("/api/rooms").json() == ROOMS
    assert bookings(c) == []


def test_r10_different_files_do_not_share_data(new_client):
    a = new_client("a.db")
    b = new_client("b.db")
    r = a.post("/api/bookings", json=body())
    assert r.status_code == 201
    assert bookings(a) == [r.json()]
    assert bookings(b) == []
    r2 = b.post("/api/bookings", json=body(room_id=2, booked_by="Ben"))
    assert r2.status_code == 201
    assert bookings(a) == [r.json()]
    assert bookings(b) == [r2.json()]


def test_r10_same_file_sees_saved_booking_after_restart(new_client):
    first = new_client("a.db")
    r = first.post("/api/bookings", json=body(booked_by="  Ana  "))
    assert r.status_code == 201
    saved = r.json()
    second = new_client("a.db")
    assert bookings(second) == [saved]


def test_r10_rooms_not_duplicated_after_restart(new_client):
    new_client("a.db")
    again = new_client("a.db")
    assert again.get("/api/rooms").json() == ROOMS


def test_r10_saved_booking_still_blocks_overlap_after_restart(new_client):
    first = new_client("a.db")
    assert first.post("/api/bookings", json=body()).status_code == 201
    second = new_client("a.db")
    r = second.post("/api/bookings", json=body(booked_by="Ben"))
    assert r.status_code == 409
    assert r.json()["error"] == "overlap"


def test_r10_cancel_is_kept_after_restart(new_client):
    first = new_client("a.db")
    r = first.post("/api/bookings", json=body())
    assert r.status_code == 201
    assert first.delete(f"/api/bookings/{r.json()['id']}").status_code == 204
    second = new_client("a.db")
    assert bookings(second) == []
