"""R6. Room."""

import pytest

DATE = "2031-03-14"


def body(**kw):
    b = {"room_id": 1, "date": DATE, "start": "09:00", "end": "10:00", "booked_by": "Ana"}
    b.update(kw)
    return b


def bookings(client, date=DATE):
    r = client.get("/api/bookings", params={"date": date})
    assert r.status_code == 200
    return r.json()


def assert_error(r, status, code):
    assert r.status_code == status
    data = r.json()
    assert set(data.keys()) == {"error", "message"}
    assert data["error"] == code


@pytest.mark.parametrize("room_id", [1, 2, 3, 4])
def test_r6_each_of_the_four_rooms_can_be_booked(client, room_id):
    r = client.post("/api/bookings", json=body(room_id=room_id))
    assert r.status_code == 201
    assert r.json()["room_id"] == room_id
    assert [b["room_id"] for b in bookings(client)] == [room_id]


@pytest.mark.parametrize("room_id", [0, 5, -1, 999999])
def test_r6_unknown_room_is_room_not_found(client, room_id):
    before = bookings(client)
    r = client.post("/api/bookings", json=body(room_id=room_id))
    assert_error(r, 404, "room_not_found")
    assert bookings(client) == before
