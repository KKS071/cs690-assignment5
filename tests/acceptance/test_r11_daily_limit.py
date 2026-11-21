"""R11. Daily limit (spec version 2).

Added after the lock, by hand (the agent may not write in tests/acceptance/). Every
expected value comes from the text of R11 and the R9 order R3, R4, R5, R6, R7, R11.
"""

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


def assert_rejected(client, payload, status, code):
    before = bookings(client)
    r = client.post("/api/bookings", json=payload)
    assert_error(r, status, code)
    assert bookings(client) == before


def test_r11_two_bookings_on_one_date_allowed(client):
    a = book(client, room_id=1, start="09:00", end="10:00")
    b = book(client, room_id=2, start="11:00", end="12:00")
    assert bookings(client) == [a, b]


def test_r11_third_booking_on_one_date_rejected_and_not_saved(client):
    book(client, room_id=1, start="09:00", end="10:00")
    book(client, room_id=1, start="10:00", end="11:00")
    assert_rejected(client, body(room_id=1, start="13:00", end="14:00"), 409, "daily_limit")


def test_r11_limit_counts_across_all_rooms(client):
    book(client, room_id=1)
    book(client, room_id=2)
    assert_rejected(client, body(room_id=3), 409, "daily_limit")


def test_r11_same_name_with_other_case_and_spaces_is_same_person(client):
    book(client, room_id=1, booked_by="Ana Lima")
    book(client, room_id=2, booked_by="  ana lima ")
    assert_rejected(client, body(room_id=3, booked_by="ANA LIMA\t"), 409, "daily_limit")


def test_r11_other_people_are_not_limited(client):
    book(client, room_id=1, booked_by="Ana")
    book(client, room_id=2, booked_by="Ana")
    c = book(client, room_id=3, booked_by="Ben")
    assert c in bookings(client)


def test_r11_other_dates_are_not_counted(client):
    book(client, room_id=1)
    book(client, room_id=2)
    other = book(client, room_id=3, date="2031-03-15")
    assert bookings(client, "2031-03-15") == [other]


def test_r11_cancelling_one_of_two_allows_a_new_one(client):
    first = book(client, room_id=1, start="09:00", end="10:00")
    book(client, room_id=2, start="09:00", end="10:00")
    assert client.delete(f"/api/bookings/{first['id']}").status_code == 204
    again = book(client, room_id=3, start="15:00", end="16:00")
    assert again in bookings(client)


def test_r11_overlap_is_reported_before_daily_limit(client):
    book(client, room_id=1, start="09:00", end="10:00")
    book(client, room_id=2, start="09:00", end="10:00")
    assert_rejected(client, body(room_id=1, start="09:30", end="10:30"), 409, "overlap")


def test_r11_room_and_time_errors_are_reported_before_daily_limit(client):
    book(client, room_id=1)
    book(client, room_id=2)
    assert_rejected(client, body(room_id=9), 404, "room_not_found")
    assert_rejected(client, body(room_id=3, start="07:00"), 422, "invalid_time")
