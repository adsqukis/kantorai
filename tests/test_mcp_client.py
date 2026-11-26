import pytest
from types import SimpleNamespace
from laporan.config import load_servers, load_sources
from laporan.mcp_client import McpClient, ToolNotAllowed, McpCallError, READ_ONLY_TOOLS, parse_result
from tests.fakes import FakeTransport


@pytest.fixture
def servers(settings_fixture):
    return load_servers(settings_fixture)


async def test_write_tool_blocked_before_network(servers):
    t = FakeTransport()
    with pytest.raises(ToolNotAllowed):
        await McpClient(servers, transport=t).call("taqis", "taqis_aksi", {"operasi": "POST /api/wa/broadcasts/:id/send"})
    assert t.calls == []


@pytest.mark.parametrize("server,tool", [
    ("taqis", "taqis_konfirmasi"),
    ("smartup", "execute_marketplace_operation"),
    ("smartup", "marketplace_record_opex"),
    ("qukistudio", "qukis_siapkan_5_ide"),
    ("nope", "get_overview"),
])
async def test_other_write_or_unknown_tools_blocked(servers, server, tool):
    t = FakeTransport()
    with pytest.raises(ToolNotAllowed):
        await McpClient(servers, transport=t).call(server, tool, {})
    assert t.calls == []


async def test_allowed_tool_passes_bearer_token(servers, monkeypatch):
    monkeypatch.setenv("CMS_TIKTOK_TOKEN", "t123")
    t = FakeTransport(responses={"get_overview": {"cards": {}}})
    out = await McpClient(servers, transport=t).call("cms_tiktok", "get_overview", {})
    assert out == {"cards": {}}
    assert t.calls[0].headers["Authorization"] == "Bearer t123"
    assert t.calls[0].url == servers["cms_tiktok"].url


def test_taqis_whitelist_is_read_only():
    assert READ_ONLY_TOOLS["taqis"] == frozenset({"taqis_baca", "taqis_daftar_operasi"})


def test_whitelist_covers_every_configured_call(settings_fixture):
    for s in load_sources(settings_fixture):
        for c in s.calls:
            assert c.tool in READ_ONLY_TOOLS[c.server], (c.server, c.tool)


def _res(text=None, structured=None, is_error=False):
    content = [SimpleNamespace(type="text", text=text)] if text is not None else []
    return SimpleNamespace(content=content, structured_content=structured, is_error=is_error)


def test_parse_result_prefers_structured():
    assert parse_result(_res(text='{"a":1}', structured={"b": 2})) == {"b": 2}


def test_parse_result_json_text():
    assert parse_result(_res(text='{"a":1}')) == {"a": 1}


def test_parse_result_plain_text():
    assert parse_result(_res(text="halo")) == "halo"


def test_parse_result_error_raises():
    with pytest.raises(McpCallError, match="rusak"):
        parse_result(_res(text="server rusak", is_error=True))
