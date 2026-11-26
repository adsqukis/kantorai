from laporan import cli, db
from laporan.timeutil import today_wib


def test_demo_seeds_a_finished_report(settings_fixture, monkeypatch, capsys):
    monkeypatch.setattr(cli, "get_settings", lambda: settings_fixture)
    assert cli.main(["demo"]) == 0
    run = db.load_run(db.connect(settings_fixture.db_path), today_wib())
    assert run.status == "SELESAI"
    assert [r.source_id for r in run.reporters] == ["konten", "tiktok", "taqis", "keuangan"]
    assert run.summary.penting and run.analysis and len(run.analysis.saran) >= 3
    assert "CONTOH" in run.summary.penting[0]
    assert "data contoh" in capsys.readouterr().out.lower()


def test_demo_berjalan_leaves_run_in_progress(settings_fixture, monkeypatch):
    monkeypatch.setattr(cli, "get_settings", lambda: settings_fixture)
    assert cli.main(["demo", "--berjalan"]) == 0
    run = db.load_run(db.connect(settings_fixture.db_path), today_wib())
    assert run.status == "BERJALAN"
    assert [r.source_id for r in run.reporters] == ["konten"]
