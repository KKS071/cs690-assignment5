"""R8. Cancel."""

import pytest

DATE = "2031-03-14"


def body(**kw):
    b = {"room_id": 1, "date": DATE, "start": "09:00", "end": "10:00", "booked_by": "Ana"}
    b.update(kw)
    return b


def book(client, **kw):
    r = client.post("/api/bookings", json=body(**kw))
    assert r.status_code == 201, r.text
    return r.json()


def bookings(client, date=DATE):
    r = client.get("/api/bookings", params={"date": date})
    assert r.status_code == 200
    return r.json()


def assert_error(r, status, code):
    assert r.status_code == status
    data = r.json()
    assert set(data.keys()) == {"error", "message"}
    assert data["error"] == code


def test_r8_delete_returns_204_with_empty_body(client):
    b = book(client)
    r = client.delete(f"/api/bookings/{b['id']}")
    assert r.status_code == 204
    assert r.content == b""


def test_r8_deleted_booking_is_gone_from_list(client):
    b = book(client)
    assert client.delete(f"/api/bookings/{b['id']}").status_code == 204
    assert bookings(client) == []


def test_r8_delete_removes_only_that_booking(client):
    a = book(client, start="09:00", end="10:00", booked_by="Ana")
    b = book(client, start="10:00", end="11:00", booked_by="Ben")
    c = book(client, room_id=2, booked_by="Cho")
    assert client.delete(f"/api/bookings/{b['id']}").status_code == 204
    assert bookings(client) == [a, c]


def test_r8_time_is_free_to_book_again(client):
    b = book(client, start="09:00", end="11:00")
    assert client.delete(f"/api/bookings/{b['id']}").status_code == 204
    again = book(client, start="09:00", end="11:00", booked_by="Ben")
    assert bookings(client) == [again]


def test_r8_deleting_twice_gives_booking_not_found(client):
    gone = book(client, start="09:00", end="10:00")
    keep = book(client, start="12:00", end="13:00")
    assert client.delete(f"/api/bookings/{gone['id']}").status_code == 204
    before = bookings(client)
    assert before == [keep]
    r = client.delete(f"/api/bookings/{gone['id']}")
    assert_error(r, 404, "booking_not_found")
    assert bookings(client) == before


def test_r8_unknown_large_id_gives_booking_not_found(client):
    book(client)
    before = bookings(client)
    r = client.delete("/api/bookings/999999")
    assert_error(r, 404, "booking_not_found")
    assert bookings(client) == before


@pytest.mark.parametrize("bad_id", ["abc", "1.5", "one", "1x"])
def test_r8_non_integer_id_gives_invalid_request(client, bad_id):
    book(client)
    before = bookings(client)
    r = client.delete(f"/api/bookings/{bad_id}")
    assert_error(r, 422, "invalid_request")
    assert bookings(client) == before
