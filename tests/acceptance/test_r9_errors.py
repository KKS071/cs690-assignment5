"""R9. Errors: body shape, failed requests change nothing, order of checks."""

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
    assert isinstance(data["message"], str)


def assert_rejected(client, payload, status, code):
    before = bookings(client)
    r = client.post("/api/bookings", json=payload)
    assert_error(r, status, code)
    assert bookings(client) == before


# --- error body shape for framework-level failures -------------------------

def test_r9_invalid_json_error_body_has_exactly_error_and_message(client):
    r = client.post("/api/bookings", content=b"{not json",
                    headers={"Content-Type": "application/json"})
    assert_error(r, 422, "invalid_request")
    assert bookings(client) == []


def test_r9_missing_field_error_body_has_exactly_error_and_message(client):
    payload = body()
    del payload["booked_by"]
    assert_rejected(client, payload, 422, "invalid_request")


def test_r9_wrong_type_error_body_has_exactly_error_and_message(client):
    assert_rejected(client, body(room_id="one"), 422, "invalid_request")


def test_r9_missing_query_date_error_body_has_exactly_error_and_message(client):
    assert_error(client.get("/api/bookings"), 422, "invalid_request")


def test_r9_bad_path_id_error_body_has_exactly_error_and_message(client):
    assert_error(client.delete("/api/bookings/abc"), 422, "invalid_request")


# --- a failed request changes nothing (other dates and rooms too) ----------

def test_r9_failed_posts_leave_all_existing_bookings_unchanged(client):
    a = book(client, room_id=1, start="09:00", end="10:00")
    b = book(client, room_id=3, date="2031-03-15", start="14:00", end="16:00")
    for payload, status, code in [
        (body(booked_by=""), 422, "invalid_name"),
        (body(start="07:00"), 422, "invalid_time"),
        (body(room_id=7), 404, "room_not_found"),
        (body(start="09:30", end="10:30", booked_by="Ben"), 409, "overlap"),
    ]:
        assert_error(client.post("/api/bookings", json=payload), status, code)
    assert bookings(client) == [a]
    assert bookings(client, "2031-03-15") == [b]


# --- order of checks: R3, R4, R5, R6, R7 -----------------------------------

@pytest.mark.parametrize(
    "payload",
    [
        body(start="9:00", booked_by=""),         # R3 time format + R4
        body(date="2031-02-30", booked_by="   "),  # R3 impossible date + R4
        body(booked_by=123, start="07:00"),        # R3 wrong type + R5
    ],
)
def test_r9_r3_reported_before_r4_and_r5(client, payload):
    assert_rejected(client, payload, 422, "invalid_request")


def test_r9_r3_reported_before_r6(client):
    assert_rejected(client, body(room_id=9, end="1000"), 422, "invalid_request")


def test_r9_r3_reported_before_r7(client):
    book(client)
    assert_rejected(client, body(booked_by=None), 422, "invalid_request")


def test_r9_r3_missing_field_reported_before_r6(client):
    payload = body(room_id=9)
    del payload["date"]
    assert_rejected(client, payload, 422, "invalid_request")


def test_r9_r4_reported_before_r5(client):
    assert_rejected(client, body(booked_by="", start="07:00", end="11:00"),
                    422, "invalid_name")


def test_r9_r4_reported_before_r6(client):
    assert_rejected(client, body(booked_by="x" * 41, room_id=5), 422, "invalid_name")


def test_r9_r4_reported_before_r7(client):
    book(client)
    assert_rejected(client, body(booked_by="  "), 422, "invalid_name")


def test_r9_r5_reported_before_r6(client):
    assert_rejected(client, body(room_id=0, start="10:00", end="09:00"),
                    422, "invalid_time")


def test_r9_r5_reported_before_r7(client):
    book(client, start="09:00", end="11:00")
    assert_rejected(client, body(start="09:00", end="09:15"), 422, "invalid_time")


def test_r9_r5_duration_reported_before_r7(client):
    book(client, start="09:00", end="10:00")
    assert_rejected(client, body(start="09:00", end="13:00"), 422, "invalid_time")


def test_r9_all_rules_broken_reports_r3(client):
    book(client)
    assert_rejected(
        client,
        body(room_id=9, date="2031-3-14", start="07:15", end="06:00", booked_by=""),
        422, "invalid_request",
    )
