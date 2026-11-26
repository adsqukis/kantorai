from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

WIB = ZoneInfo("Asia/Jakarta")


def today_wib(now: datetime | None = None) -> date:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(WIB).date()


def report_dates(run_date: date) -> dict[str, str]:
    return {
        "kemarin": (run_date - timedelta(days=1)).isoformat(),
        "lusa": (run_date - timedelta(days=2)).isoformat(),
        "tujuh_hari_lalu": (run_date - timedelta(days=8)).isoformat(),
    }
