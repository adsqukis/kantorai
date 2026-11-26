from laporan import cli
from tests.fakes import FakeTransport


def test_probe_lists_tools(settings_fixture, monkeypatch, capsys):
    monkeypatch.setenv("CMS_TIKTOK_TOKEN", "x")
    monkeypatch.setattr(cli, "get_settings", lambda: settings_fixture)
    code = cli.main(["probe", "--server", "cms_tiktok"], transport=FakeTransport())
    out = capsys.readouterr().out
    assert code == 0
    assert "get_overview" in out


def test_probe_missing_token_reports_clearly(settings_fixture, monkeypatch, capsys):
    monkeypatch.delenv("TAQIS_TOKEN", raising=False)
    monkeypatch.setattr(cli, "get_settings", lambda: settings_fixture)
    code = cli.main(["probe", "--server", "taqis"], transport=FakeTransport())
    assert code == 1
    assert "TAQIS_TOKEN" in capsys.readouterr().out


def test_probe_try_runs_source_calls(settings_fixture, monkeypatch, capsys):
    from tests.fakes import FakeTransport
    monkeypatch.setenv("CMS_TIKTOK_TOKEN", "x")
    monkeypatch.setattr(cli, "get_settings", lambda: settings_fixture)
    t = FakeTransport()
    code = cli.main(["probe", "--try", "tiktok"], transport=t)
    out = capsys.readouterr().out
    assert code == 0
    assert {c.tool for c in t.calls} >= {"get_overview", "get_live_sessions"}
    assert "overview" in out and "OK" in out


def test_serve_starts_uvicorn_on_localhost(settings_fixture, monkeypatch):
    seen = {}
    monkeypatch.setattr(cli, "get_settings", lambda: settings_fixture)
    monkeypatch.setattr(cli, "uvicorn_run", lambda app, host, port, **kw: seen.update(host=host, port=port))
    assert cli.main(["serve"]) == 0
    assert seen == {"host": "127.0.0.1", "port": 8080}
