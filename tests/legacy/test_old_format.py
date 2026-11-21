"""Characterization tests for legacy/old_format.py.

These pin what the code does today, right or wrong. Every expected value was taken
from running the original legacy/old_format.py, not from the spec. A test marked
"# BUG: pinned, not fixed" pins a result that is wrong for the new backend; it must
keep passing until someone decides, on purpose, to fix that bug.
"""

import pytest

from legacy.old_format import ROOMS, parse_old_row, to_24h


def row(**changes):
    base = {"room": "Room A", "day": "3/14/2031", "from": "9:00 AM", "to": "10:30 AM", "who": "ana"}
    base.update(changes)
    return base


# ---------------------------------------------------------------- to_24h: normal cases

def test_legacy_to_24h_morning_is_zero_padded():
    assert to_24h("9:00 AM") == "09:00"


def test_legacy_to_24h_afternoon_adds_12():
    assert to_24h("1:00 PM") == "13:00"
    assert to_24h("11:45 PM") == "23:45"


def test_legacy_to_24h_without_suffix_is_taken_as_is():
    assert to_24h("8:30") == "08:30"
    assert to_24h("0:15") == "00:15"
    assert to_24h("14:00") == "14:00"


def test_legacy_to_24h_strips_outer_whitespace():
    assert to_24h(" 9:00 AM ") == "09:00"


def test_legacy_to_24h_extra_space_before_suffix_drops_suffix():
    # "9:00  PM" splits into ["9:00", "", "PM"]: parts[1] is "", so PM is ignored.
    assert to_24h("9:00  AM") == "09:00"
    assert to_24h("9:00  PM") == "09:00"


def test_legacy_to_24h_ignores_words_after_suffix():
    assert to_24h("9:00 PM extra") == "21:00"


def test_legacy_to_24h_ignores_seconds():
    assert to_24h("9:00:59 AM") == "09:00"


# ---------------------------------------------------------------- to_24h: wrong results

# BUG: pinned, not fixed
def test_legacy_to_24h_noon_pm_becomes_24():
    assert to_24h("12:30 PM") == "24:30"
    assert to_24h("12:00 PM") == "24:00"


# BUG: pinned, not fixed
def test_legacy_to_24h_midnight_am_stays_12():
    assert to_24h("12:00 AM") == "12:00"
    assert to_24h("12:30 AM") == "12:30"


# BUG: pinned, not fixed
def test_legacy_to_24h_lowercase_pm_is_ignored():
    assert to_24h("3:00 pm") == "03:00"
    assert to_24h("3:00 Pm") == "03:00"


# BUG: pinned, not fixed
def test_legacy_to_24h_minutes_are_not_padded():
    assert to_24h("9:5 AM") == "09:5"


# BUG: pinned, not fixed
def test_legacy_to_24h_pm_on_24h_hour_goes_past_23():
    assert to_24h("13:00 PM") == "25:00"


# BUG: pinned, not fixed
def test_legacy_to_24h_suffix_without_space_stays_in_minutes():
    assert to_24h("9:00AM") == "09:00AM"
    assert to_24h("9:00PM") == "09:00PM"


# ---------------------------------------------------------------- to_24h: exceptions

def test_legacy_to_24h_empty_raises_value_error():
    with pytest.raises(ValueError):
        to_24h("")


def test_legacy_to_24h_no_colon_raises_index_error():
    with pytest.raises(IndexError):
        to_24h("9")
    with pytest.raises(IndexError):
        to_24h("9 AM")


def test_legacy_to_24h_non_numeric_hour_raises_value_error():
    with pytest.raises(ValueError):
        to_24h("abc")
    with pytest.raises(ValueError):
        to_24h(":30")


def test_legacy_to_24h_non_string_raises_attribute_error():
    with pytest.raises(AttributeError):
        to_24h(None)


# ---------------------------------------------------------------- parse_old_row: normal cases

def test_legacy_parse_sample_row():
    assert parse_old_row(row()) == {
        "room_id": 1,
        "date": "2031-03-14",
        "start": "09:00",
        "end": "10:30",
        "booked_by": "Ana",
    }


