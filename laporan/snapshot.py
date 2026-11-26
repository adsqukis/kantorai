"""Rekaman data: jalankan rantai laporan dengan hasil panggilan MCP yang sudah direkam.

Dipakai untuk uji coba dengan data asli sebelum token MCP tersedia di server.
Format file: JSON list [{"server", "tool", "args", "result"}].
"""
import json
from datetime import date
from typing import Any

from .fetch import fill_placeholders
from .mcp_client import McpCallError
from .models import ServerConf, SourceSpec


def _key(server: str, tool: str, args: dict) -> str:
    return json.dumps([server, tool, args], sort_keys=True, ensure_ascii=False)


def planned_calls(sources: list[SourceSpec], servers: dict[str, ServerConf], run_date: date) -> list[dict]:
    out = []
    for spec in sources:
        for c in spec.calls:
            out.append({"source": spec.id, "key": c.key, "server": c.server, "tool": c.tool,
                        "args": fill_placeholders(c.args, run_date)})
    return out


class SnapshotTransport:
    needs_auth = False

    def __init__(self, path: str, servers: dict[str, ServerConf]):
        by_url = {s.url: name for name, s in servers.items()}
        self._by_url = by_url
        with open(path, encoding="utf-8") as f:
            entries = json.load(f)
        self._results = {_key(e["server"], e["tool"], e.get("args") or {}): e["result"] for e in entries}

    async def call_tool(self, url: str, headers: dict, tool: str, args: dict) -> Any:
        server = self._by_url.get(url, url)
        k = _key(server, tool, args or {})
        if k not in self._results:
            raise McpCallError(f"panggilan {server}/{tool} {json.dumps(args, ensure_ascii=False)} tidak ada di rekaman")
        return self._results[k]

    async def list_tools(self, url: str, headers: dict) -> list[dict]:
        raise McpCallError("rekaman tidak menyimpan daftar tool")
