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
