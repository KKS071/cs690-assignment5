"""R3. Request shape of POST /api/bookings."""

import pytest

DATE = "2031-03-14"
FIELDS = ["room_id", "date", "start", "end", "booked_by"]


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


def assert_rejected(client, payload, status=422, code="invalid_request"):
    before = bookings(client)
    r = client.post("/api/bookings", json=payload)
    assert_error(r, status, code)
    assert bookings(client) == before


def test_r3_valid_booking_returns_201_with_six_fields(client):
    r = client.post("/api/bookings", json=body(room_id=2, start="09:00", end="10:30"))
    assert r.status_code == 201
    data = r.json()
    assert set(data.keys()) == {"id", "room_id", "date", "start", "end", "booked_by"}
    assert isinstance(data["id"], int) and not isinstance(data["id"], bool)
    assert {k: data[k] for k in FIELDS} == body(room_id=2, start="09:00", end="10:30")
    assert bookings(client) == [data]


def test_r3_unknown_fields_are_ignored(client):
    r = client.post("/api/bookings", json=body(extra="x", people=4, id=12345))
    assert r.status_code == 201
    data = r.json()
    assert set(data.keys()) == {"id", "room_id", "date", "start", "end", "booked_by"}
    assert {k: data[k] for k in FIELDS} == body()
    assert bookings(client) == [data]


def test_r3_invalid_json_is_invalid_request(client):
    before = bookings(client)
    r = client.post("/api/bookings", content=b"{not json",
                    headers={"Content-Type": "application/json"})
    assert_error(r, 422, "invalid_request")
    assert bookings(client) == before


@pytest.mark.parametrize("payload", [[], [body()], "text", 5])
def test_r3_body_not_an_object_is_invalid_request(client, payload):
    assert_rejected(client, payload)


@pytest.mark.parametrize("field", FIELDS)
def test_r3_missing_field_is_invalid_request(client, field):
    payload = body()
    del payload[field]
    assert_rejected(client, payload)


@pytest.mark.parametrize("value", ["1", True, False, None, 1.5, [1], {"id": 1}])
def test_r3_room_id_wrong_type_is_invalid_request(client, value):
    assert_rejected(client, body(room_id=value))


@pytest.mark.parametrize("field", ["date", "start", "end", "booked_by"])
@pytest.mark.parametrize("value", [123, None, True, ["x"], {"a": 1}])
def test_r3_string_field_wrong_type_is_invalid_request(client, field, value):
    assert_rejected(client, body(**{field: value}))


@pytest.mark.parametrize(
    "bad_date",
    ["2031-3-14", "2031-03-4", "31-03-14", "14-03-2031", "20310314",
     "2031/03/14", "", "abcd-ef-gh"],
)
def test_r3_badly_formatted_date_is_invalid_request(client, bad_date):
    assert_rejected(client, body(date=bad_date))


@pytest.mark.parametrize("bad_date", ["2031-02-30", "2031-02-29", "2031-13-01",
                                      "2031-00-10", "2031-04-31"])
def test_r3_impossible_date_is_invalid_request(client, bad_date):
    assert_rejected(client, body(date=bad_date))


def test_r3_leap_day_in_leap_year_is_accepted(client):
    r = client.post("/api/bookings", json=body(date="2032-02-29"))
    assert r.status_code == 201
    assert r.json()["date"] == "2032-02-29"


@pytest.mark.parametrize("field", ["start", "end"])
@pytest.mark.parametrize(
    "bad_time",
    ["9:00", "09:0", "0900", "09.00", "09-00", "", "ab:cd", "09:00:00",
     "24:00", "25:00", "09:60", "099:00"],
)
def test_r3_badly_formatted_time_is_invalid_request(client, field, bad_time):
    assert_rejected(client, body(**{field: bad_time}))
