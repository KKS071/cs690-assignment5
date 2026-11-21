"""R1. List rooms."""

ROOMS = [
    {"id": 1, "name": "Quiet Room A", "capacity": 2},
    {"id": 2, "name": "Quiet Room B", "capacity": 2},
    {"id": 3, "name": "Group Room C", "capacity": 6},
    {"id": 4, "name": "Group Room D", "capacity": 8},
]


def test_r1_lists_exactly_the_four_rooms_in_id_order(client):
    r = client.get("/api/rooms")
    assert r.status_code == 200
    assert r.json() == ROOMS


def test_r1_rooms_unchanged_after_bookings(client):
    r = client.post(
        "/api/bookings",
        json={"room_id": 3, "date": "2031-03-14", "start": "09:00",
              "end": "10:00", "booked_by": "Ana"},
    )
    assert r.status_code == 201
    r = client.get("/api/rooms")
    assert r.status_code == 200
    assert r.json() == ROOMS
