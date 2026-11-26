import pytest
from pydantic import ValidationError
from laporan.config import load_sources, load_servers, load_brands, token_for
from laporan.models import Summary, Analysis, Saran


def test_sources_yaml_has_four_sources(settings_fixture):
    ids = [s.id for s in load_sources(settings_fixture)]
    assert ids == ["konten", "tiktok", "taqis", "keuangan"]


def test_every_call_points_at_known_server(settings_fixture):
    servers = load_servers(settings_fixture)
    for s in load_sources(settings_fixture):
        for c in s.calls:
            assert c.server in servers


def test_brands_loaded(settings_fixture):
    names = [b.nama for b in load_brands(settings_fixture)]
    assert "Generos Milk" in names


def test_missing_token_env_raises_clear_error(monkeypatch, settings_fixture):
    srv = load_servers(settings_fixture)["taqis"]
    monkeypatch.delenv(srv.token_env, raising=False)
    with pytest.raises(RuntimeError, match=srv.token_env):
        token_for(srv)


def test_token_read_from_env(monkeypatch, settings_fixture):
    srv = load_servers(settings_fixture)["taqis"]
    monkeypatch.setenv(srv.token_env, "abc")
    assert token_for(srv) == "abc"


def test_summary_caps_five():
    with pytest.raises(ValidationError):
        Summary(penting=["a"] * 6, lakukan=[])
    with pytest.raises(ValidationError):
        Summary(penting=[], lakukan=["a"] * 6)


def test_analysis_needs_three_to_five_saran():
    s = Saran(brand="Generos Milk", teks="x", alasan="y", dugaan=False)
    with pytest.raises(ValidationError):
        Analysis(temuan=[], saran=[s, s], peringatan=[])
    with pytest.raises(ValidationError):
        Analysis(temuan=[], saran=[s] * 6, peringatan=[])
    assert len(Analysis(temuan=[], saran=[s] * 3, peringatan=[]).saran) == 3
