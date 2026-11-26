from datetime import datetime, timezone, date
from laporan.timeutil import today_wib, report_dates


def test_today_wib_from_utc_late_evening():
    # 23:30 UTC 25 Nov = 06:30 WIB 26 Nov
    assert today_wib(datetime(2026, 11, 25, 23, 30, tzinfo=timezone.utc)) == date(2026, 11, 26)


def test_report_dates():
    d = report_dates(date(2026, 11, 26))
    assert d == {"kemarin": "2026-11-25", "lusa": "2026-11-24", "tujuh_hari_lalu": "2026-11-18"}
