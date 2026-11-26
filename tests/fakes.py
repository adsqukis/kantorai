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
