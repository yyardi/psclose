import pytest

from psclose import periods


def test_period_bounds():
    assert periods.period_start("2026-07") == "2026-07-01"
    assert periods.period_end("2026-07") == "2026-07-31"
    assert periods.period_end("2026-02") == "2026-02-28"
    assert periods.period_end("2028-02") == "2028-02-29"


def test_neighbours_and_ranges():
    assert periods.next_period("2026-12") == "2027-01"
    assert periods.prev_period("2026-01") == "2025-12"
    assert periods.period_range("2026-05", "2026-08") == ["2026-05", "2026-06", "2026-07", "2026-08"]
    assert periods.period_range("2026-08", "2026-05") == []
    assert periods.period_of("2026-07-14") == "2026-07"
    assert periods.label("2026-07") == "July 2026"


def test_rejects_garbage():
    with pytest.raises(ValueError):
        periods.period_end("2026-13")
    with pytest.raises(ValueError):
        periods.period_end("July")
