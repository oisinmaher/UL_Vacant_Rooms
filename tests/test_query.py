"""Tests for the pure data logic in scrape_info (no Qt / selenium needed)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from scrape_info import DAYS, TIMES, ScrapeInfo

BUILDING = "Computer Science Building"


@pytest.fixture(scope="module")
def info():
    return ScrapeInfo()


def test_query_structure(info):
    result = info.query(BUILDING, "Monday", "09:00")
    assert result["day"] == "Monday"
    assert result["building"] == BUILDING
    assert result["times"] == ["09:00", "10:00", "11:00"]
    assert len(result["slots"]) == 3
    for rooms in result["slots"]:
        assert isinstance(rooms, list)
        assert rooms == sorted(rooms)


def test_query_last_day_clamps_to_available_hours(info):
    result = info.query(BUILDING, "Friday", "17:00")
    assert result["times"] == ["17:00"]
    assert len(result["slots"]) == 1


def test_always_free_is_intersection(info):
    for day in DAYS:
        for time in TIMES:
            result = info.query(BUILDING, day, time)
            expected = sorted(
                set.intersection(*(set(slot) for slot in result["slots"]))
                if result["slots"] else set()
            )
            assert result["always_free"] == expected
            for slot in result["slots"]:
                assert set(result["always_free"]) <= set(slot)


def test_run_text_roundtrip(info):
    text = info.run(BUILDING, "Monday", "10:00")
    assert "Monday 10:00–12:00" in text
    assert "10:00:" in text and "11:00:" in text and "12:00:" in text
    assert "hours" in text.lower()