def test_legacy_parse_result_has_exactly_five_keys_in_order():
    assert list(parse_old_row(row())) == ["room_id", "date", "start", "end", "booked_by"]


def test_legacy_parse_maps_every_room():
    assert ROOMS == {"Room A": 1, "Room B": 2, "Room C": 3, "Room D": 4}
    for name, room_id in ROOMS.items():
        assert parse_old_row(row(room=name))["room_id"] == room_id


def test_legacy_parse_strips_room_day_and_name():
    out = parse_old_row(row(room=" Room B ", day=" 3/14/2031 ", who="  bo chen  "))
    assert out["room_id"] == 2
    assert out["date"] == "2031-03-14"
    assert out["booked_by"] == "Bo chen"


def test_legacy_parse_two_digit_year_gets_20_prefix():
    assert parse_old_row(row(day="12/1/31"))["date"] == "2031-12-01"


def test_legacy_parse_pads_month_and_day():
    assert parse_old_row(row(day="3/2/2031"))["date"] == "2031-03-02"
    assert parse_old_row(row(day="03/02/2031"))["date"] == "2031-03-02"


def test_legacy_parse_capitalizes_only_first_letter():
    assert parse_old_row(row(who="bo chen"))["booked_by"] == "Bo chen"
    assert parse_old_row(row(who="ANA"))["booked_by"] == "ANA"
    assert parse_old_row(row(who="éva"))["booked_by"] == "Éva"
    assert parse_old_row(row(who="mcDonald"))["booked_by"] == "McDonald"


def test_legacy_parse_uses_to_24h_for_both_times():
    out = parse_old_row(row(**{"from": "1:00 PM", "to": "2:00 PM"}))
    assert (out["start"], out["end"]) == ("13:00", "14:00")


def test_legacy_parse_ignores_extra_columns_and_extra_date_parts():
    out = parse_old_row(row(day="3/14/2031/9", note="x"))
    assert out["date"] == "2031-03-14"


# ---------------------------------------------------------------- parse_old_row: wrong results

# BUG: pinned, not fixed
def test_legacy_parse_noon_pm_start_becomes_24():
    out = parse_old_row(row(**{"from": "12:30 PM", "to": "2:00 PM"}))
    assert (out["start"], out["end"]) == ("24:30", "14:00")


# BUG: pinned, not fixed
def test_legacy_parse_lowercase_pm_row_is_morning():
    out = parse_old_row(row(**{"from": "3:00 pm", "to": "4:00 pm"}))
    assert (out["start"], out["end"]) == ("03:00", "04:00")


# BUG: pinned, not fixed
def test_legacy_parse_one_and_three_digit_years_are_kept():
    assert parse_old_row(row(day="1/2/5"))["date"] == "5-01-02"
    assert parse_old_row(row(day="3/14/131"))["date"] == "131-03-14"


# BUG: pinned, not fixed
def test_legacy_parse_day_month_order_is_not_checked():
    assert parse_old_row(row(day="14/3/2031"))["date"] == "2031-14-03"


# BUG: pinned, not fixed
def test_legacy_parse_unpadded_minutes_pass_through():
    assert parse_old_row(row(**{"from": "9:5 AM"}))["start"] == "09:5"


# ---------------------------------------------------------------- parse_old_row: exceptions

def test_legacy_parse_unknown_room_raises_key_error():
    with pytest.raises(KeyError):
        parse_old_row(row(room="Room E"))


def test_legacy_parse_missing_column_raises_key_error():
    data = row()
    del data["who"]
    with pytest.raises(KeyError):
        parse_old_row(data)


def test_legacy_parse_empty_name_raises_index_error():
    with pytest.raises(IndexError):
        parse_old_row(row(who=""))
    with pytest.raises(IndexError):
        parse_old_row(row(who="   "))


def test_legacy_parse_day_without_slashes_raises_index_error():
    with pytest.raises(IndexError):
        parse_old_row(row(day="3-14-2031"))
    with pytest.raises(IndexError):
        parse_old_row(row(day="3/14"))


def test_legacy_parse_bad_time_raises_like_to_24h():
    with pytest.raises(IndexError):
        parse_old_row(row(**{"from": "9"}))
    with pytest.raises(ValueError):
        parse_old_row(row(to="noon"))
