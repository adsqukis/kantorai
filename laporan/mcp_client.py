"""Klien MCP baca-saja. Tool di luar daftar putih ditolak sebelum koneksi dibuka."""
import json
from typing import Any, Protocol

from .config import token_for
from .models import ServerConf

# Harus sama persis dengan tool yang dipakai config/sources.yaml (+ tool discovery).
READ_ONLY_TOOLS: dict[str, frozenset[str]] = {
    "qukistudio": frozenset({
        "qukis_ringkasan_pagi", "qukis_kpi", "qukis_daftar_posting",
        "qukis_ringkasan_insight", "qukis_web_analytics", "qukis_daftar_brand",
    }),
    "cms_tiktok": frozenset({
        "get_overview", "get_sales_summary", "get_order_status_summary",
        "get_live_sessions", "get_content_top_videos", "get_ads_spend_summary",
        "get_affiliate_performance",
    }),
    "taqis": frozenset({"taqis_baca", "taqis_daftar_operasi"}),
    "smartup": frozenset({
        "marketplace_dashboard_summary", "marketplace_top_products",
        "marketplace_revenue_trend", "marketplace_stores",
    }),
}

CALL_TIMEOUT = 60.0


class ToolNotAllowed(Exception):
    pass


class McpCallError(Exception):
    pass


class Transport(Protocol):
    async def call_tool(self, url: str, headers: dict, tool: str, args: dict) -> Any: ...
    async def list_tools(self, url: str, headers: dict) -> list[dict]: ...


def parse_result(res: Any) -> Any:
    texts = [c.text for c in (res.content or []) if getattr(c, "type", None) == "text"]
    if getattr(res, "is_error", False):
        raise McpCallError(" ".join(texts) or "tool mengembalikan error")
    structured = getattr(res, "structured_content", None)
    if structured is not None:
        return structured
    text = "\n".join(texts)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


class HttpTransport:
    """Transport nyata: MCP streamable HTTP dengan header Authorization."""

    async def _session(self, url: str, headers: dict):
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client
        from mcp.shared._httpx_utils import create_mcp_http_client
        import httpx2

        client = create_mcp_http_client(headers=headers, timeout=httpx2.Timeout(CALL_TIMEOUT))
        return client, streamable_http_client(url, http_client=client), ClientSession

    async def call_tool(self, url: str, headers: dict, tool: str, args: dict) -> Any:
        client, transport, ClientSession = await self._session(url, headers)
        async with client, transport as (read, write), ClientSession(read, write) as s:
            await s.initialize()
            return parse_result(await s.call_tool(tool, args, read_timeout_seconds=CALL_TIMEOUT))

    async def list_tools(self, url: str, headers: dict) -> list[dict]:
        client, transport, ClientSession = await self._session(url, headers)
        async with client, transport as (read, write), ClientSession(read, write) as s:
            await s.initialize()
            res = await s.list_tools()
            return [{"name": t.name, "description": t.description, "inputSchema": t.input_schema} for t in res.tools]


class McpClient:
    def __init__(self, servers: dict[str, ServerConf], transport: Transport | None = None):
        self.servers = servers
        self.transport = transport or HttpTransport()

    def _headers(self, server: ServerConf) -> dict:
        if getattr(self.transport, "needs_auth", True) is False:
            return {}
        return {"Authorization": f"Bearer {token_for(server)}"}

    async def call(self, server: str, tool: str, args: dict) -> Any:
        if tool not in READ_ONLY_TOOLS.get(server, frozenset()) or server not in self.servers:
            raise ToolNotAllowed(f"tool '{tool}' di server '{server}' tidak ada di daftar baca-saja")
        conf = self.servers[server]
        return await self.transport.call_tool(conf.url, self._headers(conf), tool, args)

    async def list_tools(self, server: str) -> list[dict]:
        conf = self.servers[server]
        return await self.transport.list_tools(conf.url, self._headers(conf))
