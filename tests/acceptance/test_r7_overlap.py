"""R7. No overlap."""

import pytest

DATE = "2031-03-14"


def body(**kw):
    b = {"room_id": 1, "date": DATE, "start": "10:00", "end": "12:00", "booked_by": "Ana"}
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


@pytest.mark.parametrize(
    "start,end",
    [
        ("10:00", "12:00"),  # identical
        ("09:00", "11:00"),  # overlaps the start
        ("11:00", "13:00"),  # overlaps the end
        ("10:30", "11:30"),  # inside
        ("09:30", "12:30"),  # covers
        ("10:00", "10:30"),  # same start, shorter
        ("11:30", "12:00"),  # same end, shorter
    ],
)
def test_r7_overlapping_booking_same_room_same_date_rejected(client, start, end):
    book(client)
    before = bookings(client)
    r = client.post("/api/bookings", json=body(start=start, end=end, booked_by="Ben"))
    assert_error(r, 409, "overlap")
    assert bookings(client) == before


def test_r7_touching_booking_before_allowed(client):
    first = book(client)
    second = book(client, start="08:30", end="10:00", booked_by="Ben")
    assert [b["id"] for b in bookings(client)] == [second["id"], first["id"]]


def test_r7_touching_booking_after_allowed(client):
    first = book(client)
    second = book(client, start="12:00", end="13:00", booked_by="Ben")
    assert [b["id"] for b in bookings(client)] == [first["id"], second["id"]]


def test_r7_same_person_back_to_back_allowed(client):
    first = book(client, start="10:00", end="12:00")
    second = book(client, start="12:00", end="14:00")
    assert [b["id"] for b in bookings(client)] == [first["id"], second["id"]]


def test_r7_filling_gap_between_two_bookings_allowed(client):
    a = book(client, start="09:00", end="10:00", booked_by="Ana")
    c = book(client, start="11:00", end="12:00", booked_by="Cho")
    b = book(client, start="10:00", end="11:00", booked_by="Ben")
    assert [x["id"] for x in bookings(client)] == [a["id"], b["id"], c["id"]]


def test_r7_same_time_different_room_allowed(client):
    a = book(client, room_id=1)
    b = book(client, room_id=2)
    assert [x["id"] for x in bookings(client)] == [a["id"], b["id"]]


def test_r7_same_time_same_room_different_date_allowed(client):
    a = book(client, date=DATE)
    b = book(client, date="2031-03-15")
    assert [x["id"] for x in bookings(client)] == [a["id"]]
    assert [x["id"] for x in bookings(client, "2031-03-15")] == [b["id"]]


def test_r7_overlap_with_second_of_several_bookings_rejected(client):
    book(client, start="08:00", end="09:00", booked_by="Ana")
    book(client, start="13:00", end="15:00", booked_by="Ben")
    before = bookings(client)
    r = client.post("/api/bookings", json=body(start="14:30", end="16:00", booked_by="Cho"))
    assert_error(r, 409, "overlap")
    assert bookings(client) == before
