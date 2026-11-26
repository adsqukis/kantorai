from dataclasses import dataclass, field
from typing import Any


@dataclass
class Call:
    url: str
    headers: dict
    tool: str
    args: dict


@dataclass
class FakeTransport:
    responses: dict[str, Any] = field(default_factory=dict)
    calls: list[Call] = field(default_factory=list)

    async def call_tool(self, url: str, headers: dict, tool: str, args: dict) -> Any:
        self.calls.append(Call(url, headers, tool, args))
        return self.responses.get(tool, {"ok": True})

    async def list_tools(self, url: str, headers: dict) -> list[dict]:
        return [{"name": "get_overview", "inputSchema": {}}]


@dataclass
class ClientCall:
    server: str
    tool: str
    args: dict


@dataclass
class FakeClient:
    """Pengganti McpClient: respons per (tool) atau per key args, error per tool."""
    responses: dict[str, Any] = field(default_factory=dict)
    fail_tools: set[str] = field(default_factory=set)
    calls: list[ClientCall] = field(default_factory=list)

    async def call(self, server: str, tool: str, args: dict) -> Any:
        self.calls.append(ClientCall(server, tool, args))
        if tool in self.fail_tools:
            raise RuntimeError(f"{tool} mati")
        r = self.responses.get(tool, {"ok": 1})
        return r(args) if callable(r) else r
