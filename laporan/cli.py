import argparse
import asyncio
import json
import sys

from .config import Settings, load_servers, load_sources
from .fetch import fetch_source
from .timeutil import today_wib
from .mcp_client import McpClient


def get_settings() -> Settings:
    return Settings()


async def _probe(settings: Settings, server: str | None, transport) -> int:
    servers = load_servers(settings)
    client = McpClient(servers, transport=transport)
    names = [server] if server else list(servers)
    code = 0
    for name in names:
        print(f"== {name} ({servers[name].url})")
        try:
            for t in await client.list_tools(name):
                schema = json.dumps(t.get("inputSchema") or {}, ensure_ascii=False)
                print(f"  - {t['name']}: {schema[:300]}")
        except Exception as e:  # tampilkan semua error koneksi/token dengan jelas
            print(f"  GAGAL: {e}")
            code = 1
    return code


async def _probe_try(settings: Settings, source_id: str, transport) -> int:
    spec = next((s for s in load_sources(settings) if s.id == source_id), None)
    if spec is None:
        print(f"Sumber '{source_id}' tidak ada di sources.yaml")
        return 1
    raw = await fetch_source(McpClient(load_servers(settings), transport=transport), spec, today_wib())
    for key, value in raw.items.items():
        top = list(value)[:8] if isinstance(value, dict) else type(value).__name__
        print(f"  OK    {key}: {len(json.dumps(value, ensure_ascii=False))} karakter, kunci {top}")
    for key, err in raw.errors.items():
        print(f"  GAGAL {key}: {err}")
    return 1 if raw.errors else 0


def main(argv: list[str] | None = None, *, transport=None) -> int:
    p = argparse.ArgumentParser(prog="laporan")
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("probe", help="lihat daftar tool tiap server MCP")
    pr.add_argument("--server")
    pr.add_argument("--try", dest="try_source", metavar="SOURCE_ID")
    args = p.parse_args(argv)
    settings = get_settings()
    if args.cmd == "probe":
        if args.try_source:
            return asyncio.run(_probe_try(settings, args.try_source, transport))
        return asyncio.run(_probe(settings, args.server, transport))
    return 2


if __name__ == "__main__":
    sys.exit(main())
