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


class FakeOpenAI:
    """Meniru openai.AsyncOpenAI: mengembalikan teks dari daftar `replies` berurutan."""

    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.requests: list[dict] = []
        outer = self

        class _Completions:
            async def create(self, **kw):
                outer.requests.append(kw)
                text = outer.replies.pop(0)
                msg = type("M", (), {"content": text})()
                return type("R", (), {"choices": [type("C", (), {"message": msg})()]})()

        self.chat = type("Chat", (), {"completions": _Completions()})()


class FakeLLM:
    """Meniru LLM.complete: mengembalikan objek dari `outputs` berurutan (atau raise bila Exception)."""

    def __init__(self, outputs: list):
        self.outputs = list(outputs)
        self.calls: list[dict] = []

    async def complete(self, system: str, user: str, schema):
        self.calls.append({"system": system, "user": user, "schema": schema})
        out = self.outputs.pop(0)
        if isinstance(out, Exception):
            raise out
        return out


class SchemaLLM:
    """LLM palsu yang menjawab berdasarkan skema yang diminta (aman untuk pemanggilan paralel)."""

    def __init__(self, by_schema: dict):
        self.by_schema = by_schema
        self.calls: list = []

    async def complete(self, system: str, user: str, schema):
        self.calls.append(schema.__name__)
        out = self.by_schema[schema.__name__]
        if isinstance(out, Exception):
            raise out
        return out


@dataclass
class FlakyClient(FakeClient):
    """Gagal `fail_times[tool]` kali pertama, lalu berhasil."""
    fail_times: dict[str, int] = field(default_factory=dict)

    async def call(self, server: str, tool: str, args: dict) -> Any:
        if self.fail_times.get(tool, 0) > 0:
            self.fail_times[tool] -= 1
            self.calls.append(ClientCall(server, tool, args))
            raise RuntimeError(f"{tool} sementara mati")
        return await super().call(server, tool, args)
