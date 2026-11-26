import json
from datetime import date
import pytest
from laporan import cli
from laporan.config import load_servers, load_sources
from laporan.mcp_client import McpCallError, McpClient
from laporan.snapshot import SnapshotTransport, planned_calls

D = date(2026, 11, 26)


def test_planned_calls_resolve_dates(settings_fixture):
    calls = planned_calls(load_sources(settings_fixture), load_servers(settings_fixture), D)
    sales = [c for c in calls if c["key"] == "sales"][0]
    assert sales == {"source": "tiktok", "key": "sales", "server": "cms_tiktok", "tool": "get_sales_summary",
                     "args": {"from": "2026-11-25", "to": "2026-11-25"}}


async def test_snapshot_replays_recorded_result_without_tokens(settings_fixture, tmp_path, monkeypatch):
    monkeypatch.delenv("CMS_TIKTOK_TOKEN", raising=False)
    rec = tmp_path / "r.json"
    rec.write_text(json.dumps([{"server": "cms_tiktok", "tool": "get_sales_summary",
                                "args": {"to": "2026-11-25", "from": "2026-11-25"}, "result": {"cards": {"total_omset": 36120000}}}]))
    client = McpClient(load_servers(settings_fixture), transport=SnapshotTransport(str(rec), load_servers(settings_fixture)))
    out = await client.call("cms_tiktok", "get_sales_summary", {"from": "2026-11-25", "to": "2026-11-25"})
    assert out == {"cards": {"total_omset": 36120000}}


async def test_snapshot_missing_call_is_an_error(settings_fixture, tmp_path):
    rec = tmp_path / "r.json"
    rec.write_text("[]")
    client = McpClient(load_servers(settings_fixture), transport=SnapshotTransport(str(rec), load_servers(settings_fixture)))
    with pytest.raises(McpCallError, match="rekaman"):
        await client.call("cms_tiktok", "get_overview", {})


async def test_snapshot_still_enforces_read_only(settings_fixture, tmp_path):
    from laporan.mcp_client import ToolNotAllowed
    rec = tmp_path / "r.json"
    rec.write_text("[]")
    client = McpClient(load_servers(settings_fixture), transport=SnapshotTransport(str(rec), load_servers(settings_fixture)))
    with pytest.raises(ToolNotAllowed):
        await client.call("taqis", "taqis_aksi", {})


def test_cli_rencana_prints_json(settings_fixture, monkeypatch, capsys):
    monkeypatch.setattr(cli, "get_settings", lambda: settings_fixture)
    assert cli.main(["rencana", "--date", "2026-11-26"]) == 0
    calls = json.loads(capsys.readouterr().out)
    assert {c["source"] for c in calls} == {"konten", "tiktok", "taqis", "keuangan"}
