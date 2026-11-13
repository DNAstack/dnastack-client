import time
from datetime import datetime, timezone

import pytest

from dnastack.common.iso_time import InvalidPointInTimeError, parse_point_in_time

NOW = datetime(2026, 1, 31, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def toronto_timezone(monkeypatch):
    monkeypatch.setenv('TZ', 'America/Toronto')
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


class TestDurations:
    @pytest.mark.parametrize('duration, expected', [
        ('P1D', datetime(2026, 2, 1, 10, 0, 0, tzinfo=timezone.utc)),
        ('P2W', datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)),
        ('PT12H', datetime(2026, 1, 31, 22, 0, 0, tzinfo=timezone.utc)),
        ('PT90M', datetime(2026, 1, 31, 11, 30, 0, tzinfo=timezone.utc)),
        ('PT30S', datetime(2026, 1, 31, 10, 0, 30, tzinfo=timezone.utc)),
        ('P1DT2H', datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)),
        ('p1d', datetime(2026, 2, 1, 10, 0, 0, tzinfo=timezone.utc)),
    ])
    def test_counts_duration_from_now(self, duration, expected):
        assert parse_point_in_time(duration, now=NOW) == expected

    def test_clamps_month_to_its_last_day(self):
        assert parse_point_in_time('P1M', now=NOW) == datetime(2026, 2, 28, 10, 0, 0, tzinfo=timezone.utc)

    def test_adds_years_as_calendar_years(self):
        assert parse_point_in_time('P1Y', now=NOW) == datetime(2027, 1, 31, 10, 0, 0, tzinfo=timezone.utc)

    @pytest.mark.parametrize('duration', ['P', 'PT', 'P1DT', 'P1H', 'PT1D', 'P1.5D', 'PXD'])
    def test_rejects_malformed_duration(self, duration):
        with pytest.raises(InvalidPointInTimeError):
            parse_point_in_time(duration, now=NOW)


class TestDates:
    def test_date_means_end_of_that_day_in_local_timezone(self, toronto_timezone):
        # Midnight starting Nov 2 in Toronto (EST, UTC-5) is 05:00 UTC.
        assert parse_point_in_time('2026-11-01') == datetime(2026, 11, 2, 5, 0, 0, tzinfo=timezone.utc)

    def test_rejects_impossible_date(self):
        with pytest.raises(InvalidPointInTimeError):
            parse_point_in_time('2026-02-30')


class TestDateTimes:
    def test_keeps_given_offset(self):
        assert parse_point_in_time('2026-11-01T17:00:00-04:00') == datetime(2026, 11, 1, 21, 0, 0, tzinfo=timezone.utc)

    def test_accepts_zulu_suffix(self):
        assert parse_point_in_time('2026-11-01T17:00:00Z') == datetime(2026, 11, 1, 17, 0, 0, tzinfo=timezone.utc)

    def test_date_time_without_offset_is_local(self, toronto_timezone):
        # Toronto is on EDT (UTC-4) in mid-October.
        assert parse_point_in_time('2026-10-15T17:00:00') == datetime(2026, 10, 15, 21, 0, 0, tzinfo=timezone.utc)

    def test_rejects_text_that_is_not_a_point_in_time(self):
        with pytest.raises(InvalidPointInTimeError):
            parse_point_in_time('next tuesday')
