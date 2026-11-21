"""R4. Name."""

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


def assert_rejected(client, payload, status=422, code="invalid_name"):
    before = bookings(client)
    r = client.post("/api/bookings", json=payload)
    assert_error(r, status, code)
    assert bookings(client) == before


def test_r4_name_is_trimmed_in_response_and_storage(client):
    r = client.post("/api/bookings", json=body(booked_by="   Ana Lima \t "))
    assert r.status_code == 201
    assert r.json()["booked_by"] == "Ana Lima"
    assert [b["booked_by"] for b in bookings(client)] == ["Ana Lima"]


def test_r4_one_character_name_allowed(client):
    r = client.post("/api/bookings", json=body(booked_by="A"))
    assert r.status_code == 201
    assert r.json()["booked_by"] == "A"


def test_r4_forty_characters_allowed(client):
    name = "a" * 40
    r = client.post("/api/bookings", json=body(booked_by=name))
    assert r.status_code == 201
    assert r.json()["booked_by"] == name


def test_r4_forty_characters_after_trimming_allowed(client):
    name = "b" * 40
    r = client.post("/api/bookings", json=body(booked_by="   " + name + "  "))
    assert r.status_code == 201
    assert r.json()["booked_by"] == name
    assert [b["booked_by"] for b in bookings(client)] == [name]


def test_r4_inner_spaces_count_toward_length(client):
    name = "ab " * 13 + "c"  # 40 characters
    assert len(name) == 40
    r = client.post("/api/bookings", json=body(booked_by=name))
    assert r.status_code == 201
    assert r.json()["booked_by"] == name


def test_r4_forty_one_characters_rejected(client):
    assert_rejected(client, body(booked_by="c" * 41))


def test_r4_forty_one_characters_after_trimming_rejected(client):
    assert_rejected(client, body(booked_by="  " + "d" * 41 + "  "))


def test_r4_empty_name_rejected(client):
    assert_rejected(client, body(booked_by=""))


@pytest.mark.parametrize("name", [" ", "     ", "\t", "\n", " \t\n "])
def test_r4_whitespace_only_name_rejected(client, name):
    assert_rejected(client, body(booked_by=name))
