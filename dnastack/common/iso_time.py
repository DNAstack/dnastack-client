import calendar
import re
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

_DURATION_PATTERN = re.compile(
    r'^P'
    r'(?:(?P<years>\d+)Y)?'
    r'(?:(?P<months>\d+)M)?'
    r'(?:(?P<weeks>\d+)W)?'
    r'(?:(?P<days>\d+)D)?'
    r'(?:T'
    r'(?:(?P<hours>\d+)H)?'
    r'(?:(?P<minutes>\d+)M)?'
    r'(?:(?P<seconds>\d+(?:\.\d+)?)S)?'
    r')?$',
    re.IGNORECASE,
)

_DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')


class InvalidPointInTimeError(ValueError):
    """ Raised when a value is neither an ISO 8601 duration, date nor date-time """


def parse_point_in_time(value: str, now: Optional[datetime] = None) -> datetime:
    """
    Resolve an ISO 8601 duration, date or date-time to a timezone-aware point in time.

    - A duration (e.g. ``P30D``, ``PT12H``, ``P1Y2M``) is counted from ``now``.
    - A date without a time (e.g. ``2026-11-01``) means the end of that day in the local timezone, i.e. the
      start of the following day.
    - A date-time without an offset is in the local timezone.

    :param value: the text to resolve
    :param now: the instant a duration is counted from; defaults to the current time
    :return: the resolved point in time, in UTC
    """
    text = value.strip()
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    if text[:1].upper() == 'P':
        return _add_duration(now, text)

    if _DATE_PATTERN.match(text):
        try:
            day = date.fromisoformat(text)
        except ValueError as e:
            raise InvalidPointInTimeError(f'Invalid date: {value}') from e
        next_midnight = datetime.combine(day + timedelta(days=1), time.min).astimezone()
        return next_midnight.astimezone(timezone.utc)

    try:
        moment = datetime.fromisoformat(text)
    except ValueError as e:
        raise InvalidPointInTimeError(
            f'"{value}" is not an ISO 8601 duration (e.g. P30D), date (e.g. 2026-11-01) '
            f'or date-time (e.g. 2026-11-01T17:00:00Z)'
        ) from e
    if moment.tzinfo is None:
        moment = moment.astimezone()
    return moment.astimezone(timezone.utc)


def _add_duration(start: datetime, text: str) -> datetime:
    match = _DURATION_PATTERN.match(text)
    if not match or text.upper() in ('P', 'PT') or text.upper().endswith('T'):
        raise InvalidPointInTimeError(f'Invalid ISO 8601 duration: {text}')

    parts = {k: v for k, v in match.groupdict().items() if v is not None}
    result = _add_months(start, int(parts.get('years', 0)) * 12 + int(parts.get('months', 0)))
    return result + timedelta(weeks=int(parts.get('weeks', 0)),
                              days=int(parts.get('days', 0)),
                              hours=int(parts.get('hours', 0)),
                              minutes=int(parts.get('minutes', 0)),
                              seconds=float(parts.get('seconds', 0)))


def _add_months(start: datetime, months: int) -> datetime:
    """ Calendar month arithmetic, clamping to the last day of a shorter month (Jan 31 + 1 month = Feb 28/29) """
    if months == 0:
        return start
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return start.replace(year=year, month=month, day=day)
