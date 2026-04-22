from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from calendar import monthrange

from app.i18n import format_date_range, format_month_year, translate as t


PERIOD_OPTIONS = ("month", "last_30", "year", "all", "custom")


@dataclass(frozen=True)
class PeriodSelection:
    key: str
    start: datetime | None
    end: datetime | None
    label: str
    start_value: str
    end_value: str


def _month_bounds(now: datetime) -> tuple[datetime, datetime]:
    start = datetime(now.year, now.month, 1)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1)
    else:
        end = datetime(now.year, now.month + 1, 1)
    return start, end


def _year_bounds(now: datetime) -> tuple[datetime, datetime]:
    return datetime(now.year, 1, 1), datetime(now.year + 1, 1, 1)


def _parse_date(value: str | None) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.combine(datetime.strptime(value, "%Y-%m-%d").date(), time.min)
    except ValueError:
        return None


def _date_input(value: datetime | None) -> str:
    return value.date().isoformat() if value else ""


def resolve_period(period: str | None, start: str | None = None, end: str | None = None) -> PeriodSelection:
    now = datetime.now()
    selected = (period or "month").strip().lower()
    if selected not in PERIOD_OPTIONS:
        selected = "month"

    if selected == "last_30":
        start_at = datetime.combine((now - timedelta(days=29)).date(), time.min)
        end_at = datetime.combine(now.date() + timedelta(days=1), time.min)
        return PeriodSelection(
            key=selected,
            start=start_at,
            end=end_at,
            label=format_date_range(start_at, end_at - timedelta(seconds=1)),
            start_value=_date_input(start_at),
            end_value=_date_input(end_at - timedelta(days=1)),
        )

    if selected == "year":
        start_at, end_at = _year_bounds(now)
        return PeriodSelection(
            key=selected,
            start=start_at,
            end=end_at,
            label=str(now.year),
            start_value=_date_input(start_at),
            end_value=_date_input(end_at - timedelta(days=1)),
        )

    if selected == "all":
        return PeriodSelection(
            key=selected,
            start=None,
            end=None,
            label=t("periods.all_time"),
            start_value="",
            end_value="",
        )

    if selected == "custom":
        start_at = _parse_date(start)
        raw_end = _parse_date(end)
        end_at = raw_end + timedelta(days=1) if raw_end else None

        if start_at and raw_end and raw_end < start_at:
            start_at, raw_end = raw_end, start_at
            end_at = raw_end + timedelta(days=1)

        if start_at and raw_end:
            label = format_date_range(start_at, raw_end)
        elif start_at:
            label = t("periods.from_date", date=start_at.date().isoformat())
        elif raw_end:
            label = t("periods.to_date", date=raw_end.date().isoformat())
        else:
            start_at, end_at = _month_bounds(now)
            label = format_month_year(now)

        return PeriodSelection(
            key=selected,
            start=start_at,
            end=end_at,
            label=label,
            start_value=_date_input(start_at),
            end_value=_date_input(raw_end),
        )

    start_at, end_at = _month_bounds(now)
    return PeriodSelection(
        key="month",
        start=start_at,
        end=end_at,
        label=format_month_year(now),
        start_value=_date_input(start_at),
        end_value=_date_input(datetime(now.year, now.month, monthrange(now.year, now.month)[1])),
    )


def apply_period_filter(query, model, selection: PeriodSelection):
    if selection.start is not None:
        query = query.filter(model.date >= selection.start)
    if selection.end is not None:
        query = query.filter(model.date < selection.end)
    return query


def period_query_params(selection: PeriodSelection) -> dict[str, str]:
    params = {"period": selection.key}
    if selection.key == "custom":
        if selection.start_value:
            params["start"] = selection.start_value
        if selection.end_value:
            params["end"] = selection.end_value
    return params
