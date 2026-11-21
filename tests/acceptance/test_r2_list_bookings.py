"""R2. List bookings."""

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


def assert_error(r, status, code):
    assert r.status_code == status
    data = r.json()
    assert set(data.keys()) == {"error", "message"}
    assert data["error"] == code


def test_r2_date_with_no_bookings_gives_empty_list(client):
    r = client.get("/api/bookings", params={"date": DATE})
    assert r.status_code == 200
    assert r.json() == []


def test_r2_returns_booking_with_exactly_six_fields(client):
    created = book(client, room_id=2, start="11:00", end="12:30", booked_by="Ben")
    r = client.get("/api/bookings", params={"date": DATE})
    assert r.status_code == 200
    assert r.json() == [
        {"id": created["id"], "room_id": 2, "date": DATE, "start": "11:00",
         "end": "12:30", "booked_by": "Ben"}
    ]


def test_r2_ordered_by_room_id_then_start(client):
    a = book(client, room_id=3, start="08:00", end="09:00", booked_by="Ana")
    b = book(client, room_id=1, start="14:00", end="15:00", booked_by="Ben")
    c = book(client, room_id=1, start="09:00", end="10:00", booked_by="Cho")
    d = book(client, room_id=2, start="12:00", end="13:00", booked_by="Dev")
    e = book(client, room_id=1, start="10:00", end="11:00", booked_by="Eli")
    r = client.get("/api/bookings", params={"date": DATE})
    assert r.status_code == 200
    assert [x["id"] for x in r.json()] == [c["id"], e["id"], b["id"], d["id"], a["id"]]


def test_r2_only_bookings_on_the_given_date(client):
    on = book(client, date=DATE)
    book(client, date="2031-03-15")
    book(client, date="2031-03-13")
    r = client.get("/api/bookings", params={"date": DATE})
    assert r.status_code == 200
    assert [x["id"] for x in r.json()] == [on["id"]]


def test_r2_room_id_filter_returns_only_that_room(client):
    book(client, room_id=1, start="09:00", end="10:00", booked_by="Ana")
    b1 = book(client, room_id=2, start="09:00", end="10:00", booked_by="Ben")
    b2 = book(client, room_id=2, start="13:00", end="14:00", booked_by="Cho")
    book(client, room_id=3, start="09:00", end="10:00", booked_by="Dev")
    book(client, room_id=2, date="2031-03-15", booked_by="Eli")
    r = client.get("/api/bookings", params={"date": DATE, "room_id": "2"})
    assert r.status_code == 200
    assert [x["id"] for x in r.json()] == [b1["id"], b2["id"]]


def test_r2_room_id_filter_with_no_bookings_gives_empty_list(client):
    book(client, room_id=1)
    r = client.get("/api/bookings", params={"date": DATE, "room_id": "4"})
    assert r.status_code == 200
    assert r.json() == []


def test_r2_missing_date_is_invalid_request(client):
    r = client.get("/api/bookings")
    assert_error(r, 422, "invalid_request")


def test_r2_missing_date_with_room_id_is_invalid_request(client):
    r = client.get("/api/bookings", params={"room_id": "1"})
    assert_error(r, 422, "invalid_request")


@pytest.mark.parametrize(
    "bad_date",
    ["2031-3-14", "2031-03-4", "31-03-14", "14-03-2031", "20310314",
     "2031/03/14", "2031-03-14T00:00", "abc", "", "2031-03-1a"],
)
def test_r2_badly_formatted_date_is_invalid_request(client, bad_date):
    r = client.get("/api/bookings", params={"date": bad_date})
    assert_error(r, 422, "invalid_request")


@pytest.mark.parametrize("bad_date", ["2031-02-30", "2031-02-29", "2031-13-01",
                                      "2031-00-10", "2031-04-31", "2031-01-00"])
def test_r2_impossible_date_is_invalid_request(client, bad_date):
    r = client.get("/api/bookings", params={"date": bad_date})
    assert_error(r, 422, "invalid_request")


def test_r2_leap_day_in_leap_year_is_a_real_date(client):
    r = client.get("/api/bookings", params={"date": "2032-02-29"})
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.parametrize("bad_room", ["abc", "x1", "one"])
def test_r2_non_integer_room_id_is_invalid_request(client, bad_room):
    r = client.get("/api/bookings", params={"date": DATE, "room_id": bad_room})
    assert_error(r, 422, "invalid_request")


@pytest.mark.parametrize("room", ["0", "5", "999999"])
def test_r2_unknown_room_id_is_room_not_found(client, room):
    r = client.get("/api/bookings", params={"date": DATE, "room_id": room})
    assert_error(r, 404, "room_not_found")
