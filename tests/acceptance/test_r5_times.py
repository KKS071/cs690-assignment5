"""R5. Times."""

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


def assert_ok(client, start, end):
    r = client.post("/api/bookings", json=body(start=start, end=end))
    assert r.status_code == 201
    assert (r.json()["start"], r.json()["end"]) == (start, end)
    assert [(b["start"], b["end"]) for b in bookings(client)] == [(start, end)]


def assert_rejected(client, start, end):
    before = bookings(client)
    r = client.post("/api/bookings", json=body(start=start, end=end))
    assert_error(r, 422, "invalid_time")
    assert bookings(client) == before


def test_r5_thirty_minute_booking_allowed(client):
    assert_ok(client, "09:30", "10:00")


def test_r5_exactly_180_minutes_allowed(client):
    assert_ok(client, "09:00", "12:00")


def test_r5_180_minutes_on_half_hours_allowed(client):
    assert_ok(client, "10:30", "13:30")


def test_r5_210_minutes_rejected(client):
    assert_rejected(client, "09:00", "12:30")


def test_r5_much_longer_than_180_minutes_rejected(client):
    assert_rejected(client, "08:00", "22:00")


def test_r5_start_at_0800_allowed(client):
    assert_ok(client, "08:00", "09:00")


def test_r5_end_at_2200_allowed(client):
    assert_ok(client, "19:00", "22:00")


def test_r5_start_at_0730_rejected(client):
    assert_rejected(client, "07:30", "09:00")


def test_r5_end_at_2230_rejected(client):
    assert_rejected(client, "21:00", "22:30")


def test_r5_booking_wholly_before_opening_rejected(client):
    assert_rejected(client, "06:00", "07:00")


def test_r5_booking_wholly_after_closing_rejected(client):
    assert_rejected(client, "22:00", "23:00")


@pytest.mark.parametrize("start,end", [("09:15", "10:00"), ("09:00", "10:45"),
                                       ("09:01", "10:00"), ("09:00", "09:59")])
def test_r5_minutes_not_00_or_30_rejected(client, start, end):
    assert_rejected(client, start, end)


def test_r5_start_equal_to_end_rejected(client):
    assert_rejected(client, "10:00", "10:00")


def test_r5_start_after_end_rejected(client):
    assert_rejected(client, "11:00", "10:00")
