from datetime import date
from laporan.db import connect, start_run, save_reporter, save_raw, save_analysis, finish_run, load_run, list_run_dates
from laporan.models import Analysis, RawData, Saran, Summary
from tests.factories import ok_result

D = date(2026, 11, 26)


def test_roundtrip(tmp_path):
    conn = connect(str(tmp_path / "x.db"))
    rid = start_run(conn, D)
    save_raw(conn, rid, RawData(source_id="tiktok", run_date=D, items={"a": 1}))
    save_reporter(conn, rid, ok_result("tiktok"))
    s = Saran(brand="Generos Milk", teks="t", alasan="a")
    save_analysis(conn, rid, Analysis(saran=[s] * 3))
    finish_run(conn, rid, Summary(penting=["x"], lakukan=["y"]), "SELESAI")
    run = load_run(conn, D)
    assert run.status == "SELESAI"
    assert [r.source_id for r in run.reporters] == ["tiktok"]
    assert run.analysis.saran[0].brand == "Generos Milk"
    assert run.summary.penting == ["x"]
    assert run.finished_at is not None


def test_new_run_is_berjalan(tmp_path):
    conn = connect(str(tmp_path / "x.db"))
    start_run(conn, D)
    assert load_run(conn, D).status == "BERJALAN"


def test_rerun_same_date_replaces(tmp_path):
    conn = connect(str(tmp_path / "x.db"))
    a = start_run(conn, D)
    save_reporter(conn, a, ok_result("tiktok"))
    b = start_run(conn, D)
    assert a != b
    assert load_run(conn, D).reporters == []
    assert list_run_dates(conn) == [D]


def test_list_run_dates_newest_first(tmp_path):
    conn = connect(str(tmp_path / "x.db"))
    for d in (date(2026, 11, 24), date(2026, 11, 26), date(2026, 11, 25)):
        start_run(conn, d)
    assert list_run_dates(conn) == [date(2026, 11, 26), date(2026, 11, 25), date(2026, 11, 24)]


def test_load_missing_is_none(tmp_path):
    assert load_run(connect(str(tmp_path / "x.db")), D) is None
